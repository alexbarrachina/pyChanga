# %% setup
from pyChanga import *
from random import choice

notes = [60, 64, 67, 72]

# %% melody
# Run this part, change the notes, and run it again.
while True:
    piano(choice(notes), 0.7, 0.5)

# %% bass
# Bring in a second voice without stopping the melody.
while True:
    bass(36, 0.6, 2)
    bass(43, 0.6, 2)

# %% rhythm
while True:
    drumSeq("k-h-s-h-", 0.25)
