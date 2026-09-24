# %% setup
from pyChanga import *

# build your scale using scale functions like major_scale(), natural_minor_scale(), pentatonic_scale()
scale = natural_minor_scale(60)

# %% moving_window
while True:
    for start in range(7):
        for pitch in scale[start:start + 4]:
            marimba(pitch, 0.55, 0.25)

# %% harmony
while True:
    for degree in [0, 3, 5, 4]:
        organ(scale[degree:degree + 5:2], 0.6, 4)
