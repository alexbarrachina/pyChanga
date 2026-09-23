from pyChanga import *

set_vibra()
set_organ()

f = open("sequence.txt")
big_str = f.read()

melody = big_str.split(",") 

print(melody)

melo_llist = []

for ele in melody:
    melo_int = int(ele)
    melo_llist.append(melo_int)    

melody = melo_llist
print(melo_llist)
'''
melody = list(map(int, melody)) # convert strings to ints
'''


print('melody: ', melody)

i = 0
while True:
    for notew in melody:
        note = int(notew)
        if i%10==0:
            organ(melody[i%len(melody)]-24, 0.7, 3.0, block=False) 
        if i%3==0:
            vibra(melody[i%len(melody)]-12, 0.5, 0.6, block=False) 
        vibra(note, 1, 0.2)
        i += 1
   
  