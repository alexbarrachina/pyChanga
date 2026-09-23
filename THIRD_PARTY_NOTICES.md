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
- **TimGM6mb**: GPL-2.0-only; copyright 2004 Tim Brechbill and 2010 David Bolton.
  The unmodified SoundFont, complete license, provenance, and attribution are
  included under `runtime/packages/pyChanga/sounds`. Its source archive is
  https://deb.debian.org/debian/pool/main/t/timgm6mb-soundfont/timgm6mb-soundfont_1.3.orig.tar.gz
- **Electron**: MIT and its bundled Chromium/third-party licenses. Electron
  license files are retained in the packaged application.
- **Monaco Editor**: MIT, https://github.com/microsoft/monaco-editor

The old E-mu SoundFont and vendored SCAMP/clockblocks reference code are not
included in new application distributions. The new engine does not copy their
implementation. This notice does not change the licenses of the original course
materials or select a license for the user's new application code.
