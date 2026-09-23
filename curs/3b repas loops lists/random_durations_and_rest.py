from pyChanga import *
from random import randint

for _ in range(2):  
    for pitch in [60, 64, 67, 72]:
        dur = randint(5, 15) / 10     # pick a duration between 0.5 to 1.5
        violin(pitch, 1, dur)
        
        if randint(0,5) < 2.:  
            wait(randint(0,5)/5)