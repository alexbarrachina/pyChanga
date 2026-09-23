# %% setup
from pyChanga import *
from random import randint

# General MIDI drum pitches: 36 kick, 38 snare, 42 closed hi-hat, 49 crash.

# %% rhythm
while True:
    for step in range(8):
        drums(42, 0.35, 0.25, block=False)
        if step == 0 or step == 4:
            drums(36, 0.8, 0.25, block=False)
        if step == 2 or step == 6:
            drums(38, 0.65, 0.25, block=False)
        if randint(0, 15) == 0:
            drums(45, 0.45, 0.25, block=False)
        wait(0.25)

# %% bass
while True:
    for pitch in [36, 36, 43, 39]:
        bass(pitch, 0.5, 0.5)
