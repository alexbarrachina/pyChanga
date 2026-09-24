# %% setup
from pyChanga import *
from random import choice

notes = [60, 64, 67, 72]

# %% melody
# Run this part, change the notes, and run it again.
while True:
    piano(choice(notes), 0.5, 0.25)

# %% bass
# Bring in a second voice without stopping the melody.
while True:
    cbass(36+12, 0.7, 2)
    cbass(43+12, 0.7, 2)

# %% rhythm
while True:
    drumSeq("k-h-s-h-", 0.25)
