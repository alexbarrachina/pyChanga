from pyChanga import *
from random import randint

while True:
    rnum = randint(1, 3)
    drums(36, 0.5, 0.125) 
    if(rnum == 1):
        drums(37, 0.5, 0.25)
    else:
        wait(0.25)

'''
# randomize the drum hits
while True:
    rnum = randint(1, 3)
    drums(36, 0.5, 0.125) 
    if(rnum == 1):
        rpitch = randint(38, 56)
        drums(rpitch, 0.5, 0.25)
    else:
        wait(0.25)
'''       
