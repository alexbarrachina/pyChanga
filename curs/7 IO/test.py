from pyChanga import *
from random import randint

set_synth()
set_viola()
set_oboe()
set_drums()
set_cbass()

w=randint(1,6)
y=randint(18,24)

arp = [66-12, 70-12, 73-12, 77-12, 66, 70, 73, 77, 66+12, 70+12, 73+12, 77+12, 66-12, 70-12, 73-12, 77-12, 66, 70, 73, 77, 66+12, 70+12, 73+12, 77+12]

def viola_solo1():
    
    viola(73,0.75,0.5)
    viola(70,0.75,0.5)
    viola(65,0.75,0.25)
    viola(66,0.75,0.25)
    viola(63,0.75,0.25)
    viola(65,0.75,0.5)
    viola(61,0.75,0.25)
    viola(63,0.75,0.25)
    viola(58,0.75,0.25)


def synth_part():
    seqüència_synth = arp[w:y:3]
    for i in seqüència_synth:
        synth(i,0.5,1)

def oboe_part():
    seqüència_oboe = arp[w:y:2]
    for o in seqüència_oboe:
        oboe(o,0.35,0.5)

def cbass_part():
    seqüència_cbass = arp[0:6:4]
    for u in seqüència_cbass:
        cbass(u-12,1.2,2)
        
def bg_synth():
    synth(arp[4],0.8,3, block = False)
    synth (68,0.3,3, block = False)
    synth(arp[5],0.2,3, block = False)
    synth (arp[6],0.2,3, block = False)
    synth (arp[7],0.2,3, block = False)

y=0

while y<28:
    
  while y<3:
      viola_solo1()
     
      print(y)
      
      y=y+1
      
      
  while 3<=y<7:
      viola_solo1()
      fork(cbass_part)
     
      print(y)
     
      y=y+1
     
     
      
  while 7<=y<=11:
     viola_solo1()
     fork(cbass_part)
     fork(oboe_part)
     
     print(y)
     
     y=y+1
    
     
  
  while 12<=y<=27:
      fork(viola_solo1)
      fork(synth_part)
      fork(oboe_part)
      fork(cbass_part)
      fork(bg_synth)
      drumSeq("kkskkkskkksk",0.25)
      
      print(y)
       
      y=y+1