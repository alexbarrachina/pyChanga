from pyChanga import *

def wrap_in_range(value, high, low):
    return (value - low) % (high - low) + low

interval = 1
pitch = 48

while True:
    cello(pitch, 1.0, 1.0)
    pitch = wrap_in_range( pitch + interval, 36, 60)
    print(pitch, end=",")
    interval += 1 