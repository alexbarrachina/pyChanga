import pygame

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

PINK = (255, 0, 255)
BLACK = (0,0,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

rect_1 = pygame.Rect(200, 100, 150, 100)
print(rect_1)

while True:

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                rect_1.x += -5
            if event.key == pygame.K_RIGHT:
                rect_1.x += 5

    #mousePos = pygame.mouse.get_pos()
    #print(mousePos)
    #rect_1.x = mousePos[0] - 75
    #rect_1.y = mousePos[1] - 50
     
    # filling the screen with black ro 'refresh' the screen
    #screen.fill(BLACK)   
    pygame.draw.rect(screen, PINK, rect_1)
    pygame.display.update()
    
# https://www.pygame.org/docs/ref/mouse.html

