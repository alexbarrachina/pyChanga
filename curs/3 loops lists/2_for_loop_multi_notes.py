# %% setup
from pyChanga import *

# %% 1st example
# for every note in the range, we play now 2 notes.
# We will start with C and a perfect 4th below (a G)
for pitch in range(60, 72):
    piano(pitch, 0.7, 0.125)
    piano(pitch - 5, 0.7, 0.125)

# %% 2nd example
# Notice that we always play the same pattern, but starting with different notes.
for pitch in range(60, 90, 3):
    piano(pitch, 0.7, 0.125)
    piano(pitch - 5, 0.7, 0.125)
    piano(pitch, 0.7, 0.125)
    piano(pitch +2, 0.7, 0.125)
