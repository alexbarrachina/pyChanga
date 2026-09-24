"""Verify the supplied soundfont and the offline runtime's source selection."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pyChanga_package'))
from pyChanga.instruments import PROGRAMS

spec = importlib.util.spec_from_file_location('prepare_runtime', ROOT / 'scripts' / 'prepare_runtime.py')
prepare_runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_runtime)


class SoundfontTests(unittest.TestCase):
    def test_bundled_presets_match_the_instrument_catalog(self):
        data = (ROOT / 'pyChanga_package/pyChanga/sounds/pyChanga.sf2').read_bytes()
        self.assertEqual(data[:4], b'RIFF')
        self.assertEqual(data[8:12], b'sfbk')
        self.assertEqual(struct.unpack_from('<I', data, 4)[0] + 8, len(data))

        def chunks(start, end):
            while start + 8 <= end:
                name, size = struct.unpack_from('<4sI', data, start)
                yield name, start + 8, size
                start += 8 + size + size % 2

        presets = set()
        for name, offset, size in chunks(12, len(data)):
            if name == b'LIST' and data[offset:offset + 4] == b'pdta':
                for child, pos, length in chunks(offset + 4, offset + size):
                    if child == b'phdr':
                        # The final 38-byte record is the end-of-presets marker.
                        for record in range(pos, pos + length - 38, 38):
                            program, bank = struct.unpack_from('<HH', data, record + 20)
                            presets.add((bank, program))
        self.assertEqual(len(PROGRAMS), 21)
        self.assertEqual(presets, {(0, program) for program in PROGRAMS.values()})

    def test_runtime_uses_local_soundfont_without_downloading(self):
        with patch.object(prepare_runtime, 'download', side_effect=AssertionError('Unexpected download')):
            metadata = prepare_runtime.soundfont()
        self.assertEqual(metadata['source'], 'pyChanga_package/pyChanga/sounds/pyChanga.sf2')
        self.assertEqual(metadata['soundfontSha256'], hashlib.sha256((ROOT / metadata['source']).read_bytes()).hexdigest())

    def test_missing_or_invalid_soundfont_is_reported_without_download(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(prepare_runtime, 'ROOT', Path(directory)), \
                patch.object(prepare_runtime, 'download', side_effect=AssertionError('Unexpected download')):
            with self.assertRaisesRegex(RuntimeError, 'Bundled soundfont not found'):
                prepare_runtime.soundfont()
            target = Path(directory) / 'pyChanga_package/pyChanga/sounds/pyChanga.sf2'
            target.parent.mkdir(parents=True)
            target.write_bytes(b'not a soundfont')
            with self.assertRaisesRegex(RuntimeError, 'Invalid SoundFont'):
                prepare_runtime.soundfont()


if __name__ == '__main__':
    unittest.main()
