from pyChanga import *

# MODULO operator.
# give you the reminder, when a number is divided by another number
# In this example, the even numbers will be played 1 octave higher, the odds, a major 3rd lower

for pitch in range(50, 80):
    if pitch % 3 == 0:
        piano(pitch+12, 0.7, 0.125)
    else:
        piano(pitch-4, 0.7, 0.125)
      