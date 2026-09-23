# %% setup
from pyChanga import *

# %% 1st example
for pitch in range(50, 67):
    if pitch < 58:
        piano(pitch, 0.7, 0.25)
    else:
        cbass(pitch-24, 0.7, 0.25)

# %% 2nd example
# we can use more than one sentence inside the if
for pitch in range(50, 67):
    if pitch < 58:
        piano(pitch, 0.7, 0.25)
        piano(pitch, 0.7, 0.25)
    cbass(pitch-24, 0.7, 0.25)

