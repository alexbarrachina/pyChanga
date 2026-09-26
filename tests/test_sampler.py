"""Sampler contracts and real worker/REPL scheduling, without requiring Pyo."""
from pathlib import Path
import base64
import os
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pyChanga_package'))
from pyChanga import api
from pyChanga.audio import RecordingBackend
from pyChanga.engine import Engine, SampleNote
from pyChanga.function_capture import capture_function
from pyChanga.samples import read_sample, validate_play, envelope_points
from pyChanga.sampler import SamplerHost
from pyChanga.transport import Transport


def write_wav(path, channels=1, rate=8000, seconds=1):
    with wave.open(str(path), 'wb') as sound:
        sound.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
        sound.writeframes(struct.pack('<h', 4000) * int(rate * seconds) * channels)


class SampleFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'vóice.wav'
        write_wav(self.path)
        self.sample = read_sample(self.path)


class SampleTests(SampleFixture):
    def test_sample_can_be_unpacked_with_its_length_in_milliseconds(self):
        voice, length_ms = self.sample
        self.assertIs(voice, self.sample)
        self.assertEqual(length_ms, 1000)
        self.assertEqual(self.sample.duration_ms, length_ms)

        write_wav(self.path, seconds=.100125)
        _, length_ms = read_sample(self.path)
        self.assertEqual(length_ms, 100.125)

    def test_defaults_reverse_and_custom_start(self):
        self.assertEqual(validate_play(self.sample, .7, 1, None, 1, None, True)[2], 0)
        self.assertAlmostEqual(validate_play(self.sample, .7, 1, None, -1, None, True)[2], 7999 / 8000)
        values = validate_play(self.sample, .7, .5, .4, -.8, [0, 1, 0], False)
        self.assertEqual(values, (.7, .5, .4, -.8, (0., 1., 0.), False))

    def test_validation_happens_before_a_runtime_is_opened(self):
        for kwargs in [dict(rate=0), dict(rate=float('nan')), dict(start=-1), dict(start=1),
                       dict(env=[]), dict(env=[1]), dict(env=[0, 2]), dict(env=[0, True]),
                       dict(env=[0] * 129), dict(block=1)]:
            with self.subTest(kwargs=kwargs), patch.object(api, '_context') as context:
                with self.assertRaises((ValueError, TypeError)):
                    api.sampl(self.sample, .7, 1, **kwargs)
                context.assert_not_called()
        for volume, duration in [(-1, 1), (2, 1), (True, 1), (1, 0), (1, -1), (1, float('inf'))]:
            with self.assertRaises(ValueError):
                api.sampl(self.sample, volume, duration)

    def test_invalid_files_fail_at_loading(self):
        with self.assertRaises(FileNotFoundError):
            read_sample(self.path.with_name('missing.wav'))
        self.path.write_bytes(b'not a WAV')
        with self.assertRaisesRegex(ValueError, 'PCM WAV'):
            read_sample(self.path)
        write_wav(self.path, channels=3)
        with self.assertRaisesRegex(ValueError, 'mono or stereo'):
            read_sample(self.path)
        write_wav(self.path)
        self.path.write_bytes(self.path.read_bytes()[:-2])
        with self.assertRaisesRegex(ValueError, 'truncated'):
            read_sample(self.path)

    def test_envelope_inserts_tempo_breakpoints(self):
        transport = Transport(0)
        transport.set_tempo(120, 1)
        points = envelope_points(transport, 0, 4, (0, 1, 0))
        self.assertEqual(points, [(0, 0), (1, .5), (1.5, 1), (2.5, 0)])

    def test_import_and_fluidsynth_path_do_not_import_pyo(self):
        source = '''
import sys
class NoPyo:
    def find_spec(self, fullname, *args):
        if fullname == 'pyo' or fullname.startswith('pyo.'):
            raise AssertionError('Pyo must remain optional')
sys.meta_path.insert(0, NoPyo())
from pyChanga import *
assert 'pyo' not in sys.modules
assert 'pyChanga.session' not in sys.modules
assert callable(sampl) and callable(load_sample)
from pyChanga.audio import FluidSynthBackend
try:
    audio = FluidSynthBackend(audio_driver='offline')
except RuntimeError:
    pass  # FluidSynth's native library is also optional on test machines.
else:
    audio.note_on('a', 'test', 'piano', 60, .5, audio.now())
    audio.render(256)
    audio.close()
assert 'pyo' not in sys.modules
'''
        result = subprocess.run([sys.executable, '-c', source], capture_output=True, text=True,
                                env={**os.environ, 'PYTHONPATH': str(ROOT / 'pyChanga_package')}, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_pyo_is_local_to_sampler_process(self):
        # A tiny fake module makes this test deterministic even if Pyo is installed.
        missing = Path(self.directory.name) / 'pyo.py'
        missing.write_text('raise ModuleNotFoundError("No module named pyo", name="pyo")\n')
        with patch.object(sys, 'path', [self.directory.name, *sys.path]):
            sampler = SamplerHost(time.monotonic)
            self.addCleanup(sampler.close)
            sampler.load(self.sample)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    sampler.ready(self.sample)
                except RuntimeError as error:
                    self.assertIn('pyChanga[sampler]', str(error))
                    break
                time.sleep(.01)
            else:
                self.fail('Missing Pyo was not reported')
            self.assertTrue(sampler.process.is_alive())

    def test_service_child_preserves_queue_locks_and_hides_pyo_output(self):
        (Path(self.directory.name) / 'pyo.py').write_text(
            'print("PYO IMPORT BANNER", flush=True)\n'
            'raise ModuleNotFoundError("No module named pyo", name="pyo")\n')
        source = f'''
import os, time
from pyChanga.sampler import SamplerHost
from pyChanga.samples import read_sample
os.set_inheritable(1, False)
os.set_inheritable(2, False)
sampler = SamplerHost(time.monotonic)
sample = read_sample({str(self.path)!r})
try:
    sampler.load(sample)
    assert not os.get_inheritable(1) and not os.get_inheritable(2)
    for _ in range(400):
        try:
            sampler.ready(sample)
        except RuntimeError as error:
            assert 'pyChanga[sampler]' in str(error), str(error)
            print('Optional dependency error received')
            break
        time.sleep(.01)
    else:
        raise AssertionError('No sampler response')
finally:
    sampler.close()
'''
        env = {**os.environ, 'PYTHONPATH': os.pathsep.join([self.directory.name, str(ROOT / 'pyChanga_package')])}
        result = subprocess.run([sys.executable, '-c', source], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'Optional dependency error received')


class SampleEngineTests(SampleFixture):
    def setUp(self):
        super().setUp()
        self.events = []
        self.backend = RecordingBackend()
        self.engine = Engine(self.backend, self.events.append)
        self.addCleanup(self.engine.close)
        self.engine.sampler.load(self.sample)

    def until(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.engine.tick()
            if predicate():
                return
            time.sleep(.002)
        self.fail(str(self.events[-8:]))

    def request(self, **kwargs):
        return dict(sample=self.sample.to_dict(), volume=.6, duration=.3, offset=.2, rate=-.8,
                    env=[0, 1, 0], block=False) | kwargs

    def test_direct_samples_share_note_cursor_and_drain(self):
        sample = self.engine.direct_sample(self.request())
        piano = self.engine.direct_note(dict(instrument='piano', pitches=[60], volume=.5, duration=.3, block=True))
        self.assertAlmostEqual(sample['beat'], piano['beat'], delta=.002)
        self.until(lambda: not self.engine.active)
        event = next(e for e in self.backend.events if e['type'] == 'sample')
        self.assertEqual(event['rate'], -.8)
        self.assertAlmostEqual(event['end'] - event['at'], .3)

    def test_failed_sampler_output_keeps_fluidsynth_events_running(self):
        self.engine.direct_sample(self.request())
        self.engine.direct_note(dict(instrument='piano', pitches=[60], volume=.5, duration=.1, block=True))
        with patch.object(self.engine.sampler, 'play', side_effect=RuntimeError('Sampler output failed')):
            self.engine.tick()
        self.assertFalse(self.engine.closed)
        self.assertTrue(any(e['type'] == 'on' for e in self.backend.events))
        self.assertTrue(any(e.get('message') == 'Sampler output failed' for e in self.events))
        self.until(lambda: not self.engine.active)

    def test_worker_setup_relative_paths_run_arguments_and_nonblocking_drain(self):
        source = ('# %% setup\nfrom pyChanga import *\nvoice,length_ms=load_sample("vóice.wav")\n'
                  'def grain(sound):\n    sampl(sound,.5,.3,rate=-1,block=False)\n'
                  '# %% sound\nassert length_ms == 1000\nrun(grain,voice)\nsampl(voice,.5,.3,block=False)\n')
        self.engine.run(dict(source=source, filename=str(self.path.with_suffix('.py')),
                             name='sound', quantization='immediate'))
        self.until(lambda: len([e for e in self.backend.events if e['type'] == 'sample']) == 2)
        self.assertTrue(self.engine.active)
        self.until(lambda: not self.engine.active)
        self.assertFalse([e for e in self.events if e['type'] == 'error'])

    def test_failed_sample_setup_preserves_playing_revision(self):
        source = '# %% setup\nfrom pyChanga import *\n# %% a\nwhile True: piano(60,.5,.1)\n'
        request = dict(source=source, filename=str(self.path.with_suffix('.py')), name='a', quantization='immediate')
        old = self.engine.run(request)
        self.until(lambda: self.engine.parts[old['partId']].current is not None)
        request['source'] = source.replace('from pyChanga import *', 'from pyChanga import *\nload_sample("absent.wav")')
        self.engine.run(request)
        part = self.engine.parts[old['partId']]
        self.until(lambda: part.error is not None)
        self.assertEqual(part.current.identity, old['revision'])
        self.assertIsNone(part.current.stop)

    def test_sample_handles_survive_function_capture_from_repl(self):
        self.engine.set_launch_mode('immediate')
        def grain(sound):
            from pyChanga import sampl
            sampl(sound, .7, .1)
        payload = base64.b64encode(capture_function(grain, (self.sample,), {})).decode()
        self.engine.run_callable(dict(name='grain', function=payload))
        self.until(lambda: not self.engine.active)
        self.assertEqual(len([e for e in self.backend.events if e['type'] == 'sample']), 1)

    def test_live_envelope_is_retimed_without_changing_rate(self):
        request = self.request()
        request['duration'] = 4
        self.engine.direct_sample(request)
        self.engine.tick()
        original = next(e for e in self.backend.events if e['type'] == 'sample')
        self.engine.set_tempo(120)
        update = next(e for e in self.backend.events if e['type'] == 'sample_update')
        self.assertLess(update['end'], original['end'])
        self.assertEqual(original['rate'], -.8)

    def test_plain_script_resolves_beside_file_and_drains_samples(self):
        song = self.path.with_suffix('.py')
        song.write_text('from pyChanga import *\nvoice,length_ms=load_sample("vóice.wav")\n'
                        'sampl(voice,.5,.15,block=False)\nprint("loaded",voice.channels,length_ms)\n')
        result = subprocess.run([sys.executable, str(song)], cwd=ROOT, capture_output=True, text=True,
                                env={**os.environ, 'PYTHONPATH': str(ROOT / 'pyChanga_package'),
                                     'PYCHANGA_SILENT': '1'}, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('loaded 1 1000.0', result.stdout)


if __name__ == '__main__':
    unittest.main()
