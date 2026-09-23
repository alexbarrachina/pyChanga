# %% setup
from pyChanga import *

tempo(100)

def sax_part():
    while True:
        sax(74, 0.7, 1.0)
        sax(73, 0.7, 1.0)
        sax(72, 0.7, 5 / 6)
        sax(70, 0.7, 0.5)
        sax(67, 0.7, 1 / 6)
        sax(66, 0.7, 1 / 3)
        sax(62, 0.7, 1 / 6)
        sax(64, 0.7, 1 / 3)
        sax(66, 0.7, 1 / 6)
        sax(67, 0.7, 1 / 3)
        sax(69, 0.7, 1 / 6)
        sax(70, 0.7, 1 / 3)
        sax(72, 0.7, 1 / 6)

def bass_part():
    while True:
        for pitch in [38, 32, 33, 39, 38, 44, 43]:
            bass(pitch, 0.7, 0.5)
        bass(37, 0.9, 0.5 / 3)
        bass(38, 0.9, 0.5 / 3)
        bass(39, 0.9, 0.5 / 3)

# %% sax_part
sax_part()

# %% main_voice
bass_part()
