from pyChanga import *
tempo(70)
x = [1,2,3,4,5,6,7,8,9,10,11,12]

#tempo(145)
                      
# A tipical training arpeggio, slicing from a scale
scale = [48, 50, 52, 53, 55, 57, 59,
         48+12, 50+12, 52+12, 53+12, 55+12, 57+12, 59+12,
         48+24, 50+24, 52+24, 53+24, 55+24, 57+24, 59+24, 60+24]

i=0
while i<19:
    slice = scale[0+i:8+i:2]
    print(slice)
    for pitch in slice:
        piano(pitch+12, 0.7, 0.1)
    i = i+1
 



 
 
 
 
 
# try [i:i+8:2]