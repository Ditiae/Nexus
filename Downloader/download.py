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
from common import iprint, aprint, rprint, qprint, eprint, qcol

#logger.remove(0)  # remove output to stderr DEBUG
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
            r = requests.get("https://api.nexusmods.com/v1/users/validate.json", headers=nexus_headers)

            if API_KEYS[CURRENT_API_KEY][1] is not None and ((int(r.headers['x-rl-daily-remaining']) < 5) and
                                                             (int(r.headers['x-rl-hourly-remaining']) < 5)):
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
    init(autoreset=True)  # colorama init

    with open("settings.json") as f:
        SETTINGS = json.load(f)

    API_KEYS = SETTINGS["nexus_keys"]
    AUTH_KEY = SETTINGS["auth_key"]
    API_URL = SETTINGS["endpoint"]
    GAME = SETTINGS["game"]
    DOWNLOAD_DIRECTORY = SETTINGS["download_folder"]

    if not os.path.exists(DOWNLOAD_DIRECTORY):
        make_directory(DOWNLOAD_DIRECTORY)

    SELECTED_SERVER = None

    internal_headers = {  # used for internal API
        "key": AUTH_KEY
    }

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

with logger.catch():
    while True:
        # 1: Get next mod

        r = requests.post(get_api_endpoint("dl", "progress"), data=internal_headers)

        if not r.ok:
            if r.status_code == 404:
                print("No mods available. Waiting for 30 seconds.")
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

        mod_id = r_json["content"]["mod_id"]
        file_id = r_json["content"]["file_id"]
        mod_name = r_json["content"]["mod_name"]
        mod_version = r_json["content"]["mod_version"]

        print(mod_id, file_id)  # DEBUG

        # 2: Get download link from Nexus

        r = requests.get(f"https://api.nexusmods.com/v1/games/skyrim/mods/{mod_id}/files/{file_id}/download_link.json",
                         headers=nexus_headers)

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

        # TODO: This bit below can probably be improved
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

        mod_dir = os.path.join(DOWNLOAD_DIRECTORY, GAME, str(mod_id))
        make_directory(mod_dir)
        zip_name = os.path.join(mod_dir, mod_name + (("-" + mod_version) if mod_version is not None else "") + ".zip")
        source_name_from_url = download_link.split('/')[-1].split("?")[0]

        print(f"Begin download of {zip_name}")
        with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_LZMA) as zip_f:
            with zip_f.open(source_name_from_url, "w") as f:
                with requests.get(download_link.replace(" ", "%20"), stream=True) as r:  # this is supposedly 3x faster than f.write chunk
                    shutil.copyfileobj(r.raw, f)

        print("Download completed")

        # 4: Set status to completed
        # 5: Zip and rclone file (in separate thread?)

        input("press enter") # DEBUG
