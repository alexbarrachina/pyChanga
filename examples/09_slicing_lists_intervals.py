# %% setup
from pyChanga import *
tempo(60)

scale = [0, 2, 4, 5, 7, 9, 11, 0, 2, 4, 5, 7, 9, 11, 0, 2, 4, 5, 7, 9, 11]

# %% loop1
slice1 = scale[0:21:3]
while True:
    for interval in slice1:
        organ(interval + 48, 0.8, 2)

# %% loop2
i = 0
while True:
    slice2 = scale[0:i % 7]
    print(slice2)
    for interval in slice2:
        marimba(interval + 60, 0.55, 0.25)
    i = i + 1

# %% loop3
while True:
    i = 1
    while i < 5:
        for j in range(0, 21, i):
            piano(scale[j] + 48, 0.5, 0.125)
        i = i + 1
