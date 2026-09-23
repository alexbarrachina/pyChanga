import pygame

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

PINK = (255, 0, 255)
BLACK = (0,0,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

image = pygame.image.load("ufo.png")
x = 100
y = 100

while True:

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                x += -5
            if event.key == pygame.K_RIGHT:
                x += 5

    screen.fill(BLACK)   
    screen.blit(image, (x,y) )
    pygame.display.update()
    


