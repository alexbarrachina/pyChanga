from pyChanga import *
tempo(60)

pitches = [45,52,59,57,60,43,52,59,41,50,59,57,60,40,57,56,62]
vels = [0.9,0.6,0.8,0.5,0.8,0.9,0.6,0.8,0.9,0.6,0.8,0.5,0.8,0.9,0.6,0.6,0.8]

while True:
    for p, v in zip(pitches, vels):
        guitar(p, v, 0.25)
    

