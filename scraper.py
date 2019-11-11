import requests
import json
import os

API_KEY = os.environ['API_KEY']

headers = {'apikey': API_KEY,
           'accept': 'applications/json'}

game = "skyrim"

mods = {}

with open(f"{game}.json") as json_file:
    mods = json.load(json_file)

x = range(607, 608)
# x = range(100000, 100010)
for mod_id in x:
    print(f"I'm on mod number: {mod_id}!")
    r = requests.get(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files.json", headers=headers)
    if r.status_code == 200:
        c = json.loads(r.content)
        file_dict = {}
        for file in c['files']:
            mod_name = file['name']
            mod_description = file['description']
            links = []
            if file['category_id'] < 6:
                file_id = str(file['file_id'])
                r = requests.get(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files/{file_id}/download_"
                                 f"link.json", headers=headers)
                c = json.loads(r.content)
                print("starting download")
                url = c[1]['URI']
                print(url)

                with requests.get(url, stream=True) as s:
                    s.raise_for_status()
                    os.makedirs(os.path.join("mods", mod_name))
                    with open(os.path.join("mods", mod_name,
                                           url[url.find(str(mod_id)) + (len(str(mod_id)) + 1):url.find('?')]),
                              'wb+') as m:
                        for chunk in s.iter_content(chunk_size=8192):
                            if chunk:  # filter out keep-alive new chunks
                                m.write(chunk)
                print("finished")
                for link in range(len(c)):
                    links.append(str(c[link]['URI'].replace(" ", "%20")))
            file_dict[str(file_id)] = tuple([str(mod_name), str(mod_description), links])
        mods[str(mod_id)] = file_dict
    else:
        print(f"Mod gone, oh man :c:{r.status_code}")

with open(f"{game}.json", "w+") as json_file:
    json.dump(mods, json_file, indent=4, sort_keys=True)
