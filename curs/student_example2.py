from pyChanga import *
from random import choice, randint

tempo(60)


def drum_beat():
    ritmo = "k-k-k-k-" #k---k--- #k--k--k-
    while True:
        drumSeq(ritmo)

def tribale():
    while True:
        wait(0.75)
        tono = choice([40,45])
        organ(tono, 1, 0.1, block=False)
        
def basso():
    note = [36,36,39,36]
    state = False
    while True:
        wait(0.25)
        if state:
            for i, p in enumerate(note):
                if i % 4 == 0:
                    bass(p+12, 1, 0.25)
            else:
                for i in note:
                    bass(p+12, 1, 0.25)
        if randint(0,4)==0:
            state = not state
            
def accento():
    while True:
        wait(0.5)
        if choice([0,0,0,1]) == 1:
            for n in [72, 75, 74, 72]:
              marimba(n, 0.5, 0.125)
        else:
              marimba(choice([60,63,67]), 0.5, 0.5)

def shaker():
    while True:
        wait(0.25)
        if choice([1,1,1,0]) == 1:
            arp(60, 1, 0.05, block=False)
            wait(0.25)
              
run(tribale)
run(basso)
run(accento)
run(shaker)
run(drum_beat)

