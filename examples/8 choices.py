# %% setup
from pyChanga import *
from random import choice, choices

scale = [60, 62, 64, 65, 67, 69, 71, 72]

# %% 1st example
while True:
    pitch = choice(scale)
    piano(pitch, 1., 0.25)

# %% 2nd example
while True:
    pitch = choices(scale, weights=[10,1,4,3,7,3,4,5], k=3)
    print(pitch)
    piano(pitch, 1., 0.25)
    
