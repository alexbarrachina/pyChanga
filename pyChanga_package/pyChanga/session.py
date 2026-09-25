"""Lazy package runtime for an ordinary Python interpreter.

The service owns the clock and audio device. This small client only serializes
commands and forwards worker output, so the REPL uses the same conductor as the
editor and command-line runner.
"""
from __future__ import annotations

import atexit
import base64
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import uuid

from .function_capture import capture_function


class DefaultRuntime:
    """One service connection, created lazily by the public musical API."""

    def __init__(self):
        script = getattr(sys.modules.get("__main__"), "__file__", None)
        self.script_mode = bool(script and not str(script).startswith("<"))
        environment = os.environ.copy()
        package_root = str(Path(__file__).resolve().parents[1])
        environment["PYTHONPATH"] = os.pathsep.join(filter(None, (package_root, environment.get("PYTHONPATH"))))
        command = [sys.executable, "-m", "pyChanga", "--service"]
        if environment.get("PYCHANGA_SILENT") == "1":
            command.append("--silent")
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                        bufsize=1, env=environment)
        self.responses: queue.Queue[dict] = queue.Queue()
        self.lock = threading.Lock()
        self.closed = False
        self.throttle_until = 0.0
        self.reader = threading.Thread(target=self._read, name="pyChanga events", daemon=True)
        self.reader.start()
        try:
            first = self.responses.get(timeout=10)
        except queue.Empty as error:
            self.close()
            raise RuntimeError("pyChanga playback service did not start") from error
        if first.get("type") != "ready":
            self.close()
            raise RuntimeError(first.get("message", "pyChanga playback service did not start"))
        atexit.register(self._at_exit)

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                kind = event.get("type")
                if kind in ("ready", "response", "fatal"):
                    self.responses.put(event)
                elif kind == "output":
                    stream = sys.stderr if event.get("stream") == "stderr" else sys.stdout
                    stream.write(event.get("text", ""))
                    stream.flush()
                elif kind in ("error", "warning"):
                    print(event.get("traceback") or event.get("message", ""), file=sys.stderr, flush=True)
        finally:
            self.responses.put({"type": "fatal", "message": "pyChanga playback service stopped"})

    def _command(self, kind, **fields):
        # Only one caller may write a request and wait for its reply at a time.
        with self.lock:
            if self.closed or self.process.poll() is not None:
                raise RuntimeError("pyChanga playback service is closed")
            request_id = uuid.uuid4().hex
            request = {"version": 1, "requestId": request_id, "type": kind, **fields}
            self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
            while True:
                try:
                    response = self.responses.get(timeout=30)
                except queue.Empty as error:
                    raise RuntimeError("pyChanga playback service did not respond") from error
                if response.get("type") == "fatal":
                    raise RuntimeError(response["message"])
                if response.get("requestId") == request_id:
                    break
            if not response.get("ok"):
                raise RuntimeError(response.get("error", {}).get("message", "pyChanga command failed"))
            return response["result"]

    def _throttle(self):
        # Delay the next note, so queuing the first note returns promptly.
        delay = self.throttle_until - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def note(self, instrument, pitches, volume, duration, block):
        self._throttle()
        while True:
            result = self._command("note", instrument=instrument, pitches=pitches,
                                   volume=volume, duration=duration, block=block)
            if "retryAfter" not in result:
                break
            time.sleep(result["retryAfter"])
        self.throttle_until = time.monotonic() + result["throttle"]

    def wait(self, beats):
        self._throttle()
        result = self._command("wait", beats=beats)
        self.throttle_until = time.monotonic() + result["throttle"]

    def tempo(self, bpm):
        self._command("direct_tempo", bpm=bpm)

    def run(self, function, args, kwargs):
        payload = capture_function(function, args, kwargs)
        code = getattr(function, "__code__", None)
        result = self._command("run_callable", name=function.__name__,
                               function=base64.b64encode(payload).decode("ascii"),
                               filename=code.co_filename if code else "<stdin>",
                               line=code.co_firstlineno if code else 1)
        return result["name"]

    def launch_mode(self, mode):
        self._command("launch_mode", mode=mode)

    def stop(self, part):
        self._command("stop", partId=part)

    def stop_all(self):
        self._command("stop_all")
        self.throttle_until = 0

    def status(self):
        return self._command("status")

    def _at_exit(self):
        # A plain file should keep sounding after its top-level Python returns.
        # An interactive prompt must instead exit immediately on quit().
        # Python 3.11 records an unhandled exception in last_value.
        last_error = getattr(sys, "last_exc", getattr(sys, "last_value", None))
        interrupted = isinstance(last_error, KeyboardInterrupt)
        try:
            if self.script_mode and not interrupted:
                while True:
                    state = self.status()
                    if not state["directNotes"] and not any(p["revision"] or p["pending"] for p in state["parts"]):
                        break
                    time.sleep(0.05)
        except (KeyboardInterrupt, RuntimeError, TimeoutError):
            pass
        finally:
            self.close()

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        self.process.stdout.close()
