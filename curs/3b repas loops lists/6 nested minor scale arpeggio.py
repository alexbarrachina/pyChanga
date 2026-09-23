from pyChanga import *
from itertools import cycle

tempo(100)

d_minor = natural_minor_scale(60)

llista = [60,69,64]


for i in cycle(llista):
    violin(i, 0.8, 0.25)

