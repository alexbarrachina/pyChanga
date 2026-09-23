"""Real-time worker soak; use --seconds 600 for the release acceptance run."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pyChanga_package'))
from pyChanga.audio import RecordingBackend
from pyChanga.engine import Engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, default=600)
    args = parser.parse_args()
    warnings = []
    backend = RecordingBackend()
    engine = Engine(backend, lambda e: warnings.append(e) if e['type'] in ('warning', 'error') else None)
    start = time.monotonic()
    try:
        for i in range(8):
            engine.run({'source': f'from pyChanga import *\nwhile True:\n    piano({60+i}, 0.4, 0.25)\n',
                        'filename': f'soak-{i}.py', 'documentId': str(i), 'quantization': 'bar'})
        while time.monotonic() - start < args.seconds:
            engine.tick()
            time.sleep(0.002)
        onsets = [e for e in backend.events if e['type'] == 'on']
        counts = Counter(e['owner'] for e in onsets)
        # Onsets on any quarter-beat must land on the same absolute global grid.
        errors = [abs(e['at'] - engine.transport.time_at(round(engine.transport.beat_at(e['at']) * 4) / 4)) for e in onsets]
        result = {'seconds': round(time.monotonic() - start, 3), 'parts': len(counts),
                  'notes': len(onsets), 'notesPerPart': dict(counts),
                  'maxGridErrorMs': max(errors, default=0) * 1000, 'warnings': warnings}
        Path('test-results').mkdir(exist_ok=True)
        Path('test-results/soak.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return int(len(counts) != 8 or bool(warnings) or max(errors, default=0) > .010)
    finally:
        engine.close()


if __name__ == '__main__':
    raise SystemExit(main())
