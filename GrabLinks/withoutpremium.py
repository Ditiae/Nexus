import time
import pyautogui
import pyperclip as clip
from pprint import pprint
import imgsearch
import sys

base_url = "https://www.nexusmods.com/{}/mods/{}"
mod = "skyrim"
links = {}


input("Move mouse over the address bar and press enter")
addr_bar = pyautogui.position()

input("Press enter to start\n")

print("Starting")


def new_url(url):
    pyautogui.moveTo(addr_bar)
    pyautogui.click()
    pyautogui.keyDown("ctrl")
    pyautogui.press("a")
    pyautogui.keyUp("ctrl")
    pyautogui.typewrite(f"{url}\n", interval=0.05)


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

for i in range(26079, 26082):

    url = base_url.format(mod, i)
    print(f"\nURL: {url}, mod ID {i}")
    new_url(url)
    time.sleep(2)

    for i in range(3):
        print("Searching for button...")
        pos = imgsearch.imagesearch("vortex.png")
        if pos[0] != -1:
           print("Found at ", pos[0], pos[1])
           vortx_down = pyautogui.Point(pos[0], pos[1])
           break
        else:
            print(f"Button not found, attempt {i} gone")
            time.sleep(2)
            if i == 2:
                sys.exit()

    print("Taking link")
    press_vortx()
    counter = 0
    previous_content = ""
    while True:
        counter += 1
        print(f"\rWaiting for link handler ({counter})", end="")
        with open("share") as f:
            f_content = f.read()
            if f_content != previous_content:
                previous_content = f_content
                links[url] = f_content
                break

    time.sleep(0.2)

    print(f"Got link ({links[url]}")

print("\n\n\n")
pprint(links)
