"""The client adapter must preserve the engine's behavior and source errors."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pyChanga_package"))
from pyChanga.audio import RecordingBackend
from pyChanga.engine import Engine
from pyChanga.protocol import handle_command


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.engine = Engine(RecordingBackend(), self.events.append)
        self.addCleanup(self.engine.close)

    def command(self, kind, **fields):
        return handle_command(self.engine, {
            "version": 1, "type": kind, "requestId": "test-request", **fields,
        })

    def test_parse_exposes_launcher_without_starting_playback(self):
        result = self.command("parse", source="# %% melody\npass\n# %% bass\npass\n# %% all\n")
        self.assertTrue(result["ok"])
        self.assertEqual(result["requestId"], "test-request")
        parts = result["result"]["parts"]
        self.assertEqual([(part["name"], part["kind"]) for part in parts], [
            ("melody", "part"), ("bass", "part"), ("all", "all"),
        ])
        self.assertEqual([part["markerLine"] for part in parts], [1, 3, 5])
        self.assertFalse(self.engine.active)

    def test_invalid_commands_leave_the_runtime_usable(self):
        for request in [
            {"version": 99, "type": "shutdown"},
            {"version": 1, "type": "unknown"},
            {"version": 1, "type": "tempo", "bpm": -1},
        ]:
            with self.subTest(request=request):
                response = handle_command(self.engine, request)
                self.assertFalse(response["ok"])
                self.assertIn("ValueError", response["error"]["message"])
                self.assertFalse(self.engine.closed)
        self.assertEqual(self.command("status")["result"]["bpm"], 60)
        self.assertTrue(self.command("tempo", bpm=120)["ok"])
        self.assertEqual(self.command("status")["result"]["pendingTempo"]["bpm"], 120)

    def test_run_error_preserves_source_location_and_request(self):
        result = self.command("run", source="# %% melody\nx =\n", filename="song.py")
        self.assertFalse(result["ok"])
        self.assertEqual(result["requestId"], "test-request")
        self.assertEqual(result["error"]["filename"], "song.py")
        self.assertEqual(result["error"]["line"], 2)
        self.assertFalse(self.engine.active)


if __name__ == "__main__":
    unittest.main()
