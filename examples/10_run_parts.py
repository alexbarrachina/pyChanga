from pyChanga import *

# Every run() call starts another independent instance of the function.
def arpeggio(root):
    while True:
        for interval in [0, 4, 7, 12]:
            piano(root + interval, 0.5, 0.25)

def bassline():
    while True:
        cbass(48, 0.8, 2)
        cbass(53, 0.8, 2)

run(arpeggio, 60)  # arpeggio1
run(bassline)      # bassline1, in sync with arppegio1
wait(0.125)
run(arpeggio, 65)  # arpeggio2, alongside arpeggio1
wait(0.125)
run(arpeggio, 67)  # arpeggio2, alongside arpeggio1
wait(0.125)
run(arpeggio, 60)  # arpeggio1
