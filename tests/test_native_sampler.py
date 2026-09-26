"""Render actual Pyo output without an audio device; optional in base installs."""
import ctypes
import gc
import importlib.util
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pyChanga_package'))
from pyChanga.pyo_audio import PyoAudio
from pyChanga.samples import read_sample


class NativeSamplerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec('pyo') is None:
            if os.environ.get('PYCHANGA_REQUIRE_PYO') == '1':
                raise RuntimeError('The IDE runtime must include Pyo')
            raise unittest.SkipTest('Pyo is an optional dependency')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.audio = PyoAudio(audio='manual')
        self.addCleanup(self.audio.close)
        self.buffer = (ctypes.c_float * 256).from_address(int(self.audio.server.getOutputAddr(), 16))
        self.render(.1)  # Let the server's own initial gain ramp finish.

    def sample(self, kind='ramp', channels=1, rate=8000):
        path = Path(self.directory.name) / f'{kind}-{channels}-{rate}.wav'
        values = []
        for frame in range(rate):
            left = -.75 + 1.5 * frame / rate if kind == 'ramp' else .5
            values += [int(left * 32767)] + ([int(-left * 32767)] if channels == 2 else [])
        with wave.open(str(path), 'wb') as sound:
            sound.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
            sound.writeframes(struct.pack(f'<{len(values)}h', *values))
        sample = read_sample(path)
        self.audio.load(sample)
        return sample

    def render(self, seconds):
        left, right = [], []
        for _ in range(math.ceil(seconds * 48000 / 128)):
            self.audio.server.process()
            left.extend(self.buffer[::2])
            right.extend(self.buffer[1::2])
            self.audio.reap()
        return left, right

    def play(self, sample, *, identity='voice', owner='a', start=0, rate=1, duration=.3, env=None, delay=.02):
        at = self.audio.now() + delay
        values = env or (1, 1)
        points = [(at + duration * i / (len(values) - 1), value) for i, value in enumerate(values)]
        self.audio.play(identity, owner, sample, 1, start, rate, at, at + duration, points)
        return at

    def test_offset_rate_reverse_and_source_sample_rate(self):
        sample = self.sample()
        self.play(sample, start=.2, rate=2)
        left, right = self.render(.15)
        self.assertAlmostEqual(left[4800], -.75 + 1.5 * (.2 + .08 * 2), delta=.025)
        self.assertEqual(left, right)
        self.audio.release_owner('a')
        self.render(.02)
        self.play(sample, identity='reverse', start=.8, rate=-.5)
        left, _ = self.render(.15)
        self.assertAlmostEqual(left[4800], -.75 + 1.5 * (.8 - .08 * .5), delta=.025)

    def test_envelope_and_duration_are_rendered(self):
        self.play(self.sample('constant'), duration=.2, env=(0, 1, 0))
        left, _ = self.render(.3)
        self.assertLess(max(abs(v) for v in left[:800]), .001)
        self.assertAlmostEqual(left[int(.07 * 48000)], .25, delta=.03)
        self.assertAlmostEqual(left[int(.12 * 48000)], .5, delta=.03)
        self.assertLess(max(abs(v) for v in left[int(.23 * 48000):]), .001)
        self.assertFalse(self.audio.voices)

    def test_file_boundaries_do_not_wrap_in_either_direction(self):
        sample = self.sample('constant')
        for index, start, rate in [(0, .95, 1), (1, .05, -1)]:
            self.play(sample, identity=str(index), start=start, rate=rate, duration=.3)
            left, _ = self.render(.15)
            self.assertGreater(max(left), .2)
            self.assertLess(max(abs(v) for v in left[5000:]), .001)

    def test_stereo_and_owner_stop(self):
        sample = self.sample('constant', channels=2, rate=44100)
        self.play(sample, identity='one', owner='one', duration=.4)
        self.play(sample, identity='two', owner='two', duration=.4)
        left, right = self.render(.08)
        self.assertAlmostEqual(left[-1], 1, delta=.02)
        self.assertAlmostEqual(right[-1], -1, delta=.02)
        self.audio.release_owner('one')
        left, right = self.render(.04)
        self.assertAlmostEqual(left[-1], .5, delta=.02)
        self.assertAlmostEqual(right[-1], -.5, delta=.02)

    def test_cancel_future_and_restore_longer_end(self):
        sample = self.sample('constant')
        self.play(sample, duration=.1, delay=.1)
        self.audio.remove_future('a')
        left, _ = self.render(.25)
        self.assertEqual(max(map(abs, left)), 0)
        at = self.play(sample, identity='restored', duration=.1)
        self.render(.05)
        self.audio.update('restored', at + .3, [(at, 1), (at + .3, 1)])
        left, _ = self.render(.15)
        self.assertAlmostEqual(left[-1], .5, delta=.02)

    def test_grain_cleanup_releases_native_streams(self):
        sample = self.sample('constant')
        baseline = self.audio.server.getNumberOfStreams()
        for index in range(40):
            self.play(sample, identity=str(index), duration=.01, delay=.005)
            self.render(.03)
        gc.collect()
        self.assertFalse(self.audio.voices)
        self.assertEqual(self.audio.server.getNumberOfStreams(), baseline)


if __name__ == '__main__':
    unittest.main()
