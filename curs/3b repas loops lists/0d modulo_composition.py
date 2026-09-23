from pyChanga import *

# enumerate returns the elements in the list (pitch) and the position of the elements in the list (i)

while True:
    for i, pitch in enumerate(range(48,72)):
        if i % 5 == 0:                        # selecting by position in the scale
            marimba(pitch+12, 1., 0.5, block=False)
        if i % 3 == 0:                       
            cbass(pitch-12, 0.8, 0.5, block=False)
        if i % 4 == 0:                       
            piano(pitch, 0.7, 0.15)
        else:
            wait(0.15)
