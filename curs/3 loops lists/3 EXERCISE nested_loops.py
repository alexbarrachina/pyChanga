from pyChanga import *

c_major = major_scale(60)

piano( c_major[3], 1., 0.25)
wait(0.25)
piano( c_major[4], 1., 0.25)
piano( c_major[3], 1., 0.25)
piano( c_major[2], 1., 0.25)
piano( c_major[1], 1., 0.25)
piano( c_major[2], 1., 0.25)
wait(0.25)
piano( c_major[3], 1., 0.25)
piano( c_major[2], 1., 0.25)
piano( c_major[1], 1., 0.25)
piano( c_major[0], 1., 0.25)
piano( c_major[1], 1., 0.25)
wait(0.25)
piano( c_major[2], 1., 0.25)
piano( c_major[1], 1., 0.25)
piano( c_major[0], 1., 0.25)
piano( c_major[-1], 1., 0.25)
piano( c_major[0], 1., 0.25)

# 1/ Try to re-write the melody using
#	- only 4 statements of piano() and
#	- lists with maximum 5 elements.
# Tip: Use the following "melody" list and maybe an "offset" list. 

# melody = [2, 1 , 0, -1, 0] 

# extra/ Try to re-write the melody using
#	- only 2 statements of piano() and
#	- lists with maximum 5 elements.
#	- nested loops
