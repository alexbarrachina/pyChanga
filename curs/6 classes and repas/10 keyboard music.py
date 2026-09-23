from pyChanga import *

set_piano()

def key_listener(key, code):
    print(key)
    piano(ord(key)-24, 1.0, 0.06)


register_keyboard_listener(key_listener)

while True:
    piano(72, 1, 0.5)
