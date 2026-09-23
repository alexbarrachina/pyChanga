from pyChanga import *

tempo(120)

''''
The Fibonacci sequence is a series of numbers where each number
is the sum of the two preceding ones, typically starting.
The sequence begins: 0,1,1,2,3,5,8,13,21,34,.... 
It is characterized by the formula Fn = Fn-1 + Fn-2
 and is renowned for its appearance in nature, art.
''' 

a = 8
b = 7
while True:
    print(a, end=", ")
    clarinet(55 + a, 0.7, 0.25)
    b = (a + b) % 29 
    a = b
    
    