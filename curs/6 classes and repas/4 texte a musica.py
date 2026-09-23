from pyChanga import *

text = "aixo es una composicio feta amb notes asciiiiiiiiiiii"

for char in text:
    if char == " ":  # space is a silence
        wait(0.2)
    else:
        pitch = ord(char) - 48
        piano(pitch , 0.5, 0.06)   # ord() converts letters to numbers


# try repeating letters

