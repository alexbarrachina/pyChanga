# Contributor guide

The project has three layers. Work on music belongs in the Python package;
work on editing belongs in the browser editor; work on operating-system
integration belongs in the desktop IDE.

| Directory | Responsibility | Dependencies |
| --- | --- | --- |
| `pyChanga_package/` | Music API, clock, workers, scheduling, audio, CLI | Python and the native FluidSynth library for audio |
| `editor/` | Monaco editor, documents, musical controls, visual feedback | Browser APIs, Monaco, and the host contract in `bridge.ts` |
| `desktop/` | Electron window, file dialogs, preferences, Python service lifecycle | Electron, Node, and the editor's host contract |

The Python package never imports editor or desktop code. The editor never imports
Electron or Node code. The desktop implements `window.pyChanga` through its
isolated preload bridge. The Python package can be installed and used from the
command line without Node, Monaco, or Electron.

## Reading the Python package

Read these files in the order of the behavior you want to change:

| File | What it owns |
| --- | --- |
| `api.py` | Public music functions and argument validation; the small `Runtime` contract |
| `session.py` | Lazy ordinary-Python client, REPL output, and interpreter-exit cleanup |
| `function_capture.py` | Shared function capture for `run()`, including argument limits and worker random streams |
| `instruments.py`, `scales.py` | Instrument presets and musical scale values |
| `sections.py` | `# %%` document parsing and source selections |
| `execution.py` | Compilation and preparation of a complete `LaunchPlan`, before playback changes |
| `engine.py` | Part lifecycle, worker supervision, shared scheduling, and runtime status |
| `worker.py` | One part's Python execution, local beat cursor, and requests to the engine |
| `transport.py` | Conversion between beats and playback seconds, including tempo changes |
| `audio.py` | FluidSynth adapter and the silent recording backend used in tests |
| `errors.py` | Source locations and tracebacks, without UI formatting |
| `protocol.py` | External command validation, dispatch, and response objects |
| `service.py` | Standard-input/output communication and the engine's service loop |
| `__main__.py` | Command-line options, file execution, and service startup |

`Engine.run()` and `Engine.run_all()` are conveniences for source-based callers.
They prepare a launch plan and pass it to `Engine.start()`. The engine does not
handle protocol versions or protocol responses. `protocol.handle_command()`
adapts external commands; `service.py` adds the protocol version to outgoing
events. These are internal integration APIs; the teaching API is exported from
`pyChanga`.

## From a command to sound

1. The CLI reads a file, the editor submits its source through the desktop
   bridge, or ordinary Python starts the package service on its first musical
   call. Source documents are parsed and compiled before workers are started.
2. The engine starts a Python **process** for each part. It binds the musical API
   inside that process to `PartRuntime`, then executes setup.
3. After setup succeeds, the engine chooses a shared launch boundary. An existing
   revision continues until its replacement is ready to take over.
4. `piano()` validates a note and asks the bound runtime to send it to the
   engine. Workers have a local beat cursor; the REPL has a direct-note cursor
   that resynchronizes after idle time. Blocking notes advance the cursor;
   `block=False` leaves it in place. `wait()` advances it without a note.
5. The engine keeps notes in beats until they enter the 100 ms scheduling window.
   `Transport` converts those beats to seconds. The audio backend sends timed
   note-on and note-off events to FluidSynth's native sequencer.
6. Runtime events report status, output, and errors. The editor displays them;
   it does not determine playback timing.

There is one musical clock per engine, with FluidSynth playback time as its audio
reference. Each worker has its own cursor and namespace. `run(function)` captures
the function and its arguments and asks the engine to start another process.
It does not create another clock or audio device. The service's reader and writer
threads only move messages; its main thread alone calls the engine.
The engine also owns the persistent launch mode. Worker setup instructions are
applied before choosing a section boundary; a grouped launch applies setup
changes in document order and gives every member one boundary. The editor
selector reads and writes this package setting.

## Rules to preserve when changing playback

- Importing `pyChanga` must not open audio or start workers.
- Compile every member of a group before starting it. All members finish setup
  before receiving the same launch beat.
- Preserve the currently playing revision if replacement preparation fails.
- A part owns its queued events and voices. Stopping it must not silence another
  part, even when both play the same pitch.
- A finished Python function may still have scheduled notes. Drain those notes
  before finishing the part.
- Keep Python out of the native audio callback. Keep worker communication bounded
  so one part cannot monopolize scheduling.
- Musical errors should describe the problem without referring to an IDE button.
  Clients decide how to display recovery actions.

Bars currently contain four beats. A configurable meter would be package logic;
the editor would display the meter reported by the package.

## Current standalone support

From the repository root:

```sh
python3 -m pip install ./pyChanga_package
python3 -m pyChanga examples/01_simple_arpeggio.py
```

FluidSynth is a native dependency, separate from Python package dependencies.
The package includes its soundfont; the desktop installer additionally bundles
Python and native libraries for its own users.

A plain Python REPL or `python song.py` can use the music API directly. The
first musical call creates a package-owned service, with no explicit session
start or stop. Script exit drains scheduled notes and parts; REPL exit closes
the service. `# %%` documents use `python -m pyChanga song.py` or the IDE for
their multiple-section behavior. `Engine.start(plan)` remains an internal
launch operation.

## Development checks

```sh
python3 -m unittest discover -s tests -v
npm run typecheck
npm run build
npm run test:desktop
```

Python tests cover the teaching API, section parsing, process isolation,
replacement, synchronization, protocol responses, and native audio rendering.
The desktop smoke test covers the full editor → desktop → package connection.
`npm run dev` serves `editor/` and opens it in the Electron host. Production builds
still write the editor to `dist/renderer` and the desktop host to `dist`.
