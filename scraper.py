import time
from datetime import datetime
import requests
import json
from bs4 import BeautifulSoup
from loguru import logger

# setup logging
# to log an error to file, use logger.error("log message")
logger.add("error.log", level="ERROR")

# Load settings
with open("settings.json") as f:
    settings = json.load(f)

    API_KEY = settings["api_key"]
    AUTH_KEY = settings["auth_key"]
    API_URL = settings["api_url"]
    GAME = settings["game"]
    checkrange = range(settings["range"][0], settings["range"][1])

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
    print(f"Waiting {delta} seconds for api requests to reset...")
    time.sleep(delta)


for mod_id in checkrange:
    print(f"Mod number: {mod_id}!")
    html = str(BeautifulSoup(requests.get(f"https://www.nexusmods.com/{GAME}/mods/{mod_id}").content,
                             features="html.parser").h3)
    html = html[html.find('>') + 1:html.find('<', 2)]
    if not any(x in html.lower() for x in ["hidden mod", "not found", "not published"]):
        r = requests.get(f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mod_id}/files.json", headers=headers)
        dreqs = r.headers['x-rl-daily-remaining']
        hreqs = r.headers['x-rl-hourly-remaining']
        hreset = r.headers['x-rl-hourly-reset']
        reqs = f"API Reqs reamining: {dreqs} | {hreqs}"
        if r.ok:
            c = json.loads(r.content)
            files = c['files']
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
                    logger.error(f"Database request | {reqs} | {r.text}")
                print(f"Database request | {reqs} | {r.text}")
                if (int(dreqs) < 1) and (int(hreqs) < 1):
                    waitforapirequests(hreset)
        else:
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
