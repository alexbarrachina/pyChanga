# Copyright (C) 2026 Alex Barrachina
# SPDX-License-Identifier: GPL-3.0-only

from pyChanga import *
from random import choice, randint

pitches = [48, 51, 55, 58, 60, 63, 67, 68, 70, 72, 75]

def reel_head():
    while True:
        wait(randint(1,100)/10)
        strings(choice(pitches), 0.7, randint(1,100)/5)

# Run 6 instances of reel_head() function
for i in range(6):
    run(reel_head)
    wait(randint(1,100)/10)
