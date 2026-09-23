from pyChanga import *

text = "aquest algoritme fa musica a partir d una frase"
words = text.split(' ')
print(words)

base_loop = words[0] # 'aquest'
base_loop1 = words[1]       # 'algoritme'   try different words
base_len = len(base_loop) # 6
base_len1 = len(base_loop1) # 


while True:
    for i, char in enumerate(text):
        
        
        base_hit = ord(base_loop[i % base_len]) - 49   # ord() converts letters to numbers
        drums(base_hit, 0.5, 0.2, block=False)   

        base_hit1 = ord(base_loop1[i % base_len1]) - 49   # ord() converts letters to numbers
        drums(base_hit1, 0.5, 0.2, block=False)

        
        if char == " ":  # space is a silence
            wait(0.2)
        else:
            pitch = ord(char) - 49
            drums(pitch, 0.5, 0.2)   # ord() converts letters to numbers

