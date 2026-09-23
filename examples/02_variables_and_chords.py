# %% setup
from pyChanga import *

root = 60
volume = 0.6

# %% chords
# Finite code plays once. Select this part and run it again to hear your edits.
for offset in [0, -3, -5, -2]:
    piano([root + offset, root + offset + 4, root + offset + 7], volume, 2)

# %% overlap
# A nonblocking note lets this same part begin another gesture immediately.
piano(root - 12, 0.5, 4, block=False)
for note in major_scale(root)[:8]:
    piano(note, 0.4, 0.5)
