import pprint

import psycopg2 as psycopg2
import requests
import json
import os
from bs4 import BeautifulSoup

API_KEY = os.environ['API_KEY']

headers = {'apikey': API_KEY,
           'accept': 'applications/json'}

game = "skyrim"

conn = psycopg2.connect(host="localhost", port=5432, database="nexusmods", user="postgres", password=os.environ['DB_PASS'])

cursor = conn.cursor()

mods = {}

x = range(1, 150)
# x = range(100000, 100010)
for mod_id in x:
    print(f"I'm on mod number: {mod_id}!")
    html = str(BeautifulSoup(requests.get(f"https://www.nexusmods.com/{game}/mods/{mod_id}").content).h3)
    print(html[html.find('>')+1:html.find('<', 2)])
    if not any(x in html for x in ["Hidden mod", "Not Found"]):
        r = requests.get(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files.json", headers=headers)
        if r.ok:
            c = json.loads(r.content)
            files = c['files']
            x = range(1, len(files))
            for n in x:
                file = files[n]
                j = json.loads(requests.get(file['content_preview_link']).content)
                insert_query = """ INSERT INTO GAME (MOD_ID, MOD_NAME, MOD_DESC, MOD_VERSION, SIZE_KB, CATEGORY_NAME, 
                CONTENT_PREVIEW, UPLOADED_TIME, EXTERNAL_VIRUS_SCAN_URL) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""".replace("GAME", f"{game}")
                record_to_insert = (f"{mod_id}.{n}", file['name'], file['description'], file['version'],
                                    file['size_kb'], file['category_name'], json.dumps(j), file['uploaded_time'],
                                    file['external_virus_scan_url'])
                cursor.execute(insert_query, record_to_insert)
                conn.commit()
            # bfile_dict = {}
            # for file in c['files']:
            #     mod_name = file['name']
            #     mod_description = file['description']
            #     links = []
            #     if file['category_id'] < 6:
            #         file_id = str(file['file_id'])
            #         r = requests.get(f"https://api.nexusmods.com/v1/games/{game}/mods/{mod_id}/files/{file_id}/download_"
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
        else:
            print(f"Mod gone, oh man :c:{r.status_code}")
    else:
        insert_query = """ INSERT INTO GAME (MOD_ID, MOD_NAME, MOD_DESC, MOD_VERSION, SIZE_KB, CATEGORY_NAME, 
                        CONTENT_PREVIEW, UPLOADED_TIME, EXTERNAL_VIRUS_SCAN_URL) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""".replace("GAME", f"{game}")
        record_to_insert = (f"{mod_id}", html[html.find('>')+1:html.find('<', 2)], "", "0",
                            "0", "HIDDEN", None, None,
                            None)
        cursor.execute(insert_query, record_to_insert)
        conn.commit()
        print("Welp its hidden")

conn.close()
