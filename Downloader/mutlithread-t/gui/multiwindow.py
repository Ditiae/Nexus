import os
import threading
import colorama

from gui.master_array import get_array

master_array = get_array()

def init_array():
    # make titles red

    red_regions = [
        [[15, 26], 1],
        [[15, 26], 13],
        [[56, 67], 1],
        [[56, 67], 13],
    ]

    for r in red_regions:
        master_array[r[0][0]][r[1]] = colorama.Fore.RED + master_array[r[0][0]][r[1]]
        master_array[r[0][1]][r[1]] = master_array[r[0][1]][r[1]] + colorama.Style.RESET_ALL


def draw():
    os.system("cls")
    ostr = ""
    for i in range(len(master_array[0])):
        for row in master_array:
            ostr += row[i]
        ostr += "\n"
    print(ostr)


def write_string(start_coord, chars):
    x = start_coord[0]-1
    y = start_coord[1]-1

    if len(chars) > 27:
        chars = chars[:24]
        for i in range(3):
            chars.append(".")
    else:
        for i in range(27-len(chars)):
            chars.append(" ")

    for i, char in enumerate(chars):
        master_array[x+1][y] = char

        x += 1

    #draw()


def set_status(quadrant, type):
    options = ["Inactive", "Get link", "Download", "Remove link", "clear"]

    if type not in options:
        raise Exception("Specified type not an option")

    quadrants = [
        [13, 3],
        [54, 3],
        [13, 15],
        [54, 15]
    ]

    if type == "clear":
        to_write = []
    elif type == "Inactive":
        to_write = [c for c in "Inactive"]
        to_write[0] = colorama.Fore.CYAN + to_write[0]
        to_write[-1] = to_write[-1] + colorama.Style.RESET_ALL
    else:
        to_write = [c for c in type]
        to_write[0] = colorama.Fore.YELLOW + to_write[0]
        to_write[-1] = to_write[-1] + colorama.Style.RESET_ALL

    write_string(quadrants[quadrant-1], to_write)


def set_url(quadrant, url):
    quadrants = [
        [13, 5],
        [54, 5],
        [13, 17],
        [54, 17]
    ]

    write_string(quadrants[quadrant - 1], [c for c in str(url)])


def set_mod_id(quadrant, mod_id):
    quadrants = [
        [13, 6],
        [54, 6],
        [13, 18],
        [54, 18]
    ]

    write_string(quadrants[quadrant-1], [c for c in str(mod_id)])


def set_mod_name(quadrant, mod_name):
    quadrants = [
        [13, 7],
        [54, 7],
        [13, 19],
        [54, 19]
    ]

    write_string(quadrants[quadrant - 1], [c for c in str(mod_name)])


def set_zip_path(quadrant, zip_path):
    quadrants = [
        [13, 9],
        [54, 9],
        [13, 21],
        [54, 21]
    ]

    write_string(quadrants[quadrant - 1], [c for c in str(zip_path)])


def set_info(quadrant, info):
    quadrants = [
        [13, 11],
        [54, 11],
        [13, 23],
        [54, 23]
    ]

    write_string(quadrants[quadrant - 1], [c for c in str(info)])

def clear_quadrant(quadrant):
    set_status(quadrant, "Inactive")
    set_mod_id(quadrant, "")
    set_mod_name(quadrant, "")
    set_url(quadrant, "")
    set_zip_path(quadrant, "")
    set_info(quadrant, "")
