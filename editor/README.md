# pyChanga editor and desktop IDE

The browser editor in this directory provides a live-coding interface for the
[pyChanga Python package](../README.md). The `desktop/` directory supplies the
Electron window, file dialogs, settings, and a Python playback service. The
editor's [host contract](bridge.ts) contains browser-safe types; the desktop
[preload bridge](../desktop/preload.ts) implements it. Music, timing, workers, and
FluidSynth remain in the Python package.

## Work in the editor

Open pyChangaIDE, then click **Run** beside a musical part. Change its code and
click **Update**, or select code in that section and press **Cmd+Enter** on macOS
or **Ctrl+Enter** on Windows. Selections must stay within one section; they are
dedented for execution while error messages keep their original line numbers.
Stop individual parts in the sidebar. **Stop all** or **Cmd/Ctrl+.** silences the
performance immediately.

The BPM control changes the package's shared tempo, which starts at 60 BPM. Code
may also call `tempo(bpm)`; a successful setup with `tempo()` applies that tempo
again on each launch. **Start on** selects the next beat, next four-beat bar, or
an immediate launch. This is the package's persistent launch mode, shared with
`start_immediate()`, `start_on_beat()`, and `start_on_bar()` in Python code. When
code changes the mode, the selector updates. A timing call during setup affects
that section's launch; grouped parts still begin on one boundary. The beat
position comes from package status events; the editor displays it in four-beat
bars. The editor does not schedule notes.

Add an empty `# %% all` section to a file to launch all named parts together.
Place the cursor on it and press **Cmd/Ctrl+Enter**, or click **Run all**. Each
part prepares its own setup; they begin on one launch boundary. A syntax or
setup error cancels the group launch and leaves existing playback running. The
`# %% all` marker is a control, not a musical part. Re-running it replaces the
group together.

A file without markers is one part. In a marked file, text before the first
marker is setup, and `# %% setup` must precede musical parts. Setup is rerun
separately for each part. Use ordinary Python loops for repetition. A function
started with `run(function)` appears as its own numbered part in the sidebar,
where you can stop it individually. If you rename a playing `# %%` section and
launch the new name, the old part keeps playing until stopped.

The editor shows the package's output, errors, part states, pending launches,
beat position, and tempo. The [package README](../README.md) explains the
musical functions, REPL use, and command-line runner in detail. Ordinary Python
functions and musical statements are shared across the IDE, REPL, and scripts;
`# %%` sections are run as a document by the IDE or package runner.

## Develop the editor

From the repository root, use Node 22.12+ (Node 24 recommended), Python 3.11+,
and FluidSynth. On macOS, a development installation of FluidSynth can come
from Homebrew. Windows developers can use the prepared runtime rather than
installing FluidSynth globally.

```sh
npm install
python3 scripts/prepare_runtime.py
npm run dev
```

The development command serves `editor/` in a browser process and opens the
Electron desktop host. Set `PYCHANGA_PYTHON` to choose the development Python
interpreter. Set `PYCHANGA_NATIVE_DIR` to the prepared runtime's `native`
directory if using its FluidSynth libraries. `PYCHANGA_SILENT=1` explicitly
selects a silent test backend; audio failures do not silently switch to it.

`prepare_runtime.py` downloads checksum-verified Python and bundles the local
soundfont, recording its SHA-256 hash. It also prepares native FluidSynth
libraries. The soundfont is already in the repository and needs no separate
download. Preparing the runtime needs internet access; the resulting app runs
offline.

The app checks that the audio clock advances before reporting **Audio ready**.
On macOS, it tries the bundled PortAudio driver if CoreAudio cannot play. If
neither works, it reports an audio error.

## Build and check the IDE

```sh
npm run typecheck
npm run build
npm run test:desktop
python3 scripts/prepare_runtime.py
npm run make
```

The desktop smoke test exercises the real editor and Electron controls. It uses
silent playback unless `PYCHANGA_TEST_AUDIO=1` is set. For a packaged-app test
without system Python on the search path, set `PYCHANGA_TEST_APP` to the app's
executable.

The packaged runtime lives outside the application archive and includes CPython,
its standard library, pyChanga, FluidSynth and its dependent libraries, the
soundfont, licenses, and a version/hash manifest. The Mac DMG contains the app
and an Applications shortcut. Windows builds produce a Squirrel installer and
a ZIP. Build each target on its own operating system and architecture. Configured
CI targets are macOS arm64, macOS x64, and Windows x64.

Unsigned artifacts are for development. For a signed release, set
`SIGN_RELEASE=true`. macOS signing requires an installed Developer ID identity
and `APPLE_SIGN_IDENTITY`, `APPLE_ID`, `APPLE_APP_PASSWORD`, and `APPLE_TEAM_ID`.
Windows signing requires a certificate and `WINDOWS_CERTIFICATE_FILE` plus
`WINDOWS_CERTIFICATE_PASSWORD`. CI secrets do not install certificates.

Historical assets and legacy wrappers are excluded from application bundles.
See the [GitHub and release guide](../GITHUB.md) and
[third-party notices](../THIRD_PARTY_NOTICES.md). Audio output and clean-machine
behavior still need checks on each target system; scheduling accuracy does not
guarantee speaker latency under every system load.
