from pyChanga import *

pitches = [64, 66, 71, 73, 74, 66, 64, 73, 71, 66, 74, 73]


def piano_part():
    while True:
        for pitch in pitches:
            piano(pitch, 1.0, 0.25)


fork(piano_part, initial_tempo=100)

tempo(20)
piano_part()
