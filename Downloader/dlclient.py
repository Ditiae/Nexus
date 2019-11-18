import zipfile
import requests
from loguru import logger
import json
import shutil
import os
import time
import sys

# TODO: Add support for gamespecific download directory

# -- FUNCTIONS --
def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def make_mod_dir(id):
    id = str(id)
    dir_string = f"{download_dir}\\{id}"
    make_dir(dir_string)
    return dir_string

# -- INITIALISATION --
# load settings
with open("settings.json") as f:
    SETTINGS = json.load(f)
    download_dir = SETTINGS["download_dir"]
    endpoint = SETTINGS["endpoint"]
    post_args = {
        'key': SETTINGS["auth_key"]
    }
    del SETTINGS

# add error logging
logger.add("error.log", level="ERROR")

# make directory
make_dir(download_dir)

while True:  # to infinity and... nowhere
    print("New cycle | Making request")

    r = requests.post(f"{endpoint}select/", data=post_args)

    if not r.ok:
        if r.status_code == 500:  # catastrophic API failiure
            logger.error("Catastrophic API failiure has occured. Inform 0x5444#8669 ASAP.\nResponse from API: {r.text}\nResponse headers: {r.headers}\nResponse code: 500\nExiting now.")
            sys.exit()

        elif r.status_code == 404:  # no rows found
            time.sleep(10)
            continue

    else:
        print("Parsing...")
        j = r.json()
        mod_id = str(j["content"]["mod_id"]).split(".")[0]  # remove decimal point
        original_mod_id = j["content"]["mod_id"]
        download_url = j["content"]["download_url"]
        mod_name = j["content"]["mod_name"].replace(" ", "_")[:25]
        mod_version = j["content"]["mod_version"].replace(" ", "_")

        print(f"Info | {mod_id} | {mod_name}")

        # download mod
        mod_dir = make_mod_dir(mod_id)
        zip_name = f"{mod_dir}\\{mod_name}-{mod_version}.zip"
        source_name_from_url = download_url.split('/')[-1].split("?")[0]

        print(f"Open ZIP {zip_name}")
        with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_LZMA) as zip_f:
            with zip_f.open(source_name_from_url, "w") as f:
                print("Downloading...")
                with requests.get(download_url, stream=True) as r:
                    shutil.copyfileobj(r.raw, f)

        print("File download completed | Making remove request")

        r = requests.post(f"{endpoint}remove/", data={**post_args, "mod_id": original_mod_id})
        if not r.ok:
            if r.status_code == 500:  # catastrophic API failiure
                logger.error("Catastrophic API failiure has occured. Inform 0x5444#8669 ASAP.\nResponse from API: {r.text}\nResponse headers: {r.headers}\nResponse code: 500\nExiting now.")
                sys.exit()

            elif r.status_code == 404:  # mod_id not found
                logger.error(f"Remove endpoint sent the following error details\nMod ID {original_mod_id}\nResponse: {r.text}\nResponse code: 404\nPlease inform 0x5444#8669")

            else:
                logger.error(f"Unhandled API response code.\nMod ID {original_mod_id}\nResponse: {r.text}\nResponse code: {r.status_code}\nExiting now.")
                sys.exit()
        else:
            print("Remove request successful")

        print("Finished!\n")
        sys.exit()
