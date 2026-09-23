''' Build a Looper by repeating letters
- Insert a new note in a sequence when you press a key
- SPACE will be silence
- 'z' will erase the last note in the sequence
- 'x' will erase the first note in the sequence
Customize your looper however you like.
'''

from pyChanga import *

set_piano()

def key_listener(key, code):
    print(ord(key))


register_keyboard_listener(key_listener)

while True:
    piano(60, 1, 0.5)