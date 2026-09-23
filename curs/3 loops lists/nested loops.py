# %% setup
from pyChanga import *

pattern = [52, 57, 56]


# %% 1st example
# we can repeat the pattern forever using while loop
while True:
    for note in pattern:
        piano(note, 0.5, 0.1)

# %% 2nd example
# or change something in every step while looping
offset = 0
while True:
    for note in pattern:
        piano(note + offset, 0.5, 0.1)
    offset += 3

# %% 3rd example
# a similar strategy, but more elegant

for offset in range(0, 30, 3):    
    print (offset)
    for note in pattern:
        piano(note + offset, 0.5, 0.1)

        

