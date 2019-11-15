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


for i in range(8, 18):

    mod_id = int(i)
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
                links[mod_id] = f_content
                f.truncate(0)
                break

    time.sleep(0.5)

    print(f"\nGot link ({links[mod_id]})")

print("\n\n\n")
pprint(links)
