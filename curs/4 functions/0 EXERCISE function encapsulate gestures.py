from pyChanga import *

oboe(72, 0.9, 0.125)
oboe(79, 0.9, 0.125)
oboe(78, 0.6, 0.75)
oboe(72, 0.9, 0.125)
oboe(79, 0.9, 0.125)
oboe(78, 0.6, 0.75)
wait(0.5)
oboe(72, 0.9, 0.125)
oboe(79, 0.9, 0.125)
oboe(78, 0.6, 0.75)

# Re-write the following code in order to reduce lines of code defining a function oboe_gesture() that encapsulates a repeating gesture.
# Note that:
# - It's not easy to use a loop (while or for) because that wait() in the middle.
# - In addition to reducing the code, a function allows us to treat this gesture as a single action.