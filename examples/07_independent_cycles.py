# %% setup
from pyChanga import *
from itertools import cycle

# Unequal list lengths create changing combinations on a single global tempo.
# A None value represents a rest, expressed explicitly with wait().

# %% oboe_cycle
pitches = [69, 72, 71, 64, 66, None, 62]
durations = [1, 0.5, 0.75, 0.25, 1]
volumes = [0.35, 0.5, 0.25]
for pitch, volume, duration in zip(cycle(pitches), cycle(volumes), cycle(durations)):
    if pitch is None:
        wait(duration)
    else:
        oboe(pitch, volume, duration)

# %% clarinet_cycle
pitches = [76, 78, 77, 79, None]
durations = [2, 0.5, 1]
volumes = [0.25, 0.4, 0.3, 0.5]
for pitch, volume, duration in zip(cycle(pitches), cycle(volumes), cycle(durations)):
    if pitch is None:
        wait(duration)
    else:
        clarinet(pitch, volume, duration)
