
# Plays a few microtonal chords

from pyChanga import *

set_synth()

# playing microtonal pitches is as simple as using floating-point values for pitch
synth([62.7, 71.3], 1.0, 4)
synth([65.2, 70.9], 1.0, 4)
synth([71.5, 74.2, 73.7], 1.0, 4)

