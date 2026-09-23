import pygame

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

PINK = (255, 0, 255)
BLUE = (0,0,255)
RED = (255,0,0)
BLACK = (0,0,0)
color = PINK

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

rect_1 = pygame.Rect(200, 100, 60, 60)
rect_2 = pygame.Rect(200, 100, 30, 30)

while True:

    for event in pygame.event.get():
       pass

    # move the rect_1 with the mouse
    rect_1.center = pygame.mouse.get_pos()

    # check collision
    if rect_1.colliderect(rect_2):
        color = RED
    else:
        color = PINK
    
    #refresh screen
    screen.fill(BLACK)   

    # draw both rectangles
    pygame.draw.rect(screen, BLUE, rect_2)
    pygame.draw.rect(screen, color, rect_1)
    pygame.display.update()
    

