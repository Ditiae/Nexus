import time
import pyautogui
from pprint import pprint
import imgsearch
import sys
from urllib import parse
import requests
import shutil
import os
import json

base_url = "https://www.nexusmods.com/{}/mods/{}"
mod = "skyrim"
links = {}


input("Move mouse over the address bar and press enter")
addr_bar = pyautogui.position()

input("Press enter to start\n")

print("Starting")

# --- GUI AUTOMATION ---


def new_url(url):
    pyautogui.moveTo(addr_bar)
    time.sleep(0.1)
    pyautogui.click()
    time.sleep(0.1)
    pyautogui.keyDown("ctrl")
    pyautogui.press("a")
    pyautogui.keyUp("ctrl")
    time.sleep(0.1)
    pyautogui.typewrite(f"{url}", interval=0.05)
    time.sleep(0.1)
    pyautogui.press("delete")  # removes any autocomplete
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.1)


def press_vortx():
    pyautogui.moveTo(vortx_down)
    pyautogui.click()
    """ # would copy new URL to clipboard
    time.sleep(1.5)
    pyautogui.moveTo(addr_bar)
    pyautogui.click()
    pyautogui.keyDown("ctrl")
    pyautogui.press("a")
    pyautogui.keyUp("ctrl")
    pyautogui.keyDown("ctrl")
    pyautogui.press("c")
    pyautogui.keyUp("ctrl")
    pyautogui.press("esc")
    """


# --- OTHER FUNCTIONS ---


def parse_uri(uri):
    u = parse.urlparse(uri)
    q = parse.parse_qs(u.query)
    o = {}
    o["mod_id"] = u[2].split("/")[2]
    o["file_id"] = u[2].split("/")[-1]
    o["key"] = q["key"][0]
    o["expiry"] = q["expires"][0]
    return o


def download_file(url, path):
    if not os.path.exists(path):
        os.makedirs(path)
    local_filename = f"{path}\\" + url.split('/')[-1].split("?")[0]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename


# Load settings and setup headers
with open("settings.json") as f:
    settings = json.loads(f.read())

api_key = settings["api_key"][0]

headers = {
    'apikey': api_key,
    'accept': 'applications/json'
}

for i in range(8, 18):

    mod_id = int(i)  # casting to int forces it to copy instead of store a reference
    url = base_url.format(mod, mod_id)
    print(f"\nMod ID {i}")
    new_url(url)
    time.sleep(2.5)

    hc = False
    for i in ["notfound.png", "hidden.png"]:
        position = imgsearch.imagesearch(i)
        if position[0] != -1:
            print("Mod either hidden or not found. Moving to next mod.")
            hc = True
            break

    if hc:
        continue

    hc = False
    for i in range(5):
        e = "." * i
        print(f"\rSearching for button{e}", end="")
        position = imgsearch.imagesearch("vortex.png")
        if position[0] != -1:
           print("\nFound at ", position[0], position[1])
           vortx_down = pyautogui.Point(position[0], position[1])
           break
        else:
            time.sleep(0.25)
            if i == 4:
                print("\nButton not found. Moving to next mod.")
                hc = True
                break

    if hc:
        continue

    print("Taking link")

    press_vortx()
    counter = 0
    while True:
        counter += 1
        print(f"\rWaiting for link handler ({counter})", end="")

        with open("share", "r+") as f:
            f_content = f.read()
            if f_content != "":
                links[mod_id] = parse_uri(f_content)
                f.truncate(0)  # empties file
                break

    time.sleep(0.5)

    print(f"\nGot link ({links[mod_id]})")

    u = f"https://api.nexusmods.com/v1/games/skyrim/mods/{links[mod_id]['mod_id']}/files/{links[mod_id]['file_id']}/download_link.json"
    r = requests.get(u, headers=headers, params={"key": links[mod_id]["key"], "expires": links[mod_id]["expiry"]})
    print("downloading")
    print(r.json()[0]["URI"])
    download_file(r.json()[0]["URI"], f"downloads/{mod_id}/{links[mod_id]['file_id']}")
    print("done")

print("\n\n\n")
pprint(links)
