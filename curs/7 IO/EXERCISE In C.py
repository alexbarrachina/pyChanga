'''
In C is a minimalistic musical piece composed by Terry Riley in 1964.
It consists of series of short melodic fragments that can be repeated at the discretion of the musicians.
Performers are expected to play the first phrase once in unison, after which each performer may repeat the phrase
or move on to the next. Each phrase may be repeated an arbitrary number of times at the discretion of each musician
in the ensemble.

- Write a function (called voice()) that play one of the patterns a random number of times between 20 and 60.
- The parameter of the function is the pattern (list) to be played.
- With keys from 1 to 5 you will launch voices with patterns p1 to p5.
'''

from pyChanga import *
from itertools import cycle
from random import randint


set_piano()

p1 = [84, 0, 84, 0, 84, 0, 84, 0]
p2 = [72, 76, 0, 0] 
p3 = [60, 0, 65, 0, 64, 0, 0, 0]
p4 = [64, 0, 65, 0, 67, 0, 0, 0]
p5 = [76, 0, 77, 0, 79, 0, 0, 0]


def voice(patt):
    # Your code here
    pass

def keyboard_listener(key, code):
    # Your code here
    fork(voice, args=(p1,)) # Example of forking with arguments

register_keyboard_listener(keyboard_listener)
wait_forever()

