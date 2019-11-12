import requests
import json
from bs4 import BeautifulSoup

# Load settings
with open("settings.json") as f:
    settings = json.load(f)

    API_KEY = settings["api_key"]
    AUTH_KEY = settings["auth_key"]
    API_URL = settings["api_url"]
    GAME = settings["game"]

headers = {
    'apikey': API_KEY,
    'accept': 'applications/json'
}

mods = {}

x = range(1, 1000)
for mod_id in x:
    print(f"\nI'm on mod number: {mod_id}!")
    html = str(BeautifulSoup(requests.get(f"https://www.nexusmods.com/{GAME}/mods/{mod_id}").content,
                             features="html.parser").h3)
    html = html[html.find('>') + 1:html.find('<', 2)]
    if not any(x in html for x in ["Hidden mod", "Not found"]):
        r = requests.get(f"https://api.nexusmods.com/v1/games/{GAME}/mods/{mod_id}/files.json", headers=headers)
        reqs = f"API Reqs reamining: {r.headers['x-rl-daily-remaining']} | {r.headers['x-rl-hourly-remaining']}"
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
                print(f"File upload | {reqs} | {r.text}")

        else:
            print(f"Mod gone, oh man :c :{r.status_code}")
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
