# %% setup
from pyChanga import *
from random import choice

# %% drum sequence
# k kick, s snare, t tom, h hihat, c cymbal, o open hihat, m muted hihat, - silence
while True:
    drumSeq("k-ks-kks-k", 0.3)

# %% drums2
while True:
    drumSeq("mm-omm-ommmommmomtmomc-ommmommmomhmo", 0.3)

# %% chiptune 
beatString = "kkkksskksmk-ks-k-ks-ccckssocckhtkkshhocs"
# k kick, s snare, t tom, h hihat, c cymbal, o open hihat, m muted hihat, - silence

# slices of the full pattern
a = beatString[0:9]
b = beatString[10:19]
d = beatString[20:29]
e = beatString[30:39]
    
lista = [a,b,d,e]

while True:
    slice = choice(lista) # select a random slice
    chipSeq(slice, 0.3)



# %% main
notas_dict = {"5": 52,"6": 53,"7": 55,"8": 56,"9": 58,"n": 59,"c": 60,"d": 62,"e": 63,"f": 65,"g": 67,"a": 68,"b": 71,"+": 72,"-": 74,"*": 75, "0":0}            

def synthSeq(seq):
    nota = 0    
    for num,i in enumerate(seq): # he hecho una codificación propia, asignándole cada nota al string que he querido
        nota = notas_dict[i]
        if(nota==0):
            wait(0.25)
        if num == 0 or num % 10 == 0:
            bass(nota, 0.7, 1.5, block=False)
            epiano(nota, 0.6, 0.15)
        else:
            epiano(nota, 0.6, 0.15)

while True:
    synthSeq("cdeg+*cdee"*4)
    synthSeq("9deg+*9dee"*4)
    synthSeq("8deg+*8dee"*4)
    synthSeq("68cfa*68cf"*4)
    synthSeq("57cdeg57cd"*4)
    synthSeq("7ceg+*7ceg"*4)
    synthSeq("7ndfga7ndf"*4)

