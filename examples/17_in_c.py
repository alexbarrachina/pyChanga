from pyChanga import *
from random import randint

# start on "immediately" if you want more complex rhythms (deactivate beat/bar quantization)

# Read notes from a text file and return a list of note lists and a list of duration lists.
def read_sequences(filename):
    with open(filename, encoding="utf-8") as input_file:
        rows = [line.strip() for line in input_file if line.strip()]

    middle = len(rows) // 2
    note_rows = rows[:middle]
    duration_rows = rows[middle:]

    note_sequences = [
        [int(value) for value in row.split(":")]
        for row in note_rows
    ]
    duration_sequences = [
        [float(value) for value in row.split(":")]
        for row in duration_rows
    ]
    return note_sequences, duration_sequences

patts, durs = read_sequences("in_c.txt")

def instrument(inst,note,dur):
    match inst:
        case 1:
            piano(note,1., dur)
        case 2:
            rhodes(note,1., dur)
        case 3:
            clarinet(note,1., dur)
        case 4:
            organ(note,1., dur)
        case 5:
            ether(note,1., dur)
        case 6:
            oboe(note,1., dur)
        case 7:
            bass(note,1., dur)

step = 0

def sequence():
    octave = randint(1,2)
    nloops = randint(1,40)
    inst = randint(1,7)
    for i in range(nloops):
        for note,dur in zip(patts[step],durs[step]):
                instrument(inst, note-12+(12*octave), dur) 

while True:
    if(randint(1,7)==1):
        run(sequence)
    if(randint(1,30)==1):
        step=step+1
        print("seq",step)
    wait(randint(1,10)/10.)

