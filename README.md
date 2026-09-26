# pyChanga

pyChanga is a Python package for making music with ordinary Python code. Write
notes with functions such as `piano()`, `wait()`, and `tempo()`. Use loops and
functions to build patterns, and run independent musical parts on one shared
clock. pyChanga schedules the notes and plays them through FluidSynth and the
bundled `pyChanga.sf2` soundfont.

The package includes a command-line runner and does not require Node or Electron.
The optional [pyChanga editor](editor/README.md) provides a graphical way to work
with the same package.

## Install and play

Use Python 3.11 or newer. Install the native FluidSynth library for your system;
`pip` installs the Python package but does not install FluidSynth. From this
repository's root directory:

```sh
python3 -m pip install ./pyChanga_package
python3 -m pyChanga examples/01_simple_arpeggio.py
```

The base package has no third-party Python dependencies. Its soundfont is included in
the installation. If FluidSynth is unavailable, playback reports an error rather
than silently playing nothing. `PYCHANGA_FLUIDSYNTH` can point to a native
FluidSynth library; `PYCHANGA_NATIVE_DIR` can point to a directory containing it.

### Optional sampler

The IDE includes the Pyo sampler. Standalone FluidSynth users need no additional
installation: importing pyChanga and playing instruments never imports Pyo.
To add the sampler to a standalone environment, install the optional extra:

```sh
python3 -m pip install './pyChanga_package[sampler]'
# For a published package: python3 -m pip install 'pyChanga[sampler]'
```

Pyo contains native code. Its public PyPI 1.0.5 wheels support Python 3.11 on
macOS, Windows and Linux x64; other combinations may require a source build.
For Python 3.12 or 3.13, install the maintainer's Pyo 1.0.6 build first, then the
extra above:

```sh
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps pyo==1.0.6
```

