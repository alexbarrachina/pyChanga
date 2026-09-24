"""Audio readiness must require samples, not merely an open device handle."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pyChanga_package'))
from pyChanga.audio import AudioError, FluidSynthBackend


class AudioStartupTests(unittest.TestCase):
    def setUp(self):
        self.elapsed = 0
        self.selected = None
        self.opened = []
        self.working = {'portaudio'}
        self.audio = FluidSynthBackend.__new__(FluidSynthBackend)
        self.audio.settings = self.audio.synth = self.audio.seq = object()
        self.audio.driver = None
        self.audio.fluid_settings_setstr = self.select_driver
        self.audio.new_fluid_audio_driver = self.open_driver
        self.audio.delete_fluid_audio_driver = Mock()
        self.audio.fluid_sequencer_get_tick = lambda _: int(self.elapsed * 1000) if self.selected in self.working else 0
        for target, value in [('sys.platform', 'darwin'), ('time.monotonic', lambda: self.elapsed),
                              ('time.sleep', self.advance)]:
            patcher = patch('pyChanga.audio.' + target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def select_driver(self, settings, key, value):
        self.selected = value.decode()
        return 0

    def open_driver(self, settings, synth):
        self.opened.append(self.selected)
        return self.selected

    def advance(self, seconds):
        self.elapsed += seconds

    def test_stalled_coreaudio_falls_back_to_working_portaudio(self):
        self.audio._start_audio_driver(None)
        self.assertEqual(self.opened, ['coreaudio', 'portaudio'])
        self.assertEqual(self.audio.driver, 'portaudio')
        self.audio.delete_fluid_audio_driver.assert_called_once_with('coreaudio')

    def test_working_coreaudio_is_kept(self):
        self.working.add('coreaudio')
        self.audio._start_audio_driver(None)
        self.assertEqual(self.opened, ['coreaudio'])
        self.audio.delete_fluid_audio_driver.assert_not_called()

    def test_no_working_driver_reports_failure_and_closes_devices(self):
        self.working.clear()
        with self.assertRaisesRegex(AudioError, 'Restart audio'):
            self.audio._start_audio_driver(None)
        self.assertIsNone(self.audio.driver)
        self.assertEqual(self.audio.delete_fluid_audio_driver.call_count, 2)

    def test_explicit_driver_does_not_switch_outputs(self):
        with self.assertRaises(AudioError):
            self.audio._start_audio_driver('coreaudio')
        self.assertEqual(self.opened, ['coreaudio'])

    def test_unavailable_coreaudio_can_use_portaudio(self):
        self.audio.new_fluid_audio_driver = lambda *_: None if self.selected == 'coreaudio' else self.open_driver(None, None)
        self.audio._start_audio_driver(None)
        self.assertEqual(self.audio.driver, 'portaudio')
        self.audio.delete_fluid_audio_driver.assert_not_called()


if __name__ == '__main__':
    unittest.main()
