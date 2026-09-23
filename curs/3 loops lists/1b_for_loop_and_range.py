# %% setup
from pyChanga import *

# %% 1st example
# A chromatic sequence using a list
for p in [55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79]:
    piano(p, 0.7, 0.25)

# %% 2nd example
# the same, using range
for p in range(55, 80):
    piano(p, 0.7, 0.25)
    
# %% 3rd example
# Play multiple notes inside the loop
# We will start with C and a perfect 4th below (a G)
for p in range(55, 80):
    piano(p, 0.7, 0.2)
    piano(p-5, 0.7, 0.1)

for p in range(55, 80, 3):
    piano(p, 0.7, 0.25)

for pitch in range(57, 34, 3):  
    piano(60, 0.7, 0.2)
    piano(59, 0.7, 0.2)
    piano(60, 0.7, 0.2)
    piano(pitch, 0.7, 0.2)
