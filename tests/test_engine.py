import pathlib
import sys
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pyChanga_package"))
from pyChanga.audio import RecordingBackend
from pyChanga.engine import Engine


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.backend = RecordingBackend()
        self.engine = Engine(self.backend, self.events.append)
    def tearDown(self):
        self.engine.close()
    def run_part(self, body, name='melody', setup='from pyChanga import *'):
        return self.engine.run({'source': f'# %% setup\n{setup}\n# %% {name}\n{body}\n',
                                'documentId': 'test', 'filename': str(pathlib.Path('/tmp/música test.py')),
                                'name': name, 'quantization': 'immediate'})
    def until(self, predicate, timeout=4):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.engine.tick()
            if predicate():
                return
            time.sleep(0.002)
        self.fail(f'Timed out: {self.engine.snapshot()}, errors: {[e for e in self.events if e["type"] == "error"]}')
    def test_final_nonblocking_note_drains(self):
        result = self.run_part('piano(60, 0.5, 0.4, block=False)')
        part = self.engine.parts[result['partId']]
        self.until(lambda: any(e['type'] == 'on' for e in self.backend.events))
        self.assertTrue(self.engine.active)
        self.until(lambda: part.state == 'finished')
        notes = [e for e in self.backend.events if e.get('owner') == result['revision']]
        on = next(e for e in notes if e['type'] == 'on')
        off = next(e for e in notes if e['type'] == 'off')
        self.assertAlmostEqual(off['at'] - on['at'], 0.4, places=5)
    def test_setup_and_syntax_errors_keep_old_part(self):
        original = self.run_part('while True:\n    piano(60, 0.5, 0.25)')
        part = self.engine.parts[original['partId']]
        self.until(lambda: part.current is not None)
        with self.assertRaises(SyntaxError):
            self.run_part('if')
        self.assertEqual(part.current.identity, original['revision'])
        self.run_part('piano(72, 0.5, 1)', setup='raise ValueError("bad setup")')
        self.until(lambda: part.error is not None)
        self.assertEqual(part.current.identity, original['revision'])
        self.assertIsNone(part.current.stop)
    def test_busy_loop_can_be_stopped_without_stopping_other_part(self):
        good = self.run_part('while True:\n    piano(60, 0.5, 0.25)', 'good')
        bad = self.run_part('while True:\n    pass', 'busy')
        self.until(lambda: all(p.current is not None for p in self.engine.parts.values()))
        start = time.monotonic()
        self.engine.stop(bad['partId'])
        self.assertLess(time.monotonic() - start, 0.25)
        self.assertIsNotNone(self.engine.parts[good['partId']].current)
        self.until(lambda: not self.engine.reaping)
    def test_replacement_releases_only_old_revision(self):
        old = self.run_part('while True:\n    piano(60, 0.5, 2)')
        other = self.run_part('while True:\n    piano(60, 0.5, 2)', 'other')
        part = self.engine.parts[old['partId']]
        self.until(lambda: part.current is not None)
        new = self.run_part('while True:\n    piano(72, 0.5, 0.25)')
        self.until(lambda: part.current is not None and part.current.identity == new['revision'])
        releases = [e['owner'] for e in self.backend.events if e['type'] == 'release']
        self.assertIn(old['revision'], releases)
        self.assertNotIn(other['revision'], releases)
    def test_runtime_error_is_local_and_has_source_line(self):
        good = self.run_part('while True:\n    wait(1)', 'good')
        bad = self.run_part('wait(0.5)\nraise ValueError("oops")', 'bad')
        self.until(lambda: self.engine.parts[bad['partId']].state == 'error')
        error = self.engine.parts[bad['partId']].error
        self.assertEqual(error['line'], 5)
        self.assertIsNotNone(self.engine.parts[good['partId']].current)
    def test_latest_pending_update_wins(self):
        self.run_part('while True:\n    wait(1)')
        first = self.run_part('while True:\n    piano(65, 0.5, 1)')
        last = self.run_part('while True:\n    piano(72, 0.5, 1)')
        part = self.engine.parts[last['partId']]
        self.until(lambda: part.current is not None)
        self.assertEqual(part.current.identity, last['revision'])
        self.assertFalse(any(e['type'] == 'on' and e['owner'] == first['revision'] for e in self.backend.events))

    def test_tempo_change_retimes_sustained_note_and_worker_wait(self):
        result = self.run_part('piano(60, 0.5, 2)')
        part = self.engine.parts[result['partId']]
        self.until(lambda: part.current is not None)
        ending = part.current.start + 2
        self.engine.set_tempo(120)
        expected = self.engine.transport.time_at(ending)
        self.until(lambda: part.state == 'finished')
        off = next(e for e in self.backend.events if e['type'] == 'off' and e['owner'] == result['revision'])
        self.assertAlmostEqual(off['at'], expected, places=5)


if __name__ == '__main__':
    unittest.main()
