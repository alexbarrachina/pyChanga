from pyChanga import *

set_piano()

def key_listener(key, code):
    print(key)
    piano(ord(key)-34, 1.0, 0.06, block=False)


register_keyboard_listener(key_listener)

while True:
    piano(60, 1, 0.5)

'''
jjkjh
'''