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
wait(0.25)

melody = [2, 1 , 0, -1, 0] 
#offset
