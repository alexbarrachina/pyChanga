from pyChanga import *

# ascending arpeggio
for pitch in range(57, 34, -3): 
    piano(60, 0.7, 0.1)
    piano(59, 0.7, 0.1)
    piano(60, 0.7, 0.1)
    piano(pitch, 0.7, 0.1)

wait(1)

# descending arpeggio
for pitch in range(60, 90, 3):
    piano(pitch, 0.7, 0.125)
    piano(pitch - 5, 0.7, 0.125)
    piano(pitch, 0.7, 0.125)
    piano(pitch +2, 0.7, 0.125)