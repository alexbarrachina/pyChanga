import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ServiceTests(unittest.TestCase):
    def test_private_output_protocol_and_shutdown(self):
        process = subprocess.Popen([sys.executable, '-m', 'pyChanga', '--service', '--silent'],
            env={**os.environ, 'PYTHONPATH': str(ROOT / 'pyChanga_package')}, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        messages = queue.Queue()
        def read():
            for line in process.stdout:
                try:
                    messages.put(json.loads(line))
                except ValueError:
                    messages.put({'type':'invalid', 'text':line})
        thread = threading.Thread(target=read, daemon=True)
        thread.start()
        try:
            ready = messages.get(timeout=5)
            self.assertEqual(ready['type'], 'ready')
            self.assertEqual(ready['version'], 1)
            source = 'from pyChanga import *\nimport os\nos.write(1, b"not protocol\\n")\nprint("hello")\npiano(60, 0.5, 0.1)\n'
            process.stdin.write(json.dumps({'version':1,'type':'run','requestId':'one','source':source,'quantization':'immediate'})+'\n')
            process.stdin.flush()
            seen_output = False
            seen_response = False
            recent = []
            for _ in range(100):
                event = messages.get(timeout=5)
                recent.append(event)
                recent = recent[-8:]
                self.assertNotEqual(event['type'], 'invalid')
                self.assertEqual(event['version'], 1)
                if event['type'] == 'response':
                    self.assertEqual(event['requestId'], 'one')
                    self.assertTrue(event['ok'])
                    seen_response = True
                if event['type'] == 'output' and 'hello' in event['text']:
                    seen_output = True
                if event['type'] == 'status' and event['parts'] and event['parts'][0]['state'] == 'finished':
                    break
            else:
                self.fail(f'The part did not finish; recent events: {recent}')
            self.assertTrue(seen_output)
            self.assertTrue(seen_response)
            process.stdin.close()
            self.assertEqual(process.wait(timeout=5), 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if not process.stdin.closed:
                process.stdin.close()
            process.stdout.close()
            process.stderr.close()


if __name__ == '__main__':
    unittest.main()
