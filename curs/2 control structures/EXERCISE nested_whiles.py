from pyChanga import *

drums(36, 1.0, 0.25)
drums(42, 1.0, 0.25)
drums(38, 1.0, 0.25)
drums(42, 1.0, 0.25)

drums(49, 1.0, 0.5)
wait(0.25)
drums(45, 1.0, 0.25)    # 71 or 73 or 75 or 77



# built a rhythmic loop with
#    - pathern A, 2 times
#    - pathern B, 1 time (changing on every loop between 71, 73, 75, 77)

# execute the loop forever (you will need 3 while conditions)

# kick 36, snare 38, hi-hat 42, cymbal 49, tom 45.