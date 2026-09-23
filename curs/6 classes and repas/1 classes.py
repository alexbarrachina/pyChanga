
class Car:
    def __init__(self, color, car_type):
        self.color = color
        self.type = car_type
        self.oil = 100
        self.pos = 0
        self.vel = 0
        
    def move(self):
        self.pos = self.pos + self.vel
    
    def setVel(self, vel):
        self.vel = vel
     
    def getVel(self):
        return self.vel
        
    def getPos(self):
        return self.pos

    def setColor(self, newColor):
        self.color = newColor

car1 = Car("red", "beetle")
car2 = Car("blue", "audi")

car1.color = "pink"

print( car1.color ) 


car1.setVel(10)

for i in range(10):
    car1.move()

car1.setVel(-3)
car1.move()

print( car1.getPos())
print( car2.getPos())

print (car1.vel)