The IDE pins platform-specific 1.0.6 wheels and checksums and includes their
native libraries. No user download is required. Python 3.14 sampler binaries
are not bundled or tested; use a supported Python for standalone sampling.
See [Pyo installation](https://belangeo.github.io/pyo/download.html) and the
[maintainer's 1.0.6 announcement](https://github.com/belangeo/pyo/discussions/293).
wxPython and Pyo's GUI are not needed.

```python
from pyChanga import *

voice, length_ms = load_sample("voice.wav")
sampl(voice, 0.7, 1, start=0.5, rate=0.8, env=[0, 1, 0])
sampl(voice, 0.7, 1, rate=-1)  # Begin at the last frame and play backward.
sampl(voice, 0.5, 0.25, block=False)
wait(0.1)  # Overlap the next voice.
sampl(voice, 0.5, 0.25)
```

`load_sample(path)` loads an uncompressed PCM WAV with one or two channels.
Relative paths are resolved beside a saved script/composition, or against the
current directory in the REPL or an unsaved document. The second unpacked value
is the recording length in milliseconds. If you do not need it, write
`voice = load_sample("voice.wav")`. The sample handle can also be passed to
`run(function, voice)`. Use `load_sample()` in setup;
put `sampl()` in musical parts.

`sampl(sample, volume, duration, *, start=None, rate=1.0, env=None, block=True)`:

- Volume is 0–1; duration is a positive number of **beats**.
- Start is a position in the recording in **seconds**, independent of rate.
  An omitted start selects the first frame for positive rates and the last frame
  for negative rates. Zero rate is invalid. Changing rate changes speed and pitch.
- Envelope values are 2–128 amplitudes between 0 and 1, equally spaced across
  the duration. `[0, 1, 0]` rises to full volume halfway through and falls to zero.
  Omitted envelopes sustain at full volume. All voices have brief safety fades.
- Playback stops at the requested duration or file boundary, without looping.
  A blocking call advances by the full requested duration even if the file ends
  sooner. `block=False` keeps the cursor in place, as with instruments.
- Tempo changes adjust the remaining musical duration and envelope, while the
  file-reading rate stays unchanged. Stop, replacement and script-exit behavior
  follow the same rules as instrument notes.

Samples are cached until the playback session closes (64 MiB per decoded sample,
256 MiB total, at most 1024 handles). Up to 256 sample voices can overlap. A loaded handle keeps its
audio even if the file changes; loading again creates a new version. Restart
playback to clear the cache. Missing Pyo or an audio-device error is reported
when using the sampler and does not disable FluidSynth instruments.

The sampler and FluidSynth use separate native output streams coordinated by
one musical transport. Their timing is not sample-locked; device buffering can
introduce a small relative latency. `PYCHANGA_PYO_AUDIO` can select a Pyo output
backend, for example `portaudio` (the default). Silent mode records sample events
without importing Pyo. Try [the sampler example](examples/18_sampler.py), which
includes a generated demonstration sound.

Here is a composition with two parts. Save it as `song.py`, then run
`python3 -m pyChanga song.py`. Press Ctrl+C to stop playback.

```python
# %% setup
from pyChanga import *

# %% melody
while True:
    piano(60, 0.7, 0.5)
    piano(64, 0.7, 0.5)

# %% bass
while True:
    cbass(36, 0.6, 2)
```

The runner starts every named part together. Use `--part melody` to run just one,
`--part all` to launch all of them explicitly, or `--quantization immediate|beat|bar`
to choose the launch boundary; the default is the next beat. `--silent` runs with
a recording backend for tests and produces no sound. You can also run a plain
Python file with no section markers: the runner treats it as one part.

Importing `pyChanga` does not open audio or start workers. The first musical
command starts a playback session automatically. Pure helpers such as scales
remain usable without audio. The same musical functions work in an ordinary
Python REPL or a plain script:

```python
from pyChanga import *

def melody():
    while True:
        piano(64, 0.7, 0.5)

start_on_bar()
part = run(melody)
piano(60, 0.7, 1)
# Later: stop(part), stop_all(), or status()
```

Direct notes return control to the REPL after they are queued. Blocking notes
take successive beat positions; a pause at the prompt resynchronizes the next
note with the current beat. Very fast loops slow down as needed to keep the
queue bounded. `wait()` advances that same direct-note cursor. A plain
`python3 song.py` script keeps playing after its top-level code finishes until
its notes and parts finish; press Ctrl+C to stop an ongoing part. In a REPL,
`quit()` closes the session.
For silent REPL or plain-script tests, set `PYCHANGA_SILENT=1` before starting
Python.

`# %%` markers are a document convention for the package runner and IDE. For
multiple named sections, use `python3 -m pyChanga song.py` or the editor. Ordinary
Python functions and musical statements work unchanged in all three entry
points.

## Musical parts and timing

Each part runs in its own Python process and has its own variables and beat
cursor. Setup code runs separately for each part, so put imports, values, and
function definitions in setup and notes in musical parts. Code before the first
`# %%` marker also counts as setup. Section names must be unique. Nothing loops
automatically; use normal Python loops when you want repetition.

The shared clock starts at **60 BPM**. A blocking note or `wait(beats)` advances
only the calling part's cursor. `block=False` schedules a note without advancing
that cursor, allowing notes to overlap. A finite part finishes after its last
scheduled note ends, including any nonblocking notes.

A `# %% all` section may contain comments but no music. It launches every named
musical part at the same boundary. A syntax or setup error cancels that group
launch and keeps existing parts playing. Re-running a named part prepares a new
process and replaces the old one at the chosen boundary. A runtime error affects
only its own part. Renaming a playing section creates a new part; the old one
continues until stopped.

Use `run(function, *args, **kwargs)` in a musical part, REPL, or plain script to
start another independent part:

```python
# %% setup
from pyChanga import *

def melody(note):
    while True:
        piano(note, 0.7, 0.5)

# %% conductor
first = run(melody, 60)   # melody1
second = run(melody, 64)  # melody2 plays at the same time
```

`run()` returns the instance name and does not advance the caller's beat cursor.
Each launch captures that version of the function; redefining it later does not
change an existing part. `stop(name)` stops one instance, `stop_all()` silences
everything, and `status()` reports the beat, tempo, launch mode, and part states.
Functions imported from `random`, such as `choice`, receive independent default
random streams in each instance. Use an explicit `Random(seed)` object for
reproducible results.

## Music API

`piano(note, vol, dur, block=True)` accepts a whole MIDI pitch from 0 to 127 or a
list/tuple of pitches for a chord. Volume ranges from 0 to 1. Duration is a
positive number of beats. Volume zero is silent; MIDI pitch zero is a real note.
All instruments below use the same arguments. The bundled soundfont provides
these bank-0 presets:

| Preset | Instrument | Preset | Instrument |
| --- | --- | --- | --- |
| 00 | `piano` | 01 | `rhodes` |
| 02 | `epiano` | 03 | `cbass` |
| 04 | `drums` | 05 | `chip` |
| 06 | `bass` | 08 | `vibra` |
| 12 | `marimba` | 16 | `b3` |
| 17 | `organ` | 21 | `sh2000` |
| 22 | `arp` | 23 | `ether` |
| 40 | `violin` | 41 | `viola` |
| 42 | `cello` | 50 | `strings` |
| 68 | `oboe` | 71 | `clarinet` |
| 72 | `sub` | | |

`bass` and `cbass` are different presets. The older names `sax`, `guitar`, and
`synth` are not in the bundled soundfont.

- `wait(beats)` advances the calling part without playing a note.
- `tempo(bpm)` changes the shared tempo from 20 to 400 BPM without resetting beat
  phase. A tempo call during setup takes effect when the part launches; a later
  call is scheduled beyond the committed audio window.
- `start_immediate()`, `start_on_beat()`, and `start_on_bar()` set one persistent
  launch mode for the current playback session. It controls subsequent `run()`
  and `# %%` launches until changed again; the default is the next beat and a
  bar is four beats. Direct notes use their beat cursor instead. A timing call
  in section setup affects that section's launch.
- `major_scale(root)`, `natural_minor_scale(root)`, `pentatonic_scale(root)`, and
  `pentatonic_minor_scale(root)` accept positive or negative integer degrees and
  bounded slices such as `scale[:8]`.
- `drumSeq("k-h-s-h-", 0.25)` plays the `drums` preset. The letters `k`, `s`, `h`,
  `c`, `t`, `o`, and `m` select kick 36, snare 37, hi-hat 48, cymbal 65, tom 55,
  open hi-hat 68, and muted hi-hat 50.
- `chipSeq("k-h-s-h-", 0.25)` uses the `chip` preset. The same letters select
  pitches 60, 62, 63, 65, 64, 67, and 66. Both sequence functions use `-` for a
  rest and apply the supplied duration to every step.

## How playback works

One engine owns the shared beat-to-time mapping, note scheduling, and audio
backend. Workers can plan notes up to 100 ms ahead. The engine keeps note times
in beats until they enter the native scheduling window, then sends absolute
timestamps to FluidSynth. Python does not run inside FluidSynth's audio callback.
Tempo changes keep the beat phase continuous.

Each part revision owns its queued notes and audio channels. Stopping or replacing
one part does not silence another, even if both play the same pitch. Late note
starts are dropped with a warning instead of being played in a burst. The package
limits playback to 32 active parts, 1,024 pending notes per part, and 256
simultaneously allocated note channels. Printed output is limited to 16 KB per
part per second. A busy loop can be stopped because parts run in separate
processes. User Python still has normal filesystem and operating-system access.

For the module map and rules to preserve when changing playback, see the
[contributor guide](ARCHITECTURE.md). Soundfont and dependency licensing is in
[third-party notices](THIRD_PARTY_NOTICES.md).

## Check the package

From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tests/soak.py --seconds 600
```

Native audio tests render PCM through FluidSynth without an audio device. They
check onset timing, cancellation, and overlapping notes, and skip when
FluidSynth is unavailable. The optional soak test runs eight worker processes
for ten minutes and writes `test-results/soak.json`. Audio-device latency still
depends on the host system; scheduling accuracy is not a speaker-latency
guarantee.
