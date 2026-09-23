import pygame
from random import randint

pygame.init()

BLACK = (0,0,0)
BLUE = (0,0,255)

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 300

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

wall_positions =  [(0,1), (0,2), (0,3), (0,4), (1,1), (2,1), (2,3), (3,3), (4,0), (4,1), (4,2), (4,3)]
    
while True:

    for event in pygame.event.get():
            pass
    
    screen.fill(BLACK)
    for i in wall_positions:    
        pygame.draw.rect(screen, BLUE, (i[0]*10,i[1]*10,10,10))
    pygame.display.update()
    

# Write a game in which the player has to click on a rectangle.
# The rectangle randomly appears and disappears in a short period of time. If the player catches the rectangle:
# - adds 1 point
# - a sound is played
# - the rectangle disappears out of the screen