from pyChanga import *

set_piano()

time_list = []
notes_list = []

def key_listener(key, code):
    global counter
    global count_max
    global recording
    global playing
    global time_list
    global notes_list
    print(key)
    print(counter)
    if key =='r':
        recording = True
        print("recording")
        counter = 0
    if key =='s':
        recording = False
        playing = True
        count_max = counter
        counter = 0
        print("playing")
    if len(key) == 1: 
        piano(ord(key)-24, 1.0, 0.01, block=False)
    if len(key) == 1 and recording: 
        notes_list.append(ord(key)-24)
        time_list.append(counter)
    

register_keyboard_listener(key_listener)

counter = 0
recording = False
playing = False
count_max = 0

while True:
    counter += 1

    if playing :
        if counter > count_max:
            counter = 0
        if counter in time_list:
            ind = time_list.index(counter)
            piano(notes_list[ind], 1.0, 0.01)
        else:
            wait(0.01)
    else:
        wait(0.01)
        