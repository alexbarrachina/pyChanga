from pyChanga import *

# It's a function that interprets a drum beat coded in a string (in a word)
'''def drumSeq(seq):
    hit = 0    
    for i in seq:
        if(i=='k'):
            hit = 36 # kick
        if(i=='s'):
            hit = 38 # snare
        if(i=='h'):
            hit = 42 # hihat
        if(i=='c'):
            hit = 49 # cymbal
        if(i=='t'):
            hit = 45 # tom
        if(i=='-'):
            hit = 0 # silence
            
        if(hit==0):
            wait(0.25)
        else:
            drums(hit, 0.7, 0.25)
 '''           
# Experiment a little bit by modifiyng the pattern.
# k kick
# s snare
# h hihat
# c cymbal
# t tom
# - silence


while True:
    drumSeq("ksc-hhhs")

'''
Step1:
Create an interesting polyrhythm using 2 functions that play drumSeq() in an infinite loop.
In order to reproduce both sequences you will need to fork one of the sequences.

Step2:
Add an extra argument to the function drumSeq() to change the duration
Experiment a little bit, modifying patterns and durations and create a good pattern.
'''

# Your code here



