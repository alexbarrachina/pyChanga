# Adapted from curs/5 list operations/4 slicing lists intervals.py
# Run the named sections independently; re-run a section to replace its part.
# %% setup
from pyChanga import *


scale = [0, 2, 4, 5, 7, 9, 11, 0, 2, 4, 5, 7, 9, 11, 0, 2, 4, 5, 7, 9, 11]

def loop1():
    slice1 = scale[0:21:3]
    while True:
        for interval in slice1:
            organ(interval + 48, 0.8, 2)

def loop2():
    i = 0
    while True:
        slice2 = scale[0:i % 7]
        print(slice2)
        for interval in slice2:
            marimba(interval + 60, 0.65, 0.25)
        i = i + 1

def loop3():
    while True:
        i = 1
        while i < 5:
            for j in range(0, 21, i):
                piano(scale[j] + 72, 0.7, 0.125)
            i = i + 1

# %% loop1
loop1()

# %% loop2
loop2()

# %% main_voice
loop3()
