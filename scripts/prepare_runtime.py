"""Prepare an offline Python + FluidSynth + Pyo runtime.

Downloads have pinned checksums. On macOS, copy and relocate the native
FluidSynth dependency tree from Homebrew; it is needed only on build machines.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
from urllib.parse import quote
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache' / 'downloads'
LOCK = json.loads((ROOT / 'scripts' / 'runtime-lock.json').read_text())


def download(url, checksum=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    filename = CACHE / url.rsplit('/', 1)[-1].replace('%2B', '+')
    if not filename.exists():
        print(f'Downloading {filename.name}', flush=True)
        with urlopen(Request(url, headers={'User-Agent':'pyChangaIDE-build'}), timeout=120) as response:
            data = response.read()
        if checksum and hashlib.sha256(data).hexdigest() != checksum:
            raise RuntimeError(f'Checksum mismatch: {filename.name}')
        filename.write_bytes(data)
    if checksum and hashlib.sha256(filename.read_bytes()).hexdigest() != checksum:
        raise RuntimeError(f'Checksum mismatch in cached download: {filename}')
    return filename


def soundfont():
    target = ROOT / 'pyChanga_package' / 'pyChanga' / 'sounds' / 'pyChanga.sf2'
    if not target.is_file():
        raise RuntimeError(f'Bundled soundfont not found: {target}')
    data = target.read_bytes()
    if data[:4] != b'RIFF' or data[8:12] != b'sfbk':
        raise RuntimeError(f'Invalid SoundFont file: {target}')
    return {'source': target.relative_to(ROOT).as_posix(),
            'soundfontSha256': hashlib.sha256(data).hexdigest()}


def mac_native(destination):
    prefix = Path(subprocess.check_output(['brew', '--prefix', 'fluidsynth'], text=True).strip())
    initial = prefix / 'lib' / 'libfluidsynth.dylib'
    dependencies = {}

    def collect(original):
        original = original.resolve()
        if original.name in dependencies:
            if dependencies[original.name]['original'] != original:
                raise RuntimeError(f'Native library name collision: {original}')
            return
        output = subprocess.check_output(['otool', '-L', str(original)], text=True)
        linked = [line.strip().split(' (')[0] for line in output.splitlines()[1:]]
        dependencies[original.name] = {'original': original, 'linked': linked}
        for dependency in linked:
            if dependency.startswith(('/opt/homebrew/', '/usr/local/')):
                child = Path(dependency).resolve()
                if child != original:
                    collect(child)

    collect(initial)
    manifest = []
    for name, metadata in dependencies.items():
        target = destination / name
        shutil.copy2(metadata['original'], target)
        target.chmod(target.stat().st_mode | 0o200)
        subprocess.run(['install_name_tool', '-id', '@rpath/' + name, str(target)], check=True, capture_output=True)
        for dependency in metadata['linked']:
            if dependency.startswith(('/opt/homebrew/', '/usr/local/')):
                replacement = '@loader_path/' + Path(dependency).resolve().name
                subprocess.run(['install_name_tool', '-change', dependency, replacement, str(target)], check=True, capture_output=True)
        subprocess.run(['codesign', '--force', '--sign', '-', str(target)], check=True, capture_output=True)
        manifest.append({'name':name,'source':str(metadata['original']),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    # Preserve the actual licenses shipped by Homebrew with each dependency.
    licenses = destination / 'licenses'
    licenses.mkdir(exist_ok=True)
    for metadata in dependencies.values():
        original = metadata['original']
        cellar = next((parent for parent in original.parents if (parent / 'INSTALL_RECEIPT.json').exists()), None)
        if cellar:
            for candidate in cellar.rglob('*'):
                if candidate.is_file() and candidate.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'COPYRIGHT')):
                    target = licenses / cellar.parent.name / candidate.relative_to(cellar)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(candidate, target)
    return manifest


def sampler(runtime, packages, target):
    """Install the exact Pyo wheel, including its bundled native libraries."""
    specification = LOCK['pyo'][target]
    wheel = download(specification['url'], specification['sha256'])
    python = runtime / 'python' / ('python.exe' if target.startswith('win32') else 'bin/python3')
    subprocess.run([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps',
                    '--upgrade', '--target', str(packages), str(wheel)], check=True)
    native_files = []
    # Some wheels place shared libraries beside the Python package.
    for path in sorted(packages.rglob('*')):
        if path.suffix in ('.so', '.dylib', '.dll', '.pyd'):
            if target.startswith('darwin'):
                subprocess.run(['codesign', '--force', '--sign', '-', str(path)], check=True, capture_output=True)
            native_files.append({'path': path.relative_to(runtime).as_posix(),
                                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    environment = {**os.environ, 'PYTHONPATH': str(packages), 'PYCHANGA_REQUIRE_PYO': '1'}
    # Rendering tests make a missing or broken sampler a build error on every
    # target, without requiring a physical audio device on the build machine.
    subprocess.run([str(python), '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'),
                    '-p', 'test_native_sampler.py', '-v'],
                   env=environment, check=True, timeout=30)
    return {'version': LOCK['pyo']['version'], **specification, 'native': native_files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--soundfont-only', action='store_true')
    parser.add_argument('--target', default=f'{sys.platform}-{"arm64" if platform.machine() in ("arm64","aarch64") else "x64"}')
    args = parser.parse_args()
    font = soundfont()
    print('Verified soundfont:', font['soundfontSha256'], flush=True)
    if args.soundfont_only:
        return
    runtime = ROOT / 'runtime' / args.target / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    python = LOCK['python'][args.target]
    url = f'https://github.com/astral-sh/python-build-standalone/releases/download/{LOCK["python"]["release"]}/{quote(python["asset"])}'
    archive = download(url, python['sha256'])
    if not (runtime / 'python').exists():
        with tarfile.open(archive) as source:
            source.extractall(runtime, filter='data')
    packages = runtime / 'packages'
    packages.mkdir(exist_ok=True)
    # Retire the previous package from this generated runtime after the rename.
    if (packages / 'musica').exists():
        shutil.rmtree(packages / 'musica')
    # Replace the generated package so retired soundfonts cannot linger in builds.
    if (packages / 'pyChanga').exists():
        shutil.rmtree(packages / 'pyChanga')
    shutil.copytree(ROOT / 'pyChanga_package' / 'pyChanga', packages / 'pyChanga',
                    ignore=shutil.ignore_patterns('__pycache__', 'Emu_Planet_Phatt_Hip_Hop.sf2'))
    pyo = sampler(runtime, packages, args.target)
    native = runtime / 'native'
    native.mkdir(exist_ok=True)
    if args.target.startswith('darwin'):
        if sys.platform != 'darwin':
            raise RuntimeError('Build the macOS runtime on the target macOS architecture')
        manifest = mac_native(native)
    else:
        fluid = LOCK['fluidsynthWindows']
        archive = download(f'https://github.com/FluidSynth/fluidsynth/releases/download/v{fluid["version"]}/{fluid["asset"]}', fluid['sha256'])
        manifest = []
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                if member.filename.lower().endswith('.dll') or any(word in Path(member.filename).name.lower() for word in ['license', 'copying', 'copyright']):
                    target = native / Path(member.filename).name
                    target.write_bytes(source.read(member))
                    manifest.append({'name':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    (runtime / 'runtime-manifest.json').write_text(json.dumps({'target':args.target,'python':python,'native':manifest,'soundfont':font,'pyo':pyo}, indent=2))
    shutil.copy2(ROOT / 'THIRD_PARTY_NOTICES.md', runtime / 'THIRD_PARTY_NOTICES.md')
    print('Offline runtime ready:', runtime, flush=True)


if __name__ == '__main__':
    main()
