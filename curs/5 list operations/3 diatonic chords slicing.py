# %% setup
from pyChanga import *
          
# A tipical training arpeggio, slicing from a scale
scale = [48, 50, 52, 53, 55, 57, 59,
         48+12, 50+12, 52+12, 53+12, 55+12, 57+12, 59+12,
         48+24, 50+24, 52+24, 53+24, 55+24, 57+24, 59+24]


# %% 1st example   
# Using the same scale, a diatonic chords progression
for i in range(17):
    x = scale[0+i:7+i:2]
    piano(x, 0.7, 0.5) 			
    wait(0.5)

# Notice the "index out of range" error

# %% 2nd example
for i in range(18):
    chord = scale[i:i+7:2]
    piano(chord, 0.7, 1.)
