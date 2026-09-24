from pyChanga import *

tempo(120)

# pitch and duration lists
pitch_list = [60, 64, 66, 69, 67, 64, 60, 57, 54, 54, 54, 55]
dur_list = [1.5, 1.0, 1.0, 0.5, 1.5, 1.0, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5]

# a list instead of a single note play a chord
oboe([76, 79, 84], 0.8, 10.0, block=False)

# use zip to select pitches and the corresponding durations at the same time
for pitch, duration in zip(pitch_list, dur_list):
        clarinet(pitch, 0.8, duration)

wait(2)
# use slicing to build a sequence of diatonic chords 
scale = [48, 50, 52, 53, 55, 57, 59,
         48+12, 50+12, 52+12, 53+12, 55+12, 57+12, 59+12,
         48+24, 50+24, 52+24, 53+24, 55+24, 57+24, 59+24]

for i in range(18):
    chord = scale[i:i+7:2]
    piano(chord, 0.7, 1.)