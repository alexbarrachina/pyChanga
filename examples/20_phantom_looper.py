from pyChanga import *

voice1, _ = load_sample("samples/rare41.wav")
voice2, _ = load_sample("samples/rare54.wav")
voice3, _ = load_sample("samples/rare62.wav")

def phantom(voice, vol=0.7, dur=0.2, init_pos=0):
    for i in range(1000):
        pos = i/1000  # moving loop. Every iteration adavances a little bit the position
        sampl( voice, vol, dur, start=pos+init_pos, block=False )
        wait(dur) 

phantA = run(phantom, voice1)
wait(30)
phantB = run(phantom, voice2, vol=0.3, dur=0.3)
wait(50)
stop(phantA)
stop(phantB)

phant1 = run(phantom, voice3)
phant2 = run(phantom, voice3, dur=0.3)
phant3 = run(phantom, voice3, dur=0.4)

wait(30)

stop(phant1)
stop(phant2)
stop(phant3)

voice4, _ = load_sample("samples/sample1.wav")
run(phantom, voice4, dur=0.6, init_pos=0.5)
run(phantom, voice4, dur=0.12, init_pos=0.5)
run(phantom, voice4, dur=0.8, init_pos=0.5)
