import pygame
from random import randint

pygame.init()

BLACK = (0,0,0)
BLUE = (0,0,255)

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

rect_2 = pygame.Rect(-700, -700, 150, 150) # out of the screen

while True:

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONUP:
            pass
    
    rect_2.x = 100
    
    screen.fill(BLACK)
    pygame.draw.rect(screen, BLUE, rect_2)
    pygame.display.update()
    

# Write a game in which the player has to click on a rectangle.
# The rectangle randomly appears and disappears in a short period of time. If the player catches the rectangle:
# - adds 1 point
# - a sound is played
# - the rectangle disappears out of the screen