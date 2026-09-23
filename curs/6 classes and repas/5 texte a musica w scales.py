from pyChanga import *

major = major_scale(48)

text = "aquest algoritme fa musica a partir d una frase"

for char in text:
    if char == " ":  # space is a silence
        wait(0.2)
    else:
        pitch = major[ord(char) - 97]
        piano(pitch, 0.5, 0.1)   # ord() converts letters to numbers


# try repeating letters
print(major)