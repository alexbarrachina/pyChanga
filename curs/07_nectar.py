from pyChanga import *

from random import choice, randint
tempo(80)

inter = [1, 3, 4, 5, 6, 8]
scale = [-5, 0, 4, -3, 0, 4, 0]
scale2 = [4, 4, 2, 4, 7, 4]
scale3 = [0, -60, 0, -60, -3, -60, 0, -60]

def loop1():
    slice1 = scale[:3]
    while True:
        if randint(0, 10) == 0:
            x = choice(inter)
            slice1 = scale[:x]
        for interval in slice1:
            bass(interval + 48, 0.4, 0.25)

def loop2():
    slice2 = scale2[:1]
    while True:
        if randint(0, 10) == 0:
            x = choice(inter)
            slice2 = scale2[:x]
        for interval in slice2:
            marimba(interval + 60, 0.4, 0.25)
        wait(0.25)

def loop3():
    slice3 = scale3[:5]
    while True:
        wait(0.5)
        if randint(0, 10) == 0:
            x = choice(inter)
            slice3 = scale3[:x]
        for interval in slice3:
            piano(interval + 60, 0.3, 0.125)
        wait(0.125)

run(loop1)
run(loop2)
run(loop3)
