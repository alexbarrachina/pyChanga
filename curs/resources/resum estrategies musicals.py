# combina waits, notes i block=false
piano(67, 0.5, 0.5, block=False)    
piano(60, 0.5, 0.5)
wait(0.25)

# crear baixos amb modul
for pitch in range(60, 90, 3):    # arpegio ascending every 3 half-tones
    if pitch % 6 == 0:
        cbass(pitch-24, 1.0, 1.0, block=False)
    piano(pitch, 0.7, 0.125)

# crear arpeggios ascendents amb loops dins de loops
for i in range(60,72,3)
    for note in pattern:
        piano(note+i, 0.5, 0.1)

# crar variacions amb condicional
for pitch in range(50, 67):
    if pitch < 58:
        piano(pitch, 0.7, 0.25)
    else:
        cbass(pitch-24, 0.7, 0.25)

# usar random (randint, choice)
scale = [60, 62, 64, 65, 67, 69, 71, 72]
pitch = choice(scale)
pitch = randint(60,72)

# usar escales predefinides, major, natural_minor, pentatonic
major = major_scale(48)
pitch = major[5]

# fer servir acords
M7 = [60, 64, 67, 71]
vibra(M7, 1., 2)

# indicar la posició en la seqüència
for i, pitch in enumerate(scale):
    piano(scale[i], 0.7, 0.25)

# escollir una posició en l'escala cada 4, amb modul
for i, pitch in enumerate(scale):
    if i % 4 == 0:             
        clarinet(pitch+12, 0.9, 1.0, block=False)
    piano(pitch, 0.7, 0.25)

# encapsular gestos en funcions, amb arguments
def oboe_gesture_func(base_pitch):
    pass
oboe_gesture_func(60)
oboe_gesture_func(72)

# llençar procesos en paral·lel amb fork
fork(oboe_gesture)
paino_gesture()

# desplaçar slices sobre una escala 
scale = [...]

for i in range(19):
    slice = scale[i:i+4]
    for pitch in slice:
        piano(pitch+12, 0.7, 0.1)

# modificar el tamany d'un slice a cada volta
scale = [...]
    i = 0
    slice2 = scale[0:i%7]
    for interval in slice2:
        marimba(interval+60, 0.65, 0.25)
        i = i+ 1

# re-mesclar seqüències rítmiques amb slices
set_drums()
beatString = "-ssc-t-tt-h-h-s-"
a = beatString[0:4]
b = beatString[12:16]
drumSeq(a*8+b*2)

# usar parelles de valors per fixar pitch i durada de una melodia
llista = [(45,0.5), (52,1.0), (59,0.8), (57,0.5), (60,0.8)]
for p, d in llista:
    guitar(p, 1., d)


# loops de durades diferents. La nota evoluciona amb convinacions
# sempre diferents de p,v,d
    p = [76, 78, 77, 79, None]
    v = [2.0, 0.5, 1.0]
    d = [0.3, 0.5, 0.4, 0.6, 0.9, 0.6, 0.4]
    for pitch, volume, dur, in zip(cycle(p), cycle(v), cycle(d)):
        clarinet(pitch, volume, dur)

# usar les lletres d'una frase com a seqüencia
# separar en paraules, i loopejar cada paraula
text = "aquest algoritme fa musica a partir d una frase"
words = text.split(' ')

for char in text:
    piano(order(char)-49,1,1)