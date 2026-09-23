from pyChanga import *

tempo(90)

rhand = [0, 78, 81, 79, 78, 73, 71, 73, 74, 69, 0, 0] 

# Write a script that play the first mesures of Gymnopedies.
# - Think how to play simultaneously left hand and right hand
# - Use zip to get items from lhand and rhand lists simultaneously
# - Chords are lists inside lhand list.
# - items 'None' are wait()


for i in rhand:
    piano(i,1,1)