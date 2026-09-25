# pyChangaIDE

`pyChanga` is the Python music library; `pyChangaIDE` is its desktop live-coding editor. Each named musical
part runs in its own Python process. One playback service owns the musical clock
and FluidSynth audio. Re-running a part replaces it on the next beat while the
others continue.

## Start making music

Open the desktop app, then click **Run** beside melody, bass, and rhythm. Change a
part and click **Update**, or select code in that section and press **Cmd+Enter**
on macOS / **Ctrl+Enter** on Windows. Stop individual parts in the sidebar; use
**Stop all** or **Cmd/Ctrl+.** for immediate silence.

```python
# %% setup
from pyChanga import *
from random import choice

notes = [60, 64, 67, 72]

# %% melody
while True:
    piano(choice(notes), 0.7, 0.5)

# %% bass
while True:
    cbass(36, 0.6, 2)
    cbass(43, 0.6, 2)
```

The clock starts at **60 BPM**, equivalent to `tempo(60)`. Change the tempo with
the BPM control or `tempo(bpm)`; explicit tempo calls in lessons override the default.

Setup runs afresh for every part. Imports, values, and function definitions are
independent copies; there is no shared mutable namespace. Music belongs in parts,
not setup. Nothing repeats automatically: use ordinary Python loops. A finite
part finishes after its final scheduled note, including nonblocking notes.

Text before the first section is setup;
`# %% setup`, when present, must come before the musical parts. A file without sections is
one part. Names must be unique within a file. A selection cannot cross sections.
Selections are dedented and retain their original line numbers for errors.

Add an empty `# %% all` section to launch every musical part in the current file.
Place the cursor on that line and press **Cmd/Ctrl+Enter**, or click **Run all**
in the sidebar. All parts prepare their own setup, then start together at the
selected launch boundary. Running it again replaces all those parts together.
A syntax or setup error cancels the group launch and leaves existing playback
running. The launcher may contain comments, but music belongs in named parts:

```python
# %% setup
from pyChanga import *

# %% melody
while True:
    piano(60, 0.7, 1)

# %% rhythm
while True:
    drumSeq("k-h-s-h-")

# %% all
```

The launcher is a control, so it does not create an extra musical part.

Use `run(function)` to start a function as an independent musical part. Define
the function in setup, then launch it from a musical section:

```python
# %% setup
from pyChanga import *

def melody(note):
    while True:
        piano(note, 0.7, 0.5)

# %% conductor
run(melody, 60)  # melody1
run(melody, 64)  # melody2, playing at the same time
```

`run()` returns the new part's name. Each call starts a separate instance, and
the caller continues immediately without advancing its beat cursor. The sidebar
shows each instance separately, so you can stop one without stopping the others.
Helpers imported from `random`, such as `randint` and `choice`, get independent
random streams in each instance. Use an explicit `Random(seed)` object when you
want reproducible results.
Use `# %% all` to start every named section together. If you rename a playing
`# %%` section and launch the new name, the old part keeps playing until stopped.


## Music API

Notation and some examples are inpired in SCAMP https://scamp.marcevanstein.com/

`piano(note, vol, dur, block=True)` plays an integer MIDI pitch from 0 to 127, or a
list/tuple for a chord. Volume is 0–1; duration is positive beats. `block=False`
schedules a note without advancing the part's cursor, so subsequent notes can
overlap. Use `wait(beats)` to advance time without a note. Volume zero is silent;
MIDI pitch zero is a real note.

The bundled `pyChanga.sf2` provides these zero-based presets, all in bank 0:

| Preset | Instrument |
| --- | --- |
| 00 | `piano` |
| 01 | `rhodes` |
| 02 | `epiano` |
| 03 | `cbass` |
| 04 | `drums` |
| 05 | `chip` |
| 06 | `bass` |
| 08 | `vibra` |
| 12 | `marimba` |
| 16 | `b3` |
| 17 | `organ` |
| 21 | `sh2000` |
| 22 | `arp` |
| 23 | `ether` |
| 40 | `violin` |
| 41 | `viola` |
| 42 | `cello` |
| 50 | `strings` |
| 68 | `oboe` |
| 71 | `clarinet` |
| 72 | `sub` |

Each instrument uses the same arguments as `piano`. The new `bass` preset is
separate from `cbass`. Older names such as `sax`, `guitar`, and `synth` have been
replaced in the bundled examples.

- `tempo(bpm)` changes the shared tempo, 20–400 BPM, without resetting beat phase.
  Changes are scheduled beyond the committed audio window. A tempo request in
  successful setup takes effect at that part's launch. Re-running setup containing
  `tempo()` therefore re-applies that tempo.
- `major_scale(root)`, `natural_minor_scale(root)`, `pentatonic_scale(root)`, and
  `pentatonic_minor_scale(root)` support octave-extending integer degrees, negative
  degrees, and finite slices such as `scale[:8]` and `scale[0:7:2]`.
- `drumSeq("k-h-s-h-", 0.25)` plays the `drums` preset: `k` kick 36, `s` snare 37,
  `h` hi-hat 48, `c` cymbal 65, `t` tom 55, `o` open hi-hat 68, `m` muted hi-hat 50.
- `chipSeq("k-h-s-h-", 0.25)` plays the `chip` preset: `k` kick 60, `s` snare 62,
  `h` hi-hat 63, `c` clave 65, `t` tom 64, `o` open hi-hat 67, `m` muted hi-hat 66.
  Both sequencers use `-` for a rest and the supplied duration for every step.


## Run from source

Build tools need Node 22.12+ (Node 24 recommended), Python 3.11+, and FluidSynth.
The project also includes a local Node 24 executable for npm scripts. On a Mac
development machine, `brew install fluidsynth` supplies the native audio library.
Windows developers can use the prepared runtime below instead of installing
FluidSynth globally.

```sh
npm install
python3 scripts/prepare_runtime.py
npm run dev
```

`prepare_runtime.py` downloads checksum-verified Python and bundles the local
`pyChanga_package/pyChanga/sounds/pyChanga.sf2`, recording its SHA-256 hash.
The soundfont is supplied with the project and requires no download.
On macOS it also copies and relocates the Homebrew FluidSynth dependency tree.
Windows builds use the checksum-pinned official FluidSynth archive. This step
needs the internet; the resulting application does not.

Set `PYCHANGA_PYTHON` to a Python executable to override the development interpreter.
Set `PYCHANGA_NATIVE_DIR` to the prepared runtime's `native` directory if using its
FluidSynth libraries. `PYCHANGA_SILENT=1` is an explicit test mode; audio failures do
not silently switch to fake playback.

The app checks that the audio clock advances before reporting **Audio ready**.
On macOS, if CoreAudio fails to start playback, it tries the bundled PortAudio
driver automatically. If neither works, it reports an audio error.

The Python package has no Python dependencies. For command-line use:

```sh
python3 -m pip install ./pyChanga_package
python3 -m pyChanga examples/01_simple_arpeggio.py
python3 -m pyChanga examples/08_multi_parts.py --part melody
```

The CLI starts all named parts together unless `--part` selects one.
`--part all` also launches every part together. Ctrl+C stops playback.
Importing `pyChanga` alone never opens an audio device. Audio commands need the
editor or this runner; a bare `python lesson.py` explains how to use the runner.

## Architecture and timing

`pyChanga_package/pyChanga` contains the teaching API, source preparation,
process workers, conductor, beat/time mapping, audio adapter, CLI, and optional
communication service. It has no dependency on the editor or Electron.
`editor` contains the browser-based Monaco editor and its host interface.
`desktop` implements that interface with Electron, file dialogs, and Python
service management. See the [contributor guide](ARCHITECTURE.md) for the module
map, execution flow, and boundaries to preserve.

Each part has one logical beat cursor. Blocking notes and waits advance it;
computation does not extend musical durations. Workers are permitted to run up to
100 ms ahead. The conductor retains notes in beats until they enter the native
scheduling window. FluidSynth's sample-driven sequencer receives absolute
timestamps; Python never runs inside its audio callback.

Revision IDs own queued events and channels. Replacements prepare setup in a new
worker, then switch at a common beat boundary. Syntax/setup errors preserve the
old part. A runtime error affects only its part. Late note starts are dropped with
a warning instead of producing a catch-up burst. The native backend uses separate
channels for overlapping notes, even identical pitches.

Limits: 32 active parts, 1,024 pending notes per part, 256 simultaneously allocated
note channels, and 16 KB of printed output per part per second. Process isolation
keeps a busy loop stoppable; student Python still has normal filesystem and OS
access. This is a local programming environment, not a sandbox for untrusted code.

## Packaging

For uploading the source and sharing installers, see [the GitHub guide](GITHUB.md).

```sh
python3 scripts/prepare_runtime.py
npm run make
```

The runtime lives outside the application archive and includes CPython, the
standard library, pyChanga, FluidSynth and dependent libraries, soundfont, licenses,
and a version/hash manifest. The Mac DMG contains the app and an Applications
shortcut. Windows builds produce a Squirrel installer and a ZIP. Build each target
on its own OS/architecture; macOS arm64, macOS x64, and Windows x64 are configured
in `.github/workflows/build.yml`.

Unsigned local artifacts are for development. For a signed release, set
`SIGN_RELEASE=true`. macOS requires an installed Developer ID identity plus
`APPLE_SIGN_IDENTITY`, `APPLE_ID`, `APPLE_APP_PASSWORD`, and `APPLE_TEAM_ID`.
Windows requires a certificate on the build machine and
`WINDOWS_CERTIFICATE_FILE` / `WINDOWS_CERTIFICATE_PASSWORD`. CI secrets do not
install certificates themselves; provision those in your release environment.
Without these credentials, the build does not claim signing/notarization.

The existing `scamp_code` tree, old E-mu soundfont, original lessons, and legacy
wrapper are excluded from application bundles. License/provenance information is
in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Verification

```sh
python3 -m unittest discover -s tests -v
npm run typecheck
npm run build
npm run test:desktop
python3 tests/soak.py --seconds 600
```

Native audio tests render actual PCM through FluidSynth without a sound device.
They check onset timing within 10 ms, cancellation, and same-pitch isolation.
They skip explicitly if FluidSynth is unavailable. The real-time soak runs eight
Python processes for ten minutes and writes `test-results/soak.json`.

The desktop smoke test exercises real Electron controls. To test a packaged app
with no system Python on its search path, set `PYCHANGA_TEST_APP` to its executable.
Set `PYCHANGA_TEST_AUDIO=1` to test real audio; otherwise desktop tests are silent.
Audio-device round-trip latency and clean-machine behavior on each target OS still
need hardware validation; scheduling precision is not a guarantee of speaker
latency under arbitrary system load.
