from pyChanga import *
from random import randint

while True:    
    x = randint(40,80)
    drums(x, 1.0,0.6)
    drums(x, 1.0,0.3)
    
    i = randint(0,1)
    if i == 1:
        wait(0.3)
    
    drums(x+1, 1.0,0.3)
    drums(x+2, 1.0,0.3)
    drums(x+3, 1.0,0.3)
    
    i = randint(4,8)
    drums(x+i, 1.0,0.3, block=False) 
    
    i = randint(0,1)
    if i == 1:
        wait(0.3)
