from pyChanga import *

# we can define functions to take arguments

def oboe_gesture(shift):
    oboe(72 + shift, 0.9, 0.125)
    oboe(79 + shift, 0.9, 0.125)
    oboe(78 + shift, 0.6, 0.75)

oboe_gesture(1)
oboe_gesture(7)
wait(0.5)
oboe_gesture(0)

# oboe_gesture(0) is not the same as oboe_gesture()

