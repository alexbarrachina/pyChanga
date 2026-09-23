# %% setup
from pyChanga import *
from random import choice

pitches = [48, 51, 55, 58, 60, 63, 67, 68, 70, 72, 75]
durations = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5]

def gesture():
    wait(choice(durations))
    synth(choice(pitches), 0.22, choice(durations))

# Run any combination of these parts. Each has its own random choices.
# %% voice_1
while True:
    gesture()

# %% voice_2
while True:
    gesture()

# %% voice_3
while True:
    gesture()

# %% voice_4
while True:
    gesture()

# %% voice_5
while True:
    gesture()

# %% voice_6
while True:
    gesture()
