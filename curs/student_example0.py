from pyChanga import *
from random import randint

c_major = major_scale(60)
 
pattern = [0,-1,-2,-3,-4,-3,-4,-5]
final = [-6,-4,-2,-4,-3,-4,-5,-6,-7]
while True:
    i=0
    while i<3:
        for x in pattern:
            if (x) % 4 == 0:
                cbass(c_major[x-i-7],0.7,0.25,block=False)
            piano(c_major[x+i],0.7,0.25)
        i = i+1
    for y in final:
        if (y % 3 ==0) or (y % 7 == 0):
            cbass(c_major[y-7],0.7,0.25,block=False)
        piano(c_major[y],0.7,0.25)
    wait(1.75)