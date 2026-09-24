# %% setup
from pyChanga import *

tempo(100)

def clarinet_part():
    while True:
        clarinet(74, 0.7, 1.0)
        clarinet(73, 0.7, 1.0)
        clarinet(72, 0.7, 5 / 6)
        clarinet(70, 0.7, 0.5)
        clarinet(67, 0.7, 1 / 6)
        clarinet(66, 0.7, 1 / 3)
        clarinet(62, 0.7, 1 / 6)
        clarinet(64, 0.7, 1 / 3)
        clarinet(66, 0.7, 1 / 6)
        clarinet(67, 0.7, 1 / 3)
        clarinet(69, 0.7, 1 / 6)
        clarinet(70, 0.7, 1 / 3)
        clarinet(72, 0.7, 1 / 6)

def bass_part():
    while True:
        for pitch in [38, 32, 33, 39, 38, 44, 43]:
            cbass(pitch, 0.7, 0.5)
        cbass(37, 0.9, 0.5 / 3)
        cbass(38, 0.9, 0.5 / 3)
        cbass(39, 0.9, 0.5 / 3)

# %% conductor
run(clarinet_part)  # clarinet_part1
run(bass_part)      # bass_part1, playing independently
