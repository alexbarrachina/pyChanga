import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pyChanga_package"))
import pyChanga
from pyChanga import api
from pyChanga.sections import execution, parse_document
from pyChanga.transport import Transport


class FakeRuntime:
    def __init__(self):
        self.calls = []
    def note(self, *args):
        self.calls.append(("note", *args))
    def wait(self, beats):
        self.calls.append(("wait", beats))
    def tempo(self, bpm):
        self.calls.append(("tempo", bpm))


class MusicTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()
        api._bind(self.runtime)
    def tearDown(self):
        api._bind(None)
    def test_chords_and_nonblocking(self):
        pyChanga.piano([60, 64, 67], 0.7, 0.5, block=False)
        self.assertEqual(self.runtime.calls, [("note", "piano", [60, 64, 67], 0.7, 0.5, False)])
    def test_validation(self):
        for args in [(60.5, 0.5, 1), (128, 0.5, 1), (60, 2, 1), (60, 0.5, 0), (60, float('nan'), 1), ([], 0.5, 1)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                pyChanga.piano(*args)
    def test_drum_rest_duration_and_mapping(self):
        pyChanga.drumSeq("k-s", 0.75)
        self.assertEqual(self.runtime.calls[1], ("wait", 0.75))
        self.assertEqual([self.runtime.calls[i][2] for i in (0, 2)], [[36], [38]])
    def test_scales(self):
        scale = pyChanga.major_scale(60)
        self.assertEqual(scale[:8], [60, 62, 64, 65, 67, 69, 71, 72])
        self.assertEqual(scale[-1], 59)
        self.assertEqual(scale[14], 84)
        self.assertEqual(scale[7:0:-2], [72, 69, 65, 62])
        with self.assertRaises(ValueError):
            scale[:]
    def test_no_fork_or_audio_on_import(self):
        self.assertFalse(hasattr(pyChanga, "fork"))
        self.assertFalse(hasattr(pyChanga, "wait_forever"))
        api._bind(None)
        pyChanga.set_piano()
        with self.assertRaisesRegex(RuntimeError, "python -m pyChanga"):
            pyChanga.piano(60, 1, 1)


class SectionTests(unittest.TestCase):
    source = '# %% setup\nfrom pyChanga import *\nx = 60\n\n# %% melody\nwhile True:\n    piano(x, 0.7, 1)\n\n# %% bass\nbass(36, 0.8, 2)\n'
    def test_parse(self):
        doc = parse_document(self.source)
        self.assertEqual([p.name for p in doc.parts], ["melody", "bass"])
        self.assertEqual(doc.parts[0].start_line, 6)
        self.assertIn("x = 60", doc.setup)
    def test_selected_indented_code_keeps_line(self):
        _, part, body = execution(self.source, 'song.py', {"startLine": 7, "endLine": 7, "startColumn": 1, "endColumn": 21})
        self.assertEqual(part.name, 'melody')
        self.assertEqual(body.splitlines()[6], 'piano(x, 0.7, 1)')
    def test_cross_sections_rejected(self):
        with self.assertRaisesRegex(ValueError, "one musical section"):
            execution(self.source, 'song.py', {"startLine": 7, "endLine": 10, "startColumn": 1, "endColumn": 10})
    def test_duplicate_and_setup_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_document('# %% a\npass\n# %% a\npass\n')
        with self.assertRaisesRegex(ValueError, "Setup is replayed"):
            execution(self.source, 'song.py', {"startLine": 2, "endLine": 2})
    def test_plain_and_marker_in_string(self):
        doc = parse_document('text = """\n# %% not a part\n"""\nprint(text)\n')
        self.assertEqual([p.name for p in doc.parts], ['main'])
    def test_syntax_error_line(self):
        with self.assertRaises(SyntaxError) as caught:
            execution('# %% a\nx =\n', 'bad.py')
        self.assertEqual(caught.exception.lineno, 2)


class TransportTests(unittest.TestCase):
    def test_default_is_sixty_beats_per_minute(self):
        transport = Transport(100)
        self.assertEqual(transport.bpm_at(100), 60)
        self.assertEqual(transport.time_at(4), 104)
    def test_tempo_preserves_phase_and_remaining_duration(self):
        transport = Transport(100, bpm=120)
        transport.set_tempo(60, 4)
        self.assertEqual(transport.time_at(4), 102)
        self.assertEqual(transport.time_at(8), 106)
        self.assertEqual(transport.beat_at(103), 5)
        for beat in (0, 1/3, 3.99, 4, 8, 1200):
            self.assertAlmostEqual(transport.beat_at(transport.time_at(beat)), beat)
    def test_no_ten_minute_drift(self):
        transport = Transport(0, bpm=120)
        for stream in range(8):
            for index in range(4800):
                # Absolute beat positions, independent of worker processing delays.
                self.assertEqual(transport.time_at(index / 4), index / 8)
        self.assertEqual(transport.boundary(0.13, 1), 1)
        self.assertEqual(transport.boundary(0.13, 4), 4)


if __name__ == '__main__':
    unittest.main()
