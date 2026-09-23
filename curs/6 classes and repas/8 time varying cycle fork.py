# %% setup
from pyChanga import *
from itertools import cycle

tempo(90)

def do_oboe():
    p = [69, 72, 71, 64, 66, None, 62]
    d = [1.0, 0.5, 0.75, 0.25, 1.0]
    v = [0.5, 0.7, 0.3]
    for pitch, volume, dur, in zip(cycle(p), cycle(v), cycle(d)):
        oboe(pitch, volume, dur)

def do_clarinet():
    p = [76, 78, 77, 79, None]
    d = [2.0, 0.5, 1.0]
    v = [0.3, 0.5, 0.4, 0.6, 0.9, 0.6, 0.4]
    for pitch, volume, dur, in zip(cycle(p), cycle(v), cycle(d)):
        clarinet(pitch, volume, dur)

# %% oboe
do_oboe()
# %% clarinet
do_clarinet()