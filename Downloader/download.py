import sys
import time
from datetime import datetime
from colorama import Fore, Back, init
import requests
from loguru import logger
import os
import zipfile
import json
from common import iprint, aprint, rprint, qprint, eprint

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
            # Hence, if the next API key has been used, and the limts are under the threshold, wait.

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


# load settings
with logger.catch():
    init(autoreset=True)  # colorama init

    with open("settings.json") as f:
        SETTINGS = json.load(f)

    API_KEYS = SETTINGS["nexus_keys"]
    AUTH_KEY = SETTINGS["auth_key"]
    API_URL = SETTINGS["endpoint"]
    GAME = SETTINGS["game"]

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
        eprint(f"Could not parse response from internal API\n{r.status_code} - {r.text}")
        eprint("Exiting now")
        sys.exit()  # TODO: make this do something other than exiting

    mod_id = r_json["content"]["mod_id"]
    file_id = r_json["content"]["file_id"]

    print(mod_id, file_id)

    # 2: Get download link from Nexus
    # 3: Download mod
    # 4: Set status to completed
    # 5: Zip and rclone file (in separate thread?)

    input() # DEBUG
