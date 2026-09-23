from pyChanga import *

tempo(80)

sequence = [48, 50, 52, 53, 55, 57, 59]
    
print(sequence)

def octave_up(seqIn):
    seq = seqIn    # you need to make a .copy()
    for i in range(len(seq)):
        seq[i] =  seq[i] + 12
    return seq

x = [34,34,36]
y = octave_up(x)
z = octave_up(y)

sequence = x + y + z
print(x, y, z, sequence)

for element in sequence:
    piano(element, 0.7, 0.5)