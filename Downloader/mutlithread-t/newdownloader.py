import json
import sys
import threading
import time
import zipfile
from io import StringIO

import requests
import os
from loguru import logger
from tqdm import tqdm

import gui


# -- FUNCTIONS --
def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def make_mod_dir(id_input):
    id_input = str(id_input)
    dir_string = f"{download_dir}\\{id_input}"
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


# thread function
def dlt(id):
    global task_transmission

    class IOWrapper(StringIO):
        def write(self, s):
            #gui.set_info(id, s.replace("\n", "").replace("\r", ""))
            return len(s)

    while True:
        if task_transmission[f"thread_{id}"] is not None:
            task = task_transmission[f"thread_{id}"]

            mod_id = task["mod_id"]
            original_mod_id = task["original_mod_id"]
            download_url = task["download_url"]
            mod_name = task["mod_name"]
            mod_version = task["mod_version"]

            # download mod
            mod_dir = make_mod_dir(mod_id)
            zip_name = f"{mod_dir}\\{mod_name}-{mod_version}.zip"
            source_name_from_url = download_url.split('/')[-1].split("?")[0]

            gui.set_zip_path(id, zip_name)
            gui.set_mod_name(id, mod_name)
            gui.set_mod_id(id, original_mod_id)
            gui.set_url(id, download_url)


            with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_LZMA) as zip_f:
                with zip_f.open(source_name_from_url, "w") as f:
                    gui.set_status(id, "Download")
                    gui.draw()

                    with requests.get(download_url.replace(" ", "%20"),
                                      stream=True) as r:  # It should NOT take 40 minutes to download 1.6GBs
                        for chunk in tqdm(r.iter_content(chunk_size=8192), unit="MB", unit_scale=0.008192, file=IOWrapper()):
                            r.raise_for_status()
                            if chunk:  # filter out keep-alive new chunks
                                f.write(chunk)

                    # with requests.get(download_url.replace(" ", "%20"), stream=True) as r:  # this is supposedly 3x faster than f.write chunk
                    #    shutil.copyfileobj(r.raw, f)


            r = requests.post(f"{endpoint}remove/", data={**post_args, "mod_id": original_mod_id})

            if not r.ok:
                if r.status_code == 500:  # catastrophic API failiure
                    logger.error("API failiure has occured. Inform 0x5444#8669 ASAP.\nResponse from API: "
                                 "{r.text}\nResponse headers: {r.headers}\nResponse code: 500\nExiting now.")
                    sys.exit()

                elif r.status_code == 404:  # mod_id not found
                    logger.error(f"Remove endpoint sent the following error details\nMod ID {original_mod_id}\nResponse:"
                                 f" {r.text}\nResponse code: 404\nPlease inform 0x5444#8669")

                else:
                    logger.error(f"Unhandled API response code.\nMod ID {original_mod_id}\nResponse: {r.text}\nResponse"
                                 f" code: {r.status_code}\nExiting now.")
                    sys.exit()

            task_transmission[f"thread_{id}"] = None
            gui.clear_quadrant(id)
            gui.draw()

# setup threads
dl_threads = [
    threading.Thread(target=dlt, args=(1,)),
    threading.Thread(target=dlt, args=(2,)),
    threading.Thread(target=dlt, args=(3,)),
    threading.Thread(target=dlt, args=(4,))
]

# setup thread task transmission
task_transmission = {
    "thread_1": None,
    "thread_2": None,
    "thread_3": None,
    "thread_4": None
}

# setup sequencer
queued_tasks = []
def sequencer():
    global queued_tasks
    global task_transmission

    while True:
        try:
            if len(queued_tasks) == 0:
                # no queued_tasks, check for new
                r = requests.post(f"{endpoint}select/", data=post_args)

                if not r.ok:
                    if r.status_code == 403:  # wrong auth key
                        logger.error("Invalid internal API auth key.")
                        sys.exit()

                    elif r.status_code == 500:  # catastrophic API failiure
                        logger.error("API failiure has occured. Inform 0x5444#8669 ASAP.\nResponse from API: {r.text}"
                                     "\nResponse headers: {r.headers}\nResponse code: 500\nExiting now.")
                        sys.exit()

                    elif r.status_code == 404:  # no rows found
                        time.sleep(10)
                        continue

                else:
                    j = r.json()
                    mod_id = str(j["content"]["mod_id"]).split(".")[0]  # remove decimal point
                    original_mod_id = j["content"]["mod_id"]
                    download_url = j["content"]["download_url"]
                    mod_name = j["content"]["mod_name"].replace(" ", "_")[:25]
                    mod_version = j["content"]["mod_version"].replace(" ", "_")

                    proto = {"original_mod_id": original_mod_id, "mod_id": mod_id, "download_url": download_url, "mod_name": mod_name, "mod_version": mod_version}

                    hacky_continue = False
                    for key in task_transmission:
                        if task_transmission[key] is not None:
                            if task_transmission[key]["original_mod_id"] == original_mod_id:
                                hacky_continue = True

                    if hacky_continue:
                        continue

                    queued_tasks.append(proto)

            elif len(queued_tasks) != 0:
                if task_transmission["thread_1"] is None:
                    task_transmission["thread_1"] = queued_tasks.pop(0)
                elif task_transmission["thread_2"] is None:
                    task_transmission["thread_2"] = queued_tasks.pop(0)
                elif task_transmission["thread_3"] is None:
                    task_transmission["thread_3"] = queued_tasks.pop(0)
                elif task_transmission["thread_4"] is None:
                    task_transmission["thread_4"] = queued_tasks.pop(0)
        except KeyboardInterrupt:
            sys.exit()


# setup cli
gui.init_array()

for i in range(4):
    gui.set_status(i+1, "Inactive")

for thread in dl_threads:
    thread.start()

sequencer()