from pyChanga import *

# choose 1st and 4rd to play bass notes (0 and 6 every octave)

for pitch in range(60, 90, 3):    # ascending arpeggio every 3 half-tones
    if pitch % 6 == 0:
        cbass(pitch-12, 1.0, 1.0, block=False) # block=False plays the note and continue, without waiting for it to end. 
    piano(pitch, 0.6, 0.125)
    piano(pitch - 5, 0.6, 0.125)
    piano(pitch, 0.6, 0.125)
    piano(pitch +2, 0.6, 0.125)