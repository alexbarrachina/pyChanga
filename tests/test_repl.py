"""Exercise ordinary Python entry points against the real silent service."""
from pathlib import Path
import os
import signal
import subprocess
import sys
import tempfile
from textwrap import dedent
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "pyChanga_package"), "PYCHANGA_SILENT": "1"}


class ReplTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "POSIX SIGINT is needed for this subprocess check")
    def test_plain_script_interrupt_stops_playback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "loop.py"
            path.write_text('from pyChanga import *\nwhile True: piano(60,.5,.1)\n')
            process = subprocess.Popen([sys.executable, str(path)], env=ENV,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                time.sleep(.3)
                process.send_signal(signal.SIGINT)
                _, errors = process.communicate(timeout=5)
                self.assertIn("KeyboardInterrupt", errors)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    @unittest.skipIf(os.name == "nt", "POSIX SIGINT is needed for this subprocess check")
    def test_interrupt_stops_a_script_waiting_for_its_launched_part(self):
        source = ('from pyChanga import *\n'
                  'def melody():\n    while True: piano(64,.5,.1)\n'
                  'run(melody)\nprint("running", flush=True)\n')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "loop.py"
            path.write_text(source)
            process = subprocess.Popen([sys.executable, str(path)], env=ENV,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(process.stdout.readline().strip(), "running")
                time.sleep(.2)
                process.send_signal(signal.SIGINT)
                process.communicate(timeout=5)
                self.assertIsNotNone(process.returncode)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    def test_repl_launch_modes_and_fast_loop_backpressure(self):
        source = ('from pyChanga import *\nimport time\n'
                  'def melody():\n    piano(64,.5,.05)\n'
                  'for setter in (start_on_bar, start_on_beat, start_immediate):\n'
                  '    setter()\n'
                  '    name=run(melody)\n'
                  '    for _ in range(100):\n'
                  '        part=next(p for p in status()["parts"] if p["name"]==name)\n'
                  '        if part["pending"] and part["pending"]["beat"] is not None: break\n'
                  '        if part["state"]=="finished": break\n'
                  '        time.sleep(.01)\n'
                  '    print(status()["launchMode"], part["pending"]["beat"] if part["pending"] else "done")\n'
                  '    stop(name)\n'
                  'begin=time.monotonic()\n'
                  'for _ in range(30): piano(60,.5,.1)\n'
                  'print("loop",round(time.monotonic()-begin,1),status()["directNotes"])\n'
                  'stop_all()\n')
        result = subprocess.run([sys.executable, "-c", source], env=ENV,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bar 4", result.stdout)
        self.assertIn("beat 1", result.stdout)
        self.assertIn("immediate", result.stdout)
        loop = next(line for line in result.stdout.splitlines() if line.startswith("loop "))
        self.assertGreater(float(loop.split()[1]), .5)
        self.assertLessEqual(int(loop.split()[2]), 1024)

    def test_plain_script_drains_its_notes_and_launched_part(self):
        source = ('from pyChanga import *\n'
                  'start_immediate()\n'
                  'def melody():\n'
                  '    print("from launched part")\n'
                  '    piano(64, .5, .15)\n'
                  'print(run(melody))\n'
                  'piano(60, .5, .15)\n')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "song.py"
            path.write_text(source)
            started = time.monotonic()
            result = subprocess.run([sys.executable, str(path)], env=ENV,
                                    capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("melody1", result.stdout)
        self.assertIn("from launched part", result.stdout)
        self.assertGreater(time.monotonic() - started, .15)

    def test_interactive_function_capture_errors_controls_and_cleanup(self):
        # Blank lines finish each function definition at the Python prompt.
        commands = dedent('''\
            from pyChanga import *
            import time
            start_immediate()
            def melody():
                print("original")
                piano(60, .5, .1)

            name = run(melody)
            def melody():
                print("replacement")

            def failing():
                raise ValueError("part failed")

            run(failing)
            time.sleep(.5)
            print(name, status()["launchMode"])
            stop(name)
            stop_all()
            exit()
        ''')
        result = subprocess.run([sys.executable, "-i", "-q"], input=commands,
                                env=ENV, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("original", result.stdout)
        self.assertNotIn("replacement", result.stdout)
        self.assertIn("melody1 immediate", result.stdout)
        self.assertIn("part failed", result.stderr)

    def test_interrupted_script_closes_with_legacy_exception_state(self):
        source = dedent('''\
            from pyChanga import *
            import atexit
            import sys

            def melody():
                while True:
                    piano(60, .5, .1)

            def use_legacy_exception_state():
                # Reproduce the shutdown state of Python versions before last_exc.
                sys.last_value = KeyboardInterrupt()
                sys.__dict__.pop("last_exc", None)

            run(melody)
            atexit.register(use_legacy_exception_state)
            raise KeyboardInterrupt
        ''')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "interrupted.py"
            path.write_text(source)
            result = subprocess.run([sys.executable, str(path)], env=ENV,
                                    capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KeyboardInterrupt", result.stderr)
