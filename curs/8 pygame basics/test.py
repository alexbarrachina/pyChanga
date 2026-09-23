import pygame
from random import *

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
PINK = (255, 0, 255)
BLACK = (0,0,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
rect_1 = pygame.Rect(200, 100, 150, 100)

punts = 0

print(rect_1)

while True:
    i= randint(0,200000)
    if i==0:
        rect_1.x = randint(0,SCREEN_WIDTH)
        rect_1.y = randint(0,SCREEN_HEIGHT)
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.fill(BLACK)
        pygame.draw.rect(screen, PINK, rect_1)
        pygame.display.update()
            
    for event in pygame.event.get():
        mousePos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if mousePos [0] > rect_1.x and mousePos [0] < rect_1.x+rect_1.w and mousePos [1] > rect_1.y and mousePos [1] < rect_1.y+rect_1.h:
                punts += 1
                print(punts)
                bip = pygame.mixer.Sound("bip.wav")
                pygame.mixer.Sound.play(bip)
                rect_1.x = -700
                rect_1.y = -700
                screen.fill(BLACK)
                pygame.draw.rect(screen, PINK, rect_1)
                pygame.display.update()
                
            
            

    

        


# Write a game in which the player has to click on a rectangle.
# The rectangle randomly appears and disappears in a short period of time. If the player catches the rectangle:
# - adds 1 point
# - a sound is played
# - the rectangle disappears out of the screen