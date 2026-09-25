# %% setup
from pyChanga import *
from random import uniform

voice1 = load_sample("voice1.wav")
voice2 = load_sample("voice2.wav")

# %% playback
sampl(voice, 0.7, 1, rate=0.8) # sample, vol, duration

# %% reverse playback
sampl(voice, 0.7, 1, rate=-1.0)

# %% an arrangement of a spoken recording
positions = [0.0, 0.4, 1.2, 0.4]
for pos in positions:
    sampl(voice, 0.6, 0.25, start=pos)

# %% granulation
for i in range(100):    
    sampl( voice, 0.12, 0.08, start=uniform(0.0, 1.0), env=[0, 1, 0],block=False )
    wait(0.02)    

# %% moving micro-looper
for i in range(1000):
    pos = i/1000.    
    sampl( voice, 0.7, 0.1, start=pos, block=False )
    wait(0.1) 

# %% stutter
def stutter(sound, position, repeats):
    for i in range(repeats):
        volume = 0.8 if i == 0 else 0.4
        play_sample(sound, volume, 0.125, start=position)

stutter(voice, 0.4, 4)
stutter(voice, 1.2, 8)

