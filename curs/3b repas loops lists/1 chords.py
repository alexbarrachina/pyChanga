from pyChanga import *

set_vibra()

M7 = [60, 64, 67, 71]

vibra(M7, 1., 2)

piece = [ [60, 64, 67, 71], 72, 71, 75, [60, 63, 67, 70], 74, 72]

for notes in piece:
    vibra(notes, 1., 0.5)

