import pygame

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900

PINK = (255, 0, 255)
RED = (255,0,0) # R,G,B
BLACK = (0,0,0)
BLUE = (0,0,255)

color = BLUE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

rect_1 = pygame.Rect(0, 0, 50, 50)

isDragging = False

p = (300,300)

while True:

    pygame.event.get()
        
    p = pygame.mouse.get_pos()
    
    if rect_1.collidepoint(p):
        print("Tocado")
        
    rect_1.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
    
    screen.fill(BLACK)   
        
    pygame.draw.rect(screen, RED, rect_1)
    pygame.display.update()


# ok, but the rectangle should move while the mouse is dragging.



