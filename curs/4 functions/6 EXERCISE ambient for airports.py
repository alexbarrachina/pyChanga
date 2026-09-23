'''
Write a script that emulate the piece Music for Airports (2/1). Brian Eno originally used tape recorders with a magnetic tape loop on which a note had been recorded. 

Implement a function that:
 - Wait for a random time, selected from the list of durations.
 - Play a note with pitch and duration selected from the pitch and duration sites.
 - Use 'choice()' to random select from a list
 - Process both sentences in loop, forever

Use 'fork()' to execute 6 of these funcitons simultaneously.

'''
# %% setup
from pyChanga import *
from random import choice

# Pitches and durations to choose randomly
pitches = [36, 48, 51, 55, 58, 60, 63, 67, 68, 70, 72, 75]
durs = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5]

# %% synth1
# Example of synth path note. The volume uses an envelope, the same for every note
synth( 60, [0.2, 0.8, 0.3], 7.5)
    
    



