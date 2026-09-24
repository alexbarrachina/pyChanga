"""Native PCM checks; skip when the build machine has no FluidSynth installation."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pyChanga_package'))
from pyChanga.audio import AudioError, FluidSynthBackend
from pyChanga.instruments import PROGRAMS


def rms(samples):
    return math.sqrt(sum(x * x for x in samples) / max(1, len(samples)))


class NativeAudioTests(unittest.TestCase):
    def setUp(self):
        try:
            FluidSynthBackend._load_library(None)
        except (AudioError, OSError) as error:
            self.skipTest(str(error))
        # Once the library is available, missing or broken bundled presets must fail.
        self.audio = FluidSynthBackend(audio_driver='offline')
    def tearDown(self):
        if hasattr(self, 'audio'):
            self.audio.close()
    def test_native_timestamp_onset_within_ten_ms(self):
        start = self.audio.now()
        self.audio.note_on('a', 'one', 'piano', 60, .6, start + .100)
        self.audio.note_off('a', 'one', start + .200)
        left, _ = self.audio.render(14400)
        onset = next(index / 48000 for index, sample in enumerate(left) if abs(sample) > .0001)
        self.assertLess(abs(onset - .100), .010)
        self.assertGreater(rms(left[5000:8000]), .001)
    def test_every_bundled_instrument_can_render(self):
        for instrument in PROGRAMS:
            with self.subTest(instrument=instrument):
                pitch = 36 if instrument == 'drums' else 60
                self.audio.note_on(instrument, instrument, instrument, pitch, .7, self.audio.now() + .010)
                left, _ = self.audio.render(24000)
                self.assertGreater(rms(left), .0001)
                self.audio.release_owner(instrument)
    def test_cancel_future_prevents_sound(self):
        self.audio.note_on('a', 'one', 'piano', 60, .6, self.audio.now() + .100)
        self.audio.remove_future('one')
        left, _ = self.audio.render(14400)
        # FluidSynth's effects can contain an inaudible floating-point noise floor.
        self.assertLess(rms(left), 1e-6)
    def test_stop_owner_does_not_silence_identical_pitch(self):
        start = self.audio.now() + .010
        self.audio.note_on('a', 'one', 'organ', 60, .5, start)
        self.audio.note_on('b', 'two', 'organ', 60, .5, start)
        self.audio.render(4800)
        self.audio.release_owner('one')
        left, _ = self.audio.render(4800)
        self.assertGreater(rms(left), .001)
        self.assertIn('b', self.audio.voices)
        self.assertNotIn('a', self.audio.voices)
    def test_overlapping_same_pitch_within_part(self):
        start = self.audio.now() + .010
        self.audio.note_on('a', 'one', 'organ', 60, .5, start)
        self.audio.note_on('b', 'one', 'organ', 60, .5, start)
        self.assertNotEqual(self.audio.voices['a'].channel, self.audio.voices['b'].channel)
        self.audio.note_off('a', 'one', start + .050)
        self.audio.render(4800)
        left, _ = self.audio.render(4800)
        self.assertGreater(rms(left), .001)


if __name__ == '__main__':
    unittest.main()
