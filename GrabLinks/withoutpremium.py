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
    links[url] = clip.paste()
    print(f"Got link ({links[url]}")

print("\n\n\n")
pprint(links)
