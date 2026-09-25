"""Host the playback engine over standard input/output for external clients.

The main thread owns the engine. Reader/writer threads only move messages, so a
slow client cannot block audio scheduling. Worker output uses a separate pipe.
"""
from __future__ import annotations
import json
import queue
import sys
import threading
import time

from .audio import FluidSynthBackend, RecordingBackend
from .engine import Engine, LOOKAHEAD
from .protocol import PROTOCOL_VERSION, handle_command


def serve(silent=False):
    incoming = queue.Queue(maxsize=128)
    outgoing = queue.Queue(maxsize=512)
    disconnected = threading.Event()

    def emit(event):
        try:
            outgoing.put_nowait(event)
        except queue.Full:
            if event["type"] not in ("output", "status"):
                disconnected.set()  # Stop playback when the controlling client disconnects.

    def writer():
        while True:
            event = outgoing.get()
            if event is None:
                return
            try:
                message = {**event, "version": PROTOCOL_VERSION}
                sys.stdout.write(json.dumps(message, ensure_ascii=False, allow_nan=False) + "\n")
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
                emit({"type": "error", "message": str(error)})

    writer_thread = threading.Thread(target=writer, daemon=True)
    writer_thread.start()
    try:
        backend = RecordingBackend() if silent else FluidSynthBackend()
    except Exception as error:
        emit({"type": "fatal", "message": str(error)})
        outgoing.put(None)
        writer_thread.join(timeout=2)
        return 1
    engine = Engine(backend, emit)
    threading.Thread(target=reader, daemon=True).start()
    emit({"type": "ready", "audio": "silent" if silent else "fluidsynth", "lookaheadMs": LOOKAHEAD * 1000})
    try:
        while not disconnected.is_set() and not engine.closed:
            # Bound client traffic so a stream of commands cannot starve scheduling.
            for _ in range(8):
                try:
                    response = handle_command(engine, incoming.get_nowait())
                    emit(response)
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
