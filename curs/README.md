# Lessons for pyChangaIDE

This is the working copy of the course for `pyChangaIDE`. Music imports use
`from pyChanga import *`. The migrated concurrency lessons use named musical parts
instead of `fork()`. Call `run(function)` from a musical section to start an
independent numbered instance; repeated calls to the same function start more
instances. Setup executes afresh for every named section. The default tempo is 60 BPM;
lessons with an explicit `tempo(...)` keep their chosen tempo.

`4 functions/4 functions and parts.py` introduces the new concurrency model.
The migrated list-operation lessons keep their original musical algorithms.
`drumSeq & choice.py` uses the library's `pyChanga.sf2` drum sequence function.
`chipSeq()` uses the separate chip kit with the same rhythm symbols.

The bundled `examples` directory also provides complete lessons for variables,
chords, conditions, drums, functions, scales, independent cycles, and six ambient
voices. `06_ambient_for_airports.py` adapts the original exercise to fixed volume;
envelopes are outside the first release. `07_independent_cycles.py` replaces the
original cycle/fork lesson and expresses rests explicitly with `wait()`.

Independent-tempo piano phasing, microtonality, MIDI/OSC, keyboard/mouse input,
and pygame remain in the original course for a later release. Other core lessons
can run as one part if their notes use whole MIDI pitches and volume uses a number
from 0 to 1 and instruments from the current [preset list](../README.md#music-api).
For the `pyChanga.sf2` drum kit, use kick 36, snare 37, hi-hat 48, cymbal 65,
tom 55, open hi-hat 68, and muted hi-hat 50, or use `drumSeq()`.
MIDI pitch 0 is a real note, not a rest.

Install the canonical package from the project root with
`python3 -m pip install ./pyChanga_package`. The small package bridge in this
course folder points to that same implementation.
