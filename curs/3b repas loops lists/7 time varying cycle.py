# %% setup
from pyChanga import *
from itertools import cycle

tempo(90)

# %% print forever
llista1 = [2, 7, 4]
llista2 = [30, 20, 10, 100, 200]

for x, y in zip(cycle(llista1), cycle(llista2)):
    print(x, y)
    wait(0.5)

# %% cycle1
for x, y in zip(cycle([36, 43, 39]), cycle([60, 63, 67, 0, 71, 67])):
    oboe(x,0.7, 0.5, block=False)
    oboe(y,0.7, 0.5)

# %% cycle2
pitches = [69, 72, 71, 64, 66, 0, 62]
durs = [1.0, 0.5, 0.75, 0.25, 1.0]

for pitch, dur in zip( cycle(pitches), cycle(durs)):
     oboe(pitch, 0.7, dur)
   
