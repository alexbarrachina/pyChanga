from pyChanga import *
from random import randint

# why we need to initialize the variables rpitch3?
rpitch3 = 63

while True:
    rpitch1 = randint(45, 72)
    rpitch2 = randint(45, 72)
    if(randint(1, 3) == 1):
        rpitch3 = randint(45, 72)

    drums(45, 0.5, 0.125) 
    drums(rpitch1, 0.5, 0.125) 
    drums(rpitch2, 0.5, 0.25) 
    if(randint(1, 3) == 1):
        drums(rpitch3, 0.5, 0.25)
    else:
        wait(0.25)