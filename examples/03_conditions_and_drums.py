from pyChanga import *
from random import randint

bass_notes=[42-12, 42, 53, 51, 42, 42-12, 53, 51]


# pyChanga drum pitches: 36 kick, 37 snare, 50 hi-hat, 55 tom, 65 cymbal.

while True:
    for step in range(8):
        drums(50, 0.55, 0.25, block=False)
        if step == 0 or step == 4:
            drums(36, 0.8, 0.25, block=False)
        if step == 2 or step == 6:
            drums(37, 0.65, 0.25, block=False)    

        # random hit
        if randint(0, 3) == 0:
            x = randint(55,65)
            drums(x, 0.45, 0.25, block=False)

        # for syncopation
        wait(0.125)       
        bass(bass_notes[step], 1., 0.5, block=False)

        # syncopated random hit
        if randint(0, 2) == 0:
            x = randint(55,65)
            drums(x, 0.45, 0.25, block=False)
        wait(0.125)
        
