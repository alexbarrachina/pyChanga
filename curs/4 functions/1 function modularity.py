from pyChanga import *

def oboe_gesture():
    oboe(72, 0.9, 0.125)
    oboe(79, 0.9, 0.125)
    oboe(78, 0.6, 0.75)

def viola_gesture():
    for pitch in range(52,58):
        viola(pitch, 0.7, 0.5/3)
        viola(pitch+5, 0.7, 0.5/3)
        
oboe_gesture()
viola_gesture()
oboe_gesture()

# MODULARITY
# We define pieces of code that could be useful in different situations.
# Example: We can create multiple gestures for multiple instruments and organize them in something like a score