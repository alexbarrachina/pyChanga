import pathlib
import sys
import unittest
from unittest.mock import patch

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
    def run(self, function, args, kwargs):
        self.calls.append(("run", function, args, kwargs))
        return function.__name__ + '1'
    def launch_mode(self, mode):
        self.calls.append(("launch_mode", mode))
    def stop(self, part):
        self.calls.append(("stop", part))
    def stop_all(self):
        self.calls.append(("stop_all",))
    def status(self):
        self.calls.append(("status",))
        return {"launchMode": "beat"}


class MusicTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()
        api._bind(self.runtime)
    def tearDown(self):
        api._bind(None)
    def test_chords_and_nonblocking(self):
        pyChanga.piano([60, 64, 67], 0.7, 0.5, block=False)
        self.assertEqual(self.runtime.calls, [("note", "piano", [60, 64, 67], 0.7, 0.5, False)])
    def test_run_is_exported_and_forwards_function_and_arguments(self):
        namespace = {}
        exec('from pyChanga import *', namespace)
        def melody(note, volume=0.5):
            pass
        self.assertEqual(namespace['run'](melody, 60, volume=.7), 'melody1')
        self.assertEqual(self.runtime.calls, [('run', melody, (60,), {'volume': .7})])
    def test_run_rejects_values_without_a_function_name(self):
        for value in [None, 'melody', 42, lambda: None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                pyChanga.run(value)
        self.assertEqual(self.runtime.calls, [])
    def test_validation(self):
        for args in [(60.5, 0.5, 1), (128, 0.5, 1), (60, 2, 1), (60, 0.5, 0), (60, float('nan'), 1), ([], 0.5, 1)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                pyChanga.piano(*args)
    def test_drum_rest_duration_and_mapping(self):
        pyChanga.drumSeq("kshctom-", 0.75)
        self.assertEqual(self.runtime.calls, [
            ("note", "drums", [pitch], 0.7, 0.75, True)
            for pitch in [36, 37, 48, 65, 55, 68, 50]
        ] + [("wait", 0.75)])
    def test_chip_rest_duration_and_mapping(self):
        pyChanga.chipSeq("kshctom-", 0.5)
        self.assertEqual(self.runtime.calls, [
            ("note", "chip", [pitch], 0.7, 0.5, True)
            for pitch in [60, 62, 63, 65, 64, 67, 66]
        ] + [("wait", 0.5)])
    def test_sequences_validate_before_playing(self):
        for sequence in [pyChanga.drumSeq, pyChanga.chipSeq]:
            for pattern, duration in [("kx", .25), (None, .25), ("k", 0), ("k", -.25), ("k", float('nan'))]:
                with self.subTest(sequence=sequence.__name__, pattern=pattern, duration=duration):
                    with self.assertRaises(ValueError):
                        sequence(pattern, duration)
                    self.assertEqual(self.runtime.calls, [])
    def test_all_instruments_and_sequencers_are_exported(self):
        namespace = {}
        exec('from pyChanga import *', namespace)
        instruments = ['piano', 'rhodes', 'epiano', 'cbass', 'drums', 'chip', 'bass', 'vibra',
                       'marimba', 'b3', 'organ', 'sh2000', 'arp', 'ether', 'violin',
                       'viola', 'cello', 'strings', 'oboe', 'clarinet', 'sub']
        for name in instruments:
            with self.subTest(instrument=name):
                namespace[f'set_{name}']()
                namespace[name](60, .5, .25)
                self.assertEqual(self.runtime.calls[-1], ('note', name, [60], .5, .25, True))
        self.assertIs(namespace['chipSeq'], api.chipSeq)
        self.assertIs(namespace['drumSeq'], api.drumSeq)
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
        with patch('pyChanga.session.DefaultRuntime', return_value=self.runtime) as create:
            self.assertEqual(pyChanga.major_scale(60)[0], 60)
            self.assertEqual(pyChanga.status()['launchMode'], 'beat')
            pyChanga.stop_all()
            create.assert_not_called()
            pyChanga.piano(60, 1, 1)
            create.assert_called_once()
        self.assertEqual(self.runtime.calls, [("note", "piano", [60], 1.0, 1.0, True)])

    def test_session_controls_forward_to_the_runtime(self):
        pyChanga.start_immediate()
        pyChanga.start_on_bar()
        pyChanga.start_on_beat()
        pyChanga.stop("melody1")
        pyChanga.stop_all()
        self.assertEqual(pyChanga.status(), {"launchMode": "beat"})
        self.assertEqual(self.runtime.calls, [("launch_mode", "immediate"), ("launch_mode", "bar"),
                                              ("launch_mode", "beat"), ("stop", "melody1"),
                                              ("stop_all",), ("status",)])


class SectionTests(unittest.TestCase):
    source = '# %% setup\nfrom pyChanga import *\nx = 60\n\n# %% melody\nwhile True:\n    piano(x, 0.7, 1)\n\n# %% bass\ncbass(36, 0.8, 2)\n'
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
    def test_all_is_a_launcher_separate_from_musical_parts(self):
        source = self.source + '# %% all\n# Start the whole composition.\n'
        doc = parse_document(source)
        self.assertEqual([p.name for p in doc.parts], ['melody', 'bass'])
        self.assertEqual([p.name for p in doc.sections], ['melody', 'bass', 'all'])
        line = doc.launcher.marker_line
        for selection in [
            {'startLine': line, 'endLine': line},
            {'startLine': line, 'endLine': line + 1, 'endColumn': 1},
        ]:
            _, section, _ = execution(source, 'song.py', selection)
            self.assertEqual(section.name, 'all')
        self.assertEqual(execution(source, 'song.py', name='all')[1].name, 'all')
    def test_all_can_precede_setup_and_keeps_error_lines(self):
        source = '# %% all\n# %% setup\nfrom pyChanga import *\nx =\n# %% melody\npiano(60, .5, 1)\n'
        with self.assertRaises(SyntaxError) as caught:
            execution(source, 'song.py', name='all')
        self.assertEqual(caught.exception.lineno, 4)
    def test_all_before_a_part_does_not_capture_its_marker(self):
        source = '# %% all\n# %% melody\npass\n'
        self.assertEqual(execution(source, 'song.py', {'startLine': 2, 'endLine': 2})[1].name, 'melody')
    def test_all_rejects_code_duplicate_markers_and_cross_section_selection(self):
        with self.assertRaisesRegex(ValueError, 'empty or comment-only'):
            parse_document(self.source + '# %% all\npiano(60, .5, 1)\n')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            parse_document(self.source + '# %% all\n# %% all\n')
        with self.assertRaisesRegex(ValueError, 'one musical section'):
            execution('# %% all\n# %% melody\npass\n', 'song.py', {'startLine': 1, 'endLine': 3, 'endColumn': 5})
        with self.assertRaisesRegex(ValueError, 'Add a musical part'):
            parse_document('# %% all\n')


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
