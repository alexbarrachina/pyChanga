from pyChanga import *
from random import randint

while True:
    rnum = randint(1, 3)
    drums(36, 0.5, 0.125) 
    if(rnum == 1):
        drums(40 , 0.5, 0.25)
    else:
        wait(0.25)
        
'''
while True:
    rnum = randint(1, 3)
    drums(36, 0.5, 0.125) 
    if(rnum == 1):
        rpitch = randint(40, 72)
        drums(rpitch, 0.5, 0.25)
    else:
        wait(0.25)
        
rpitch = 60
while True:
    drums(36, 0.5, 0.125) 
    if(randint(1, 2) == 1):
        if(randint(1, 3)==1):
            rpitch = randint(40, 72)
        drums(rpitch, 0.5, 0.25)
    else:
        wait(0.25)
'''