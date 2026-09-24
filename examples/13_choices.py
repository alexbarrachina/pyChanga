from pyChanga import *
from random import choice, choices

# Use choice, choices to select notes/chords from a scale
scale = [48, 50, 52, 53, 55, 57, 59, 60]

def choicer1():
    while True:
        pitch = choice(scale)
        piano(pitch+12, 1., 0.25)
        silence = choice([0,0,0,0,0,0,0,0.25,0.25,0.5])
        wait(silence)

def choicer2():
    while True:
        pitch = choices(scale, weights=[10,1,4,3,7,3,4,5], k=3)
        print(pitch)
        organ(pitch, 1., 0.5)
    
run(choicer1)
wait(0.125)
run(choicer2)