from pyChanga import *

set_piano()

i=0
for i in range (0,24):    
    for pitch in [48,55,60,52,55,60]:
        if pitch % 4 == 0:
            piano(pitch+i+12, 0.7, 0.5, block=False)
        if pitch % 2 == 0:
            piano(pitch+i-12, 0.7, 0.5, block=False)
        if pitch % 3 == 0:
            piano(pitch+i+3, 0.7, 0.5, block=False)
        if pitch % 5 == 0:
            piano(pitch+i-24, 0.7, 0.5, block=False)
        
        piano(pitch+i, 0.7, 0.25)
        piano(pitch+i+3, 0.7, 0.125)
        piano(pitch+i, 0.7, 0.125)
        piano(pitch+i-5, 0.7, 0.5)
        piano(pitch+i, 0.7, 0.25)
        
        i+=4