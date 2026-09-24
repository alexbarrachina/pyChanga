from pyChanga import *

pitches = [64, 66, 71, 73, 74, 66, 64, 73, 71, 66, 74, 73]

def piano_part():
    while True:
        for pitch in pitches:
            piano(pitch, 1., dur)

dur=0.25
run(piano_part)
# The second pattern is slightly slower.
dur=0.245
run(piano_part)
