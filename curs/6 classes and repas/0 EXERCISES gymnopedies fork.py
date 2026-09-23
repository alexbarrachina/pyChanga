from pyChanga import *

tempo(90)

# Same exercise but using 2 separate functions for left hand and right hand.
# The piece will start after 4 mesures, lhand and rhand will play together for 4 mesures, 4 mesures lhand only again, etc...
# rhand will sound a little bit louder than lhand.

set_piano()

lhand = [43, [59,62, 66], 38, [57, 61, 66]]
rhand = [0, 78, 81, 79, 78, 73, 71, 73, 74, 69, 0, 0] 


    