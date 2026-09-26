# Bundled components

pyChangaIDE's packaged application includes the following components. The build
records exact versions and native library hashes in `runtime-manifest.json`.

- **CPython 3.13**: Python Software Foundation license and bundled dependency
  notices, retained in the standalone Python distribution. Distribution source:
  https://github.com/astral-sh/python-build-standalone
- **FluidSynth**: LGPL-2.1-or-later. Distributed as a separate dynamic library.
  Source and releases: https://github.com/FluidSynth/fluidsynth
  The native dependency licenses are retained under `runtime/native/licenses`
  on macOS, and alongside the libraries on Windows.
- **pyChanga.sf2**: project-provided SoundFont, included under
  `runtime/packages/pyChanga/sounds`. Its source path and SHA-256 hash are recorded
  in `runtime-manifest.json`.
- **Pyo 1.0.6**: LGPL-3.0-or-later. Distributed as separate extension modules
  under `runtime/packages/pyo`, with its license retained in
  `runtime/packages/pyo-1.0.6.dist-info/LICENSE`. Source:
  https://github.com/belangeo/pyo
  The maintainer's wheels include native audio/file libraries. Their license
  files and wheel metadata are retained in `runtime/packages`; binary paths and
  hashes are recorded in the Pyo section of `runtime-manifest.json`.
- **Sampler demo**: an original generated waveform in `examples/samples/demo.wav`;
  no third-party recording is used. See its adjacent README for generation details.
- **Electron**: MIT and its bundled Chromium/third-party licenses. Electron
  license files are retained in the packaged application.
- **Monaco Editor**: MIT, https://github.com/microsoft/monaco-editor
- **cloudpickle 3.1.2**: BSD-3-Clause. Used to start independent function
  instances. Its license is retained at
  `runtime/packages/pyChanga/_vendor/cloudpickle/LICENSE`.
  Source: https://pypi.org/project/cloudpickle/3.1.2/

The old TimGM6mb and E-mu SoundFonts and vendored SCAMP/clockblocks reference code
are not included in new application distributions. Historical TimGM6mb attribution
and license files are retained in `legacy/sounds`. The new engine does not copy their
implementation. This notice does not change the licenses of the original course
materials or select a license for the user's new application code.
