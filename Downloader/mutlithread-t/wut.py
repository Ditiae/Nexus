import threading
import time

from tqdm import tqdm

import gui

gui.init_array()
gui.draw()

gui.set_info(1, "HELLO WORLD")
gui.set_info(1, "NOPE")
time.sleep(3)
gui.clear_quadrant(1)