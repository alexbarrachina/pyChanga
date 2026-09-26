# %% setup
from pyChanga import *
from random import randint

voice, length_ms = load_sample("samples/rare54.wav")

# %% loop1
while True:
    sampl(voice, 0.7, 0.25, start=randint(0,9)/10.)
    piano(63, 0.7, 0.25)
    sampl(voice, 0.7, 0.25, start=0.2)
    sampl(voice, 0.7, 0.25)

# %% loop2
while True:
    bass(63-12, 1, 0.25)
    sampl(voice, 0.7, 0.5, rate=0.5)

# %% loop3
while True:
    chip(randint(48,70), 1, 0.25)
    sampl(voice, 1, 1, rate=0.25)
