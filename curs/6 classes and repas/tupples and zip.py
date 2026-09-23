from pyChanga import *

# option1: melodies as lists of tupples

arp1 = [(45,0.9), (52,0.6), (59,0.8), (57,0.5), (60,0.8)]
arp2 = [(43,0.9), (52,0.6), (59,0.8)]
arp3 = [(41,0.9), (50,0.6), (59,0.8), (57,0.5), (60,0.8)]
arp4 = [(40,0.9), (57,0.6), (56,0.6), (62,0.8)]


def arpeggio(llista):
    for p, v in llista:
        guitar(p, v, 0.25)
    wait(2.0)

# lists as function parameters
while True:
    arpeggio(arp1)
    arpeggio(arp2)
    arpeggio(arp3)
    arpeggio(arp4)

# option2: pitch and volume lists joined in a tupple of lists

def arpeggio(pitches, volumes):
    for p, v in zip(pitches, volumes):
        guitar(p, v, 0.25)
    wait(2.0)
    
