from pyChanga import *

scale = pentatonic_scale(60)
set_bassoon()

countdown = 0.8
last_position = (0, 0)

def mouse_listener(x, y):
    global countdown, last_position
    dx, dy = x - last_position[0], y - last_position[1]
    last_position = (x, y)
    countdown -= (dx ** 2 + dy ** 2) ** 0.5
    if countdown < 0:
        bassoon(scale[(34 + 40 * (1 - y))], x, 0.1, block=False)
        countdown = 0.1
    
register_mouse_listener(mouse_listener)

while True:
    wait(0.06)