from pyChanga import *

# choose 1st and 4rd to play bass notes (0 and 6 every octave)
# Using block=False, we can create a simultaneous 2ond voices (2 octaves lower)


for pitch in range(60, 90, 3):    # arpegio ascending every 3 half-tones
    if pitch % 6 == 0:
        cbass(pitch-24, 1.0, 1.0, block=False)
    piano(pitch, 0.7, 0.125)
    piano(pitch - 5, 0.7, 0.125)
    piano(pitch, 0.7, 0.125)
    piano(pitch +2, 0.7, 0.125)