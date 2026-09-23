# Adapted from curs/5 list operations/1 EXERCISE remix with slices.py
# Run the named sections independently; re-run a section to replace its part.
# %% setup
from pyChanga import *

tempo(80)

def loop1():
    while True:
        drumSeq('k-k-')

beatString = '-ssc-t-tt-h-h-s-'

a = beatString[0:4]

b = beatString[12:16]

d = beatString[8:11]

e = beatString[0:3]

f = beatString[5]

# %% loop1
loop1()

# %% main_voice
drumSeq(e * 8)

drumSeq(a * 2 + e)

drumSeq(b + a + (d + e) * 4, 0.125)

drumSeq(a + e + f * 7 + 'c')
