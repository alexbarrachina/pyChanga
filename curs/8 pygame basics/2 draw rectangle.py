import pygame

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

PINK = (255, 0, 255)
BLACK = (0,0,0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

rect_1 = pygame.Rect(400, 100, 100, 100)

print(rect_1)
i = 0

while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                i = i - 10
            if event.key == pygame.K_RIGHT:
                i = i + 10
            
    rect_1.x = 110 + i
   
    screen.fill(BLACK)
    pygame.draw.rect(screen, PINK, rect_1)
    #pygame.draw.circl(screen, PINK, pos, 20)
    pygame.display.update()
    


