from pyChanga import *

tempo(120)

# %% simpsons1
while True:
    for pitch in [60, 64, 66, 69, 67, 64]:
        clarinet(pitch, 0.8, 0.25)

# %% simpsons2
i=0
while True:
    for pitch in [60, 64, 66, 69, 67, 64]:
        if i % 5 == 0:
            oboe(pitch-12, 0.8, 1., block=False)
        clarinet(pitch, 0.8, 0.25)
        i=i+1
        

# %% full simpsons
# afegeix el temps al loop, afegeix un acord pedal
pitch_list = [60, 64, 66, 69, 67, 64, 60, 57, 54, 54, 54, 55]
dur_list = [1.5, 1.0, 1.0, 0.5, 1.5, 1.0, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5]

oboe([76, 79, 84], 0.8, 10.0, block=False)


for pitch, duration in zip(pitch_list, dur_list):
        clarinet(pitch, 0.8, duration)
