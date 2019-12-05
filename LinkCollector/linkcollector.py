import sys
import time
from datetime import datetime
import json

import requests
from loguru import logger
from colorama import Fore, Back, init

# TODO: There is a lot of common code in this file and DataScraper/scraper.py - consider refactoring to make it pull it
#  all from one file

logger.add("error.log", level="ERROR")

with logger.catch():
    init(autoreset=True)  # colorama init

    with open("settings.json") as f:
        settings = json.load(f)

        API_KEYS = settings["api_key"]
        AUTH_KEY = settings["auth_key"]
        API_URL = settings["base_api_url"]
        GAME = settings["game"]
        run_range = range(settings["range"][0], settings["range"][1])

    # key switching setup
    API_KEY = settings["api_key"]
    if (type(API_KEYS) == str) or ((len(API_KEYS) == 1) and (type(API_KEYS) == list)):
        API_KEY = API_KEYS if (type(API_KEYS == str)) else API_KEYS[0]
        CURRENT_API_KEY = None
    else:
        CURRENT_API_KEY = 0
        API_KEY = API_KEYS[CURRENT_API_KEY]

    if CURRENT_API_KEY is not None:
        API_KEYS = [[k, None] for k in API_KEYS]

    headers = {
        'apikey': API_KEY,
        'accept': 'applications/json'
    }


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
        delta = (parse_api_time(hourlyreset) - datetime.timestamp(datetime.now())) + 60
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
        global headers
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
                headers["apikey"] = API_KEY  # updates the dict used for request headers

                # It is assumed that if a key has been switched, the previous key has been used and hence, the
                # key that has been used and just swapped out will have a longer wait until ratelimit reset than
                # the next key. Tom from the future: turns out all ratelimits reset at the same time anyway
                # Hence, if the next API key has been used, and the limts are under the threshold, wait.

                r = requests.get("https://api.nexusmods.com/v1/users/validate.json", headers=headers)  # gets ratelimit
                # info for new key

                if API_KEYS[CURRENT_API_KEY][1] is not None and ((int(r.headers['x-rl-daily-remaining']) < 5) and
                                                                 (int(r.headers['x-rl-hourly-remaining']) < 5)):
                    wait_for_api_requests(API_KEYS[CURRENT_API_KEY][1])

            else:
                wait_for_api_requests(hreset)

    def die_func():
        input("PRESS <ENTER> to exit")
        sys.exit()

    def ratelimit_wrapper(robj):
        dreqs = int(r.headers['x-rl-daily-remaining'])
        hreqs = int(r.headers['x-rl-hourly-remaining'])
        hreset = r.headers['x-rl-hourly-reset']
        check_api_ratelimits(dreqs, hreqs, hreset)

    for mod_id in run_range:
        print(f"New mod: {mod_id}")

        # make API request to internal API for mod info
        count = -1
        while True:

            count += 1

            if count == 0:
                db_row_id = ""
            else:
                db_row_id = "." + str(count)

            db_mod_id = f'{mod_id}{db_row_id}'

            print(f"    DB id {db_mod_id}")

            params = {
                'mod_id': db_mod_id,
                'key': AUTH_KEY
            }

            r = requests.post(API_URL + "select/", data=params)

            if not r.ok:
                if r.status_code == 403:
                    print("{Back.RED}{Fore.WHITE}Internal API authentication code incorrect.")
                    die_func()
                elif r.status_code == 404:
                    break
                else:
                    logger.error(f"Unknown error from internal API - {r.text}, {r.status_code}")
                    die_func()

            print(f"{Fore.GREEN}        Data retrieved")

            try:
                j = r.json()
            except json.decoder.JSONDecodeError:
                logger.error(f"{Back.RED}{Fore.WHITE}Cannot parse response from internal API - {r.text}, {r.status_code}")
                die_func()

            if j["content"]["category_name"] in ["NOT FOUND", "HIDDEN MOD", "NO FILES", "NOT PUBLISHED", "UNDER MODERATION", "NON"]:
                print(f"{Fore.RED}        Mod - {j['content']['category_name']}")
                continue

            file_id = j["content"]["file_id"]

            print(f"        Getting download link (file ID {file_id})")

            r = requests.get(
                f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mod_id}/files/{file_id}/download_link.json",
                headers=headers)

            ratelimit_wrapper(r)

            if not r.ok:
                if r.status_code == 404:
                    # file not found
                    print("{Fore.RED}            File not found")
                    continue
                elif r.status_code == 403:

                    try:
                        j = r.json()
                    except json.decoder.JSONDecodeError:
                        logger.error(f"Cannot parse response from Nexus API - {r.text}, {r.status_code}")
                        die_func()

                    if "message" in j:
                        if "premium users only" in j["message"]:
                            # API key not premium
                            print(f"\n{Back.RED}{Fore.WHITE}This API key is not attached to a premium account and hence this script cannot be "
                                  "used to obtain download links.")
                            die_func()
                        else:
                            # mod not available
                            print(f"{Fore.RED}        Mod unavailable")
                            break
                    else:
                        logger.error(f"Cannot parse response from Nexus API - {r.text}, {r.status_code}")
                        die_func()

            print(f"{Fore.GREEN}        Got download link")

            try:
                j = r.json()
            except json.decoder.JSONDecodeError:
                logger.error(f"Cannot parse response from Nexus API - {r.text}, {r.status_code}")
                die_func()

            download_link = j[0]["URI"]

            print("        Adding to internal API")

            params = {
                "mod_id": db_mod_id,
                "download_url": download_link,
                "key": AUTH_KEY
            }

            r = requests.post(API_URL + "link/add/", data=params)

            if not r.ok:
                logger.error(f"Link insertion for DB mod {db_mod_id} failed - '{r.text}', {r.status_code}")
                die_func()

            print(f"{Back.GREEN}{Fore.BLACK}    Insertion for DB mod ID {db_mod_id} successful.")

        print("Mod link sync finished for this mod")

    print("Finished!")
    die_func()
