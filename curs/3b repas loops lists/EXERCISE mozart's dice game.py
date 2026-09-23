# This program generates an excerpt of Mozart's "Musikalisches
# Wurfelspiel" (aka Mozart's Dice Game). It demonstrates how
# randomness may be sieved (harnessed) to produce aesthetic results.
#
# The original has 16 measures with 11 choices per measure.
# This excerpt is a simplified form, with 4 mesures and 2-3 choices per mesure.
# Musical material is selected from this matrix:
#
# I         II      III        IV
# mesI-1 mesII-1 mesIII-1 mesIV-1
# mesI-2 mesII-2 mesIII-2 mesIV-2
# mesI-3
#
# Columns represent alternatives for a measure. The composer throws
# dice to select an alternative (choice) from first column.
# Then, connects it with the choice from second column, and so on.

from pyChanga import *
from random import choice, randint

mesI_1 =   [[48, 76], 72, 67]
mesI_2 =   [[48, 52, 67], 72, 76]
mesI_3 =   [[48, 52, 72], 71, 72, 76, 67, 72]
mesII_1 =  mesI_3
mesII_2 =  [[52, 55, 72], 67, 72, 76, 67, 72]
mesIII_1 = [[47, 55, 74], 76, 77, 74, [43, 72], 71]
mesIII_2 = [[43, 71], 74, 71, 69, 67]
mesIV_1 =  [[72, 67, 64, 60, 48]]
mesIV_2 =  [[48, 72, 67, 64, 60], [43, 71], [48, 64, 72]]

# - Write 4 FOR LOOPS that play the notes in a mesure. Choose the mesure between the 2-3 possible material of that mesure
# example: mesure I should be mesI-1, mesI-2 or mesI-3
# - The durations in a mesure should be random between 0.25 and 0.5

