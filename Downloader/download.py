import shutil
import sys
import time
from datetime import datetime
from colorama import Fore, Back, init
import requests
from loguru import logger
import os
import zipfile
import json
from common import iprint, aprint, qprint, eprint, qcol


# logger.remove(0)  # remove output to stderr DEBUG
logger.add("error.log", level="ERROR")
_old_print = print
print = iprint


# ----- FUNCTIONS -----
def parse_api_time(date):
    s = date.split(":")
    s[-2] = s[-2] + s[-1]
    s.pop(-1)
    date = ""
    for i in s:
        date += i + ":"
    date = date[:-1]
    return datetime.timestamp(datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z'))


def wait_for_api_requests(hourlyreset):
    delta = (parse_api_time(hourlyreset) - datetime.timestamp(datetime.now())) + 120
    while delta > 0:
        if int(delta / 60) < 1:
            p = f"{int(delta)} seconds"
        else:
            p = f"{int(delta / 60)} minutes"

        print(f"\r{Fore.YELLOW}Waiting {p} for api requests to reset...",
              end="")
        delay = 15
        delta -= delay
        time.sleep(delay)


def check_api_ratelimits(daily, hourly, hreset):
    global CURRENT_API_KEY
    global nexus_headers
    global API_KEY

    if (daily < 5) and (hourly < 5):

        if CURRENT_API_KEY is not None:  # if there are multiple keys

            # switch API key

            API_KEYS[CURRENT_API_KEY][1] = hreset  # store the reset time of the current key in use

            # determine the next key to use
            next_key = CURRENT_API_KEY + 1
            if next_key > len(API_KEYS) - 1:
                next_key = 0

            print(f"\n{Fore.YELLOW}API ratelimit reached for key {CURRENT_API_KEY}, switching to key {next_key}.\n")

            API_KEY = API_KEYS[next_key][0]  # sets API_KEY to the next key
            CURRENT_API_KEY = next_key  # updates the index
            nexus_headers["apikey"] = API_KEY  # updates the dict used for request nexus_headers

            # It is assumed that if a key has been switched, the previous key has been used and hence, the
            # key that has been used and just swapped out will have a longer wait until ratelimit reset than
            # the next key. Tom from the future: turns out all ratelimits reset at the same time anyway
            # Hence, if the next API key has been used, and the limits are under the threshold, wait.

            # Get current ratelimits
            req = requests.get("https://api.nexusmods.com/v1/users/validate.json", headers=nexus_headers)

            if API_KEYS[CURRENT_API_KEY][1] is not None and ((int(req.headers['x-rl-daily-remaining']) < 5) and
                                                             (int(req.headers['x-rl-hourly-remaining']) < 5)):
                wait_for_api_requests(API_KEYS[CURRENT_API_KEY][1])

        else:
            wait_for_api_requests(hreset)


def ratelimit_wrapper(request):
    dreqs = int(request.headers['x-rl-daily-remaining'])
    hreqs = int(request.headers['x-rl-hourly-remaining'])
    hreset = request.headers['x-rl-hourly-reset']
    check_api_ratelimits(dreqs, hreqs, hreset)


def get_api_endpoint(*args):
    o = API_URL
    if o[-1] != "/":
        o += "/"

    for arg in args:
        o += arg + "/"

    return o


def make_directory(*args):
    path = os.path.join(*args)
    if not os.path.exists(path):
        os.makedirs(path)


# load settings
with logger.catch():

    print("Nexus downloader")
    print("Loading settings")

    with open("settings.json") as f:
        SETTINGS = json.load(f)

    API_KEYS = SETTINGS["nexus_keys"]
    AUTH_KEY = SETTINGS["auth_key"]
    API_URL = SETTINGS["endpoint"]
    GAME = SETTINGS["game"]
    DOWNLOAD_DIRECTORY = SETTINGS["download_folder"]
    RCLONE_REMOTE = SETTINGS["rclone"]["remote_name"]
    RCLONE_DIRECTORY = SETTINGS["rclone"]["directory"]
    RCLONE_PROGRESS = SETTINGS["rclone"]["show_progress"]
    RCLONE_ENABLE = SETTINGS["rclone"]["enable"]
    MOD_NAME_LENGTH = SETTINGS["mod_name_len"]

    print("Checking for download directory")

    if not os.path.exists(DOWNLOAD_DIRECTORY):
        eprint("Not found. Creating")
        make_directory(DOWNLOAD_DIRECTORY)

    SELECTED_SERVER = None

    internal_headers = {  # used for internal API
        "key": AUTH_KEY
    }

    print("Initialising key switching")

    # key switching setup
    if (type(API_KEYS) == str) or ((len(API_KEYS) == 1) and (type(API_KEYS) == list)):
        API_KEY = API_KEYS if (API_KEYS == str) else API_KEYS[0]
        CURRENT_API_KEY = None
    else:
        CURRENT_API_KEY = 0
        API_KEY = API_KEYS[CURRENT_API_KEY]
    if CURRENT_API_KEY is not None:
        API_KEYS = [[k, None] for k in API_KEYS]

    nexus_headers = {  # used for Nexus API
        'apikey': API_KEY,
        'accept': 'applications/json'
    }

    print("OK!\n")

with logger.catch():
    while True:
        # 1: Get next mod

        print("Retrieving next mod")

        r = requests.post(get_api_endpoint("dl", "progress"), data=internal_headers)

        if not r.ok:
            if r.status_code == 404:
                print("No mods available. Waiting for 30 seconds\n")
                time.sleep(30)
                continue

            else:
                eprint(f"Unknown response from internal API\n{r.status_code} - {r.text}")
                eprint("Exiting now")
                sys.exit()  # TODO: make this do something other than exiting

        try:
            r_json = r.json()
        except json.decoder.JSONDecodeError:
            e_text = f"Could not parse response from internal API\n{r.status_code} - {r.text}"
            logger.exception(e_text)
            eprint(e_text)
            eprint("Exiting now")
            sys.exit()  # TODO: make this do something other than exiting

        internal_mod_id = r_json["content"]["mod_id"]  # has the weird decimal point thing used in the database
        real_mod_id = int(str(r_json["content"]["mod_id"]).split(".")[0])  # removes everything past the decimal point
        file_id = r_json["content"]["file_id"]
        mod_name = r_json["content"]["mod_name"]
        mod_version = r_json["content"]["mod_version"]

        print("Mod ID", real_mod_id)
        print("File ID", file_id)
        print("Mod name", mod_name)

        # 2: Get download link from Nexus

        r = requests.get(
            f"https://api.nexusmods.com/v1/games/skyrim/mods/{real_mod_id}/files/{file_id}/download_link.json",
            headers=nexus_headers
        )

        try:
            r_json = r.json()
        except json.decoder.JSONDecodeError:
            e_text = f"Could not parse response from the Nexus API\n{r.status_code} - {r.text}"
            logger.exception(e_text)
            eprint(e_text)
            eprint("Exiting now")
            sys.exit()  # TODO: don't exit

        servers_avail = [link["short_name"] for link in r_json]  # parse out available download servers

        if SELECTED_SERVER is None:
            server_selection = ""
            for index, server in enumerate(servers_avail):
                server_selection += f"    {index+1} - {server}\n"
            server_selection = server_selection.rstrip("\n")
            qprint(f"Please select your desired download server from one of the following:\n{server_selection}")
            del server_selection

            while True:
                selected_server = input(qcol() + "Selection (int): ")

                try:
                    selected_server = int(selected_server)
                except ValueError:
                    eprint("Not an integer. Try again.")
                    continue

                if selected_server > len(servers_avail):
                    eprint("Out of range. Try again.")
                    continue

                selected_server -= 1
                break

            SELECTED_SERVER = servers_avail[selected_server]

            print(f"Selected server: {SELECTED_SERVER}")

        # TODO: This bit can probably be improved
        if SELECTED_SERVER not in servers_avail:
            eprint("Selected server is not available; defaulting to the Nexus CDN")
            for item in r_json:
                if item["short_name"] == "Nexus CDN":
                    download_link = item["URI"]
        else:
            for item in r_json:
                if item["short_name"] == SELECTED_SERVER:
                    download_link = item["URI"]

        # 3: Download mod

        mod_dir = os.path.join(DOWNLOAD_DIRECTORY, GAME)
        make_directory(mod_dir)
        zip_name = os.path.join(mod_dir, str(real_mod_id) + "-" + mod_name[:MOD_NAME_LENGTH] + (("-" + mod_version) if mod_version is not None else "") + "-" + str(file_id) + ".zip")
        # zip_name = os.path.join(mod_dir,
        #                         str(file_id) + "-" + mod_name[:25] + (("-" + mod_version) if mod_version is not None else "") + ".zip")
        source_name_from_url = download_link.split('/')[-1].split("?")[0]

        aprint(f"Begin download of {zip_name}")
        with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_LZMA) as zip_f:
            with zip_f.open(source_name_from_url, "w") as f:
                with requests.get(download_link.replace(" ", "%20"), stream=True) as r:
                    shutil.copyfileobj(r.raw, f)

        print("Download completed")

        # 5: rclone file (in separate thread?)

        if RCLONE_ENABLE:

	        print("Rclone'ing")

	        rclone_command = f"rclone move {'-P ' if RCLONE_PROGRESS else ''}{mod_dir} " \
	            f"{RCLONE_REMOTE}:/{RCLONE_DIRECTORY}/{GAME}/"

	        os.system(rclone_command)

        # 4: Set status to completed

        print("Updating download status")

        r = requests.post(get_api_endpoint("dl", "completed"),
                          data={**internal_headers, "mod_id": internal_mod_id, "state": True})

        if not r.ok:
            eprint(f"Error returned from internal API\n{r.status_code} - {r.text}")

        print("Complete\n")
