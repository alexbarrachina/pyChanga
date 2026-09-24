from musica import *

set_drums()
set_synth()
set_marimba()
set_cbass()

harmony = [[62,66,69,73], [65, 69, 72, 76], [60, 64, 67, 71], [63, 67, 70, 74]] #array de acordes del piano

bassmelody = [38, 0, 36, 0] #línea del bajo

x = 73 # parámentros para la melodía de la marimba
y= 0

drums (61,1, 0.2)
drums (61,1, 0.05)
drums (61,1, 0.15)
drums (60,1, 0.2)
drums (61,1, 0.05)
drums (61,1,0.15 )
drums (60,1,0.2)      #break de batería del inicio


while True:
    for i, pitch in enumerate(harmony):
               
        if y % 2 == 0:
            cbass (bassmelody [i], 2, 4, block=False)  #la nota del bajo solo sonará cada dos ciclos del loop
            
        synth (harmony [i], 0.5, 3.2, block = False)
        marimba (x,1,0.4, block = False)
        drums (60, 1, 0.4, block = False)
        drums (63, 1, 0.4)
        marimba (x-4,1,0.4, block = False)
        drums (63, 1, 0.2)
        drums (60, 1, 0.2)
        marimba (x-7,1,0.4, block = False)
        drums (61, 1, 0.4, block = False)
        drums (63, 1, 0.4)
        marimba (x-11,1,0.4, block = False)            
        drums (63, 1, 0.4, block = False)
        drums (63, 1, 0.4)
        marimba (x-12,1,0.4, block = False)           
        drums (63, 1, 0.4)
        marimba (x-11,1,0.4, block = False)                      
        drums (63, 1, 0.2)
        drums (60, 1, 0.2)
        marimba (x-7,1,0.4, block = False)                                
        drums (61, 1, 0.4, block = False)
        drums (63, 1, 0.4)
        marimba (x-4,1,0.4, block = False)                                                   
        drums (60, 1, 0.4, block = False)
        drums (63, 1, 0.4)
            
        y=y+1   #para la melodía de la marimba, como se ha visto antes, he asignado dos valores: y, x. El primero sirve para marcar las vueltas que llevamos del loop (que se reinicia al y==4) y el segundo sirve para corregir la altura de la melodía dependiendo del acorde que esté tocando el sintetizador.
       
        if y  == 1:
            x=76

        if y == 2:
            x=71
            
        if y == 3:
            x=69
            
        if y == 4:
            y = 0
            x = 73
            
        print (x)
        print (y) 
                
            
        
   
      