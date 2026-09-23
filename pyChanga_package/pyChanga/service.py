"""Version 1 JSON-lines desktop protocol. Student output never uses this pipe."""
from __future__ import annotations
import json
import queue
import sys
import threading
import time

from .audio import FluidSynthBackend, RecordingBackend
from .engine import Engine


def serve(silent=False):
    incoming = queue.Queue(maxsize=128)
    outgoing = queue.Queue(maxsize=512)
    disconnected = threading.Event()

    def emit(event):
        try:
            outgoing.put_nowait(event)
        except queue.Full:
            if event["type"] not in ("output", "status"):
                disconnected.set()  # A disconnected/unresponsive editor must not leave music running.

    def writer():
        while True:
            event = outgoing.get()
            if event is None:
                return
            try:
                sys.stdout.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
                sys.stdout.flush()
            except (OSError, BrokenPipeError):
                disconnected.set()
                return

    def reader():
        while True:
            line = sys.stdin.readline(2_000_001)
            if not line:
                disconnected.set()
                return
            try:
                if len(line) > 2_000_000 or not line.endswith("\n"):
                    raise ValueError("Protocol message is too large")
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError("Protocol messages must be objects")
                incoming.put(request)
            except (ValueError, json.JSONDecodeError) as error:
                emit({"version": 1, "type": "error", "message": str(error)})

    writer_thread = threading.Thread(target=writer, daemon=True)
    writer_thread.start()
    try:
        backend = RecordingBackend() if silent else FluidSynthBackend()
    except Exception as error:
        emit({"version": 1, "type": "fatal", "message": str(error)})
        outgoing.put(None)
        writer_thread.join(timeout=2)
        return 1
    engine = Engine(backend, emit)
    threading.Thread(target=reader, daemon=True).start()
    emit({"version": 1, "type": "ready", "audio": "silent" if silent else "fluidsynth", "lookaheadMs": 100})
    try:
        while not disconnected.is_set() and not engine.closed:
            # Bound editor traffic so a stream of commands cannot starve scheduling.
            for _ in range(8):
                try:
                    engine.command(incoming.get_nowait())
                except queue.Empty:
                    break
                if engine.closed:
                    break
            engine.tick()
            time.sleep(0.002)
    finally:
        engine.close()
        try:
            outgoing.put(None, timeout=0.2)
            writer_thread.join(timeout=1)
        except queue.Full:
            pass
    return 0
