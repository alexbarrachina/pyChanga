from pyChanga import *

scale = [68, 66, 65, 63, 61, 60, 58, 68-12, 66-12, 65-12, 63-12, 61-12, 60-12, 58-12, 68-24, 66-24, 65-24, 63-24, 61-24, 60-24]

# enumerate returns the elements in the list (pitch) and the position of the elements in the list (i)

for i, pitch in enumerate(scale):
    if i % 5 == 0:                        # selecting by position in the scale
        print(i)
        clarinet(pitch-i, 0.9, 1.0, block=False)
    piano(pitch, 0.7, 0.25)