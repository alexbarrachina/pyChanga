from pyChanga import *

pattern = [68, 66, 65, 63, 61, 60, 58, 68-12, 66-12, 65-12, 63-12, 61-12, 60-12, 58-12, 68-24, 66-24, 65-24, 63-24, 61-24, 60-24]

for offset in range(30, 0, -3):
    for note in pattern:
        pitch = note + offset
        piano(pitch, 0.5, 0.25)
        if(pitch % 6 > 0):
            piano(note+offset-24, 0.5, 1.0, block=False)       
    wait(0.25)

