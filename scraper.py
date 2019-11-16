import time
from datetime import datetime
import requests
import json
from bs4 import BeautifulSoup
from loguru import logger

# setup logging
# to log an error to file, use logger.error("log message")
logger.add("error.log", level="ERROR")

with logger.catch():
    # Load settings
    with open("settings.json") as f:
        settings = json.load(f)

        API_KEYS = settings["api_key"]
        AUTH_KEY = settings["auth_key"]
        API_URL = settings["api_url"]
        GAME = settings["game"]
        checkrange = range(settings["range"][0], settings["range"][1])

    API_KEY = settings["api_key"]
    if (type(API_KEYS) == str) or ((len(API_KEYS) == 1) and (type(API_KEYS) == list)):  # if the API keys entry in the
        # settings is a string or a list with length of one
        API_KEY = API_KEYS if (type(API_KEYS == str)) else API_KEYS[0]
        CURRENT_API_KEY = None  # so it can be determined if multiple API keys are availble
    else:  # there is a list of keys
        CURRENT_API_KEY = 0  # start with the first provided key (CURRENT_API_KEY is a list index)
        API_KEY = API_KEYS[CURRENT_API_KEY]

    if CURRENT_API_KEY is not None:  # if there are mulyiple keys
        API_KEYS = [[k, None] for k in API_KEYS]  # make API_KEYS a list in format [[key, None], [key2, None], ...]
        # None will be replaced with the time when the ratelimit resets for that specific key. Signifies if that key
        # has been used or not.

    headers = {
        'apikey': API_KEY,
        'accept': 'applications/json'
    }

    mods = {}


    def parse_api_time(date):
        s = date.split(":")
        s[-2] = s[-2] + s[-1]
        s.pop(-1)
        date = ""
        for i in s:
            date += i + ":"
        date = date[:-1]
        return datetime.timestamp(datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z'))


    def waitforapirequests(hourlyreset):
        delta = (parse_api_time(hourlyreset) - datetime.timestamp(datetime.now())) + 60
        while delta > 0:
            if int(delta / 60) < 1:
                p = f"{int(delta)} seconds"
            else:
                p = f"{int(delta / 60)} minutes"

            print(f"\rWaiting {p} for api requests to reset...",
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

                print(f"\nAPI ratelimit reached for key {CURRENT_API_KEY}, switching to key {next_key}.\n")

                API_KEY = API_KEYS[next_key][0]  # sets API_KEY to the next key
                CURRENT_API_KEY = next_key  # updates the index
                headers["apikey"] = API_KEY  # updates the dict used for request headers

                # It is assumed that if a key has been switched, the previous key has been used and hence, the
                # key that has been used and just swapped out will have a longer wait until ratelimit reset than
                # the next key. Tom from the future: turns out all ratelimits reset at the same time anyway
                # Hence, if the next API key has been used, and the limts are under the threshold, wait.

                r = requests.get("https://api.nexusmods.com/v1/users/validate.json", headers=headers)  # gets ratelimit info for new key

                if API_KEYS[CURRENT_API_KEY][1] is not None and ((int(r.headers['x-rl-daily-remaining']) < 5) and (int(r.headers['x-rl-hourly-remaining']) < 5)):
                    waitforapirequests(API_KEYS[CURRENT_API_KEY][1])

            else:
                waitforapirequests(hreset)


    for mod_id in checkrange:
        print(f"\nMod number: {mod_id}!")
        html = str(BeautifulSoup(requests.get(f"https://www.nexusmods.com/{GAME}/mods/{mod_id}").content,
                                 features="html.parser").h3)
        html = html[html.find('>') + 1:html.find('<', 2)]
        if not any(x in html.lower() for x in ["hidden mod", "not found", "not published"]):
            r = requests.get(f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mod_id}/files.json", headers=headers)
            dreqs = int(r.headers['x-rl-daily-remaining'])
            hreqs = int(r.headers['x-rl-hourly-remaining'])
            hreset = r.headers['x-rl-hourly-reset']
            reqs = f"API Reqs reamining: {dreqs} | {hreqs}"
            if r.ok:
                c = json.loads(r.content)
                files = c['files']

                if len(files) == 0:
                    print("This mod has no files")
                    r = requests.get(f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mod_id}.json", headers=headers)

                    dreqs = int(r.headers['x-rl-daily-remaining'])
                    hreqs = int(r.headers['x-rl-hourly-remaining'])
                    hreset = r.headers['x-rl-hourly-reset']
                    reqs = f"API Reqs reamining: {dreqs} | {hreqs}"

                    if r.ok:
                        j = r.json()

                        params = {
                            'mod_id': f'{mod_id}',
                            'mod_name': j["name"],
                            'mod_desc': "THIS MOD HAS NO FILES - " + j['summary'],
                            'mod_version': "0",
                            'category_name': "NO FILES",
                            'content_preview': "{}",
                            'adult_content': False,
                            'key': AUTH_KEY
                        }

                        r = requests.post(API_URL, data=params)

                        print(f"Database request | {reqs} | {r.text}")

                else:
                    x = range(0, len(files))
                    for n in x:
                        file = files[n]
                        j = json.loads(requests.get(file['content_preview_link']).content)
                        params = {
                            'mod_id': f'{mod_id}.{n}',
                            'mod_name': file['name'],
                            'mod_desc': file['description'],
                            'mod_version': file['version'],
                            'file_id': file['file_id'],
                            'size_kb': file['size_kb'],
                            'category_name': file['category_name'],
                            'content_preview': json.dumps(j),
                            'uploaded_time': file['uploaded_timestamp'],
                            'external_virus_scan_url': file['external_virus_scan_url'],
                            'adult_content': html.lower() == "adult content",
                            'key': AUTH_KEY
                        }
                        r = requests.post(API_URL, data=params)
                        if not r.ok:
                            logger.error(f"Database request | {mod_id} | {reqs} | {r.text}")
                        print(f"Database request | {reqs} | {r.text}")
                        check_api_ratelimits(dreqs, hreqs, hreset)

            else:
                try:
                    j = r.json()
                    if "msg" in j:
                        if "too many requests" in j["msg"].lower():  # check for the ratelimit being completely saturated
                            check_api_ratelimits(0, 0, r.headers["x-rl-hourly-reset"])
                        else:
                            logger.error(f"Mod gone, oh man :c : {r.text}")
                    elif "message" in j:
                        if "no mod found" in j["message"].lower():
                            params = {
                                'mod_id': f'{mod_id}',
                                'mod_name': html,
                                'mod_desc': "",
                                'mod_version': "0",
                                'file_id': None,
                                'size_kb': None,
                                'category_name': html.upper(),
                                'content_preview': "{}",
                                'uploaded_time': None,
                                'external_virus_scan_url': "",
                                'adult_content': False,
                                'key': AUTH_KEY
                            }
                            r = requests.post(API_URL, data=params)
                        else:
                            logger.error(f"Mod gone, oh man :c : {r.text}")
                    else:
                        logger.error(f"Mod gone, oh man :c : {r.text}")
                except json.decoder.JSONDecodeError:
                    logger.error(f"Mod gone, oh man :c : {r.text}")
        else:
            print(html)
            params = {
                'mod_id': f'{mod_id}',
                'mod_name': html,
                'mod_desc': "",
                'mod_version': "0",
                'file_id': None,
                'size_kb': None,
                'category_name': html.upper(),
                'content_preview': "{}",
                'uploaded_time': None,
                'external_virus_scan_url': "",
                'adult_content': False,
                'key': AUTH_KEY
            }
            r = requests.post(API_URL, data=params)
            print(f"{r.text}")

            # file_dict = {}
            # for file in c['files']:
            #     mod_name = file['name']
            #     mod_description = file['description']
            #     links = []
            #     if file['category_id'] < 6:
            #         file_id = str(file['file_id'])
            #         r = requests.get(f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mod_id}/files/
            #         {file_id}/download_"
            #                          f"link.json", headers=headers)
            #         c = json.loads(r.content)
            #         print("starting download")
            #         url = c[1]['URI']
            #         print(url)
            #         with requests.get(url, stream=True) as s:
            #             s.raise_for_status()
            #             os.makedirs(os.path.join("mods", mod_name))
            #             with open(os.path.join("mods", mod_name, file['file_name']), 'wb+') as m:
            #                 for chunk in s.iter_content(chunk_size=8192):
            #                     if chunk:  # filter out keep-alive new chunks
            #                         m.write(chunk)
            #         print("finished")
            #         for link in range(len(c)):
            #             links.append(str(c[link]['URI'].replace(" ", "%20")))
            #     file_dict[str(file_id)] = tuple([str(mod_name), str(mod_description), links])
            # mods[str(mod_id)] = file_dict
