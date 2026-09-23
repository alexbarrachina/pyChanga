# %% setup
from pyChanga import *

# A function describes a gesture. Named parts provide concurrency.
def arpeggio(root, volume):
    for interval in [0, 4, 7, 12]:
        piano(root + interval, volume, 0.25)

# %% upper_voice
while True:
    arpeggio(60, 0.5)
    arpeggio(65, 0.5)

# %% lower_voice
while True:
    bass(36, 0.6, 2)
    bass(41, 0.6, 2)

# %% counterpoint
while True:
    wait(0.5)
    clarinet(79, 0.35, 0.5)
    clarinet(77, 0.35, 1)
