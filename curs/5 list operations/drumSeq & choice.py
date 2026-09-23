# Adapted from curs/5 list operations/drumSeq & choice.py
# Run the named sections independently; re-run a section to replace its part.
# %% setup
from pyChanga import *

from random import choice

dur_list = [0.0625, 0.125, 0.25, 0.5]

def ritme1():
    while True:
        x = choice(dur_list)
        drumSeq('kk-kk-kk-', x)

def ritme2():
    while True:
        x = choice(dur_list)
        drumSeq('-t-ss-t-s', x)

def ritme3():
    while True:
        x = choice(dur_list)
        drumSeq('h-h-cc-h', x)

# %% ritme1
ritme1()

# %% ritme2
ritme2()

# %% main_voice
ritme3()
