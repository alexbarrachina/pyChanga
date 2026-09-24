from pyChanga import *
from random import *

tempo(60)

bassline = [30,37,40, 42, 40, 37, 35, 37]
menor = [66,68,69,71,73,74,76,78]

def bajo():
    for i in bassline:
        bass(i,1,0.5)
        
def synte():
    organ(choice(menor),1,0.25)
    
def saxo():
    slice = menor[0: randint(1,7):randint(1,3)]
    for i in slice:
        ether(i,0.7,0.25)
    
def bateria1():
    drumSeq("kkskkkskkkskkksk")
    
    
text = "Tirale"

def bateria2():
    for i, lletra in enumerate(text):
        hit = ord(lletra)-29
        drums(hit,1,0.5)
            
while True:
    run(synte)
    run(bateria1)
    run(bateria2)
    run(saxo)
    bajo()

    
