from scamp import *
import warnings
import os

warnings.filterwarnings("ignore")

s = Session()

# tempo
def tempo(dtime):
    s.tempo = dtime

# instruments
def set_drums():
    global drums_ins
    soundfont_path = os.path.join(os.path.dirname(__file__), 'sounds', 'Emu_Planet_Phatt_Hip_Hop.sf2')
    s = Session(default_soundfont=soundfont_path)
    drums_ins = s.new_part("Kit 1")
    
def set_drums3():
    global drums_ins
    soundfont_path = os.path.join(os.path.dirname(__file__), 'sounds', 'Emu_Planet_Phatt_Hip_Hop.sf2')
    s = Session(default_soundfont=soundfont_path)
    drums_ins = s.new_part("Kit 3")

def set_piano():
    global piano_ins
    piano_ins = s.new_part("piano")

def set_clarinet():
    global clarinet_ins
    clarinet_ins = s.new_part("clarinet")
def set_oboe():
    global oboe_ins
    oboe_ins = s.new_part("oboe")
def set_violin():
    global violin_ins
    violin_ins = s.new_part("violin")
def set_cbass():
    global cbass_ins
    cbass_ins = s.new_part("cbass")
def set_viola():
    global viola_ins
    viola_ins = s.new_part("viola")
def set_sax():
    global sax_ins
    sax_ins = s.new_part("saxophone")
def set_bass():
    global bass_ins
    bass_ins = s.new_part("pitched bass")
def set_organ():
    global organ_ins
    organ_ins = s.new_part("organ")
def set_marimba():
    global marimba_ins
    marimba_ins = s.new_part("marimba")
def set_bassoon():
    global bassoon_ins
    bassoon_ins = s.new_part("bassoon")
def set_choir():
    global choir_ins
    choir_ins = s.new_part("choir aah")
def set_cello():
    global cello_ins
    cello_ins = s.new_part("cello")
def set_synth():
    global synth_ins
    synth_ins = s.new_part("synth str")
def set_vibra():
    global vibra_ins
    vibra_ins = s.new_part("vibraphone")
def set_guitar():
    global guitar_ins
    guitar_ins = s.new_part("guitar")

# players
def piano(note, vol, dur, block=True):
    if type(note) is list:
        piano_ins.play_chord(note, vol, dur, blocking=block)
    else:
        piano_ins.play_note(note, vol, dur, blocking=block)

def clarinet(note, vol, dur, block=True):
    if type(note) is list:
        clarinet_ins.play_chord(note, vol, dur, blocking=block)
    else:
        clarinet_ins.play_note(note, vol, dur, blocking=block)
        
def oboe(note, vol, dur, block=True):
    if type(note) is list:
        oboe_ins.play_chord(note, vol, dur, blocking=block)
    else:
        oboe_ins.play_note(note, vol, dur, blocking=block)

def violin(note, vol, dur, block=True):
    if type(note) is list:
        violin_ins.play_chord(note, vol, dur, blocking=block)
    else:
        violin_ins.play_note(note, vol, dur, blocking=block)
        
def cbass(note, vol, dur, block=True):
    if type(note) is list:
        cbass_ins.play_chord(note, vol, dur, blocking=block)
    else:
        cbass_ins.play_note(note, vol, dur, blocking=block)
        
def drums(note, vol, dur, block=True):
    if type(note) is list:
        drums_ins.play_chord(note, vol, dur, blocking=block)
    else:
        drums_ins.play_note(note, vol, dur, blocking=block)

def viola(note, vol, dur, block=True):
    if type(note) is list:
        viola_ins.play_chord(note, vol, dur, blocking=block)
    else:
        viola_ins.play_note(note, vol, dur, blocking=block)
      
def sax(note, vol, dur, block=True):
    if type(note) is list:
        sax_ins.play_chord(note, vol, dur, blocking=block)
    else:
        sax_ins.play_note(note, vol, dur, blocking=block)
        
def bass(note, vol, dur, block=True):
    if type(note) is list:
        bass_ins.play_chord(note, vol, dur, blocking=block)
    else:
        bass_ins.play_note(note, vol, dur, blocking=block)

def organ(note, vol, dur, block=True):
    if type(note) is list:
        organ_ins.play_chord(note, vol, dur, blocking=block)
    else:
        organ_ins.play_note(note, vol, dur, blocking=block)

def marimba(note, vol, dur, block=True):
    if type(note) is list:
        marimba_ins.play_chord(note, vol, dur, blocking=block)
    else:
        marimba_ins.play_note(note, vol, dur, blocking=block)

def bassoon(note, vol, dur, block=True):
    if type(note) is list:
        bassoon_ins.play_chord(note, vol, dur, blocking=block)
    else:
        bassoon_ins.play_note(note, vol, dur, blocking=block)

def choir(note, vol, dur, block=True):
    if type(note) is list:
        choir_ins.play_chord(note, vol, dur, blocking=block)
    else:
        choir_ins.play_note(note, vol, dur, blocking=block)
 
def cello(note, vol, dur, block=True):
    if type(note) is list:
        cello_ins.play_chord(note, vol, dur, blocking=block)
    else:
        cello_ins.play_note(note, vol, dur, blocking=block)

def synth(note, vol, dur, block=True):
    if type(note) is list:
        synth_ins.play_chord(note, vol, dur, blocking=block)
    else:
        synth_ins.play_note(note, vol, dur, blocking=block)

def vibra(note, vol, dur, block=True):
    if type(note) is list:
        vibra_ins.play_chord(note, vol, dur, blocking=block)
    else:
        vibra_ins.play_note(note, vol, dur, blocking=block)

def guitar(note, vol, dur, block=True):
    if type(note) is list:
        guitar_ins.play_chord(note, vol, dur, blocking=block)
    else:
        guitar_ins.play_note(note, vol, dur, blocking=block)
   
# scales
def natural_minor_scale(num):
    from scamp_extensions.pitch import Scale
    return Scale.natural_minor(num)

def pentatonic_scale(num):
    from scamp_extensions.pitch import Scale
    return Scale.pentatonic(num)

def pentatonic_minor_scale(num):
    from scamp_extensions.pitch import Scale
    return Scale.pentatonic_minor(num)

def major_scale(num):
    from scamp_extensions.pitch import Scale
    return Scale.diatonic(num)

# I/O

def wait_forever():
    s.wait_forever()

def register_keyboard_listener(klistener):
    s.register_keyboard_listener(klistener)
    
def register_mouse_listener(func):
    s.register_mouse_listener(on_move=func, relative_coordinates=True)
    
# drum sequence
def drumSeq(seq, dur=0.25):
    hit = 0    
    for i in seq:
        if(i=='k'):
            hit = 34 # kick
        if(i=='s'):
            hit = 56 # snare
        if(i=='h'):
            hit = 52 # hihat
        if(i=='c'):
            hit = 58 # cymbal
        if(i=='t'):
            hit = 55 # tom
        if(i=='-'):
            hit = 0 # silence
            
        if(hit==0):
            wait(0.25)
        else:
            drums(hit, 0.7, dur)
            
def char2ascii(char):
    return char.isalnum()
