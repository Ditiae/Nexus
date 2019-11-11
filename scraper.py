import requests
import json
import os
from bs4 import BeautifulSoup

API_KEY = os.environ['API_KEY']
AUTH_KEY = os.environ['AUTH_KEY']
api_url = "https://arch.tdpain.net/api/nexusmod/create/"

headers = {'apikey': API_KEY,
           'accept': 'applications/json'}

game = "skyrim"

mods = {}

x = range(10, 20)
for mod_id in x:
    print(f"I'm on mod number: {mod_id}!")
    html = str(BeautifulSoup(requests.get(f"https://www.nexusmods.com/{game}/mods/{mod_id}").content).h3)
    print(html[html.find('>') + 1:html.find('<', 2)])
    if not any(x in html for x in ["Hidden mod", "Not Found"]):
        r = requests.get(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files.json", headers=headers)
        if r.ok:
            c = json.loads(r.content)
            files = c['files']
            x = range(1, len(files))
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
                    'external_virus_scan_url': file['external_virus_scan_url'],
                    'key': AUTH_KEY
                }
                requests.post(api_url, params=params)
        else:
            print(f"Mod gone, oh man :c:{r.status_code}")
    else:
        print("Welp its hidden")

        # file_dict = {}
        # for file in c['files']:
        #     mod_name = file['name']
        #     mod_description = file['description']
        #     links = []
        #     if file['category_id'] < 6:
        #         file_id = str(file['file_id'])
        #         r = requests.get(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files/
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
