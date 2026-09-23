"""One disposable interpreter per part. No audio or clock lives here."""
from __future__ import annotations
import io
import linecache
import os
from pathlib import Path
import sys
import traceback

from . import api


class PartRuntime:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = 0.0
        self.preparing = True
        self.initial_tempo = None

    def request(self, message):
        self.connection.send(message)
        reply = self.connection.recv()
        if reply.get("type") != "continue":
            raise SystemExit(0)
        return reply

    def note(self, instrument, pitches, volume, duration, block):
        if self.preparing:
            raise RuntimeError("Put notes in a musical part, not setup. Setup is for imports, variables and functions.")
        next_cursor = self.cursor + duration if block else self.cursor
        self.request({"type": "note", "instrument": instrument, "pitches": pitches,
                      "volume": volume, "duration": duration, "cursor": self.cursor, "next": next_cursor})
        self.cursor = next_cursor

    def wait(self, beats):
        if self.preparing:
            raise RuntimeError("Put waits in a musical part, not setup")
        self.cursor += beats
        self.request({"type": "wait", "next": self.cursor})

    def tempo(self, bpm):
        if self.preparing:
            self.initial_tempo = bpm
        else:
            self.request({"type": "tempo", "bpm": bpm, "cursor": self.cursor})


class Output(io.TextIOBase):
    def __init__(self, runtime, stream):
        self.runtime, self.stream = runtime, stream

    @property
    def encoding(self):
        return "utf-8"

    def writable(self):
        return True

    def write(self, value):
        value = str(value)
        for index in range(0, min(len(value), 16384), 4096):
            self.runtime.request({"type": "output", "stream": self.stream, "text": value[index:index + 4096]})
        return len(value)

    def flush(self):
        pass


def error_info(error, filename):
    frames = traceback.extract_tb(error.__traceback__)
    frame = next((f for f in reversed(frames) if f.filename == filename), None)
    return {"message": f"{type(error).__name__}: {error}", "filename": filename,
            "line": getattr(error, "lineno", None) or (frame.lineno if frame else 1),
            "column": getattr(error, "offset", None) or 1,
            "traceback": "".join(traceback.format_exception(error))[-16000:]}


def run_worker(connection, payload):
    # Keep os.write(), extension modules and subprocess output off the service's
    # JSON protocol pipe. Ordinary print() is forwarded over the private channel.
    with open(os.devnull, "wb") as null:
        os.dup2(null.fileno(), 1)
        os.dup2(null.fileno(), 2)
    runtime = PartRuntime(connection)
    api._bind(runtime)
    sys.stdout, sys.stderr = Output(runtime, "stdout"), Output(runtime, "stderr")
    sys.stdin = io.StringIO("")
    filename = payload["filename"]
    source = payload["source"]
    linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)
    directory = Path(filename).parent
    if directory.is_dir():
        os.chdir(directory)
        sys.path.insert(0, str(directory.resolve()))
    namespace = {"__name__": "__main__", "__file__": filename, "__builtins__": __builtins__}
    phase = "setup"
    try:
        setup = compile(payload["setup"], filename, "exec")
        body = compile(payload["body"], filename, "exec")
        exec(setup, namespace, namespace)
        runtime.request({"type": "ready", "tempo": runtime.initial_tempo})
        runtime.preparing = False
        phase = "runtime"
        exec(body, namespace, namespace)
        connection.send({"type": "done", "cursor": runtime.cursor})
    except SystemExit as error:
        if error.code in (None, 0):
            connection.send({"type": "done", "cursor": runtime.cursor})
        else:
            connection.send({"type": "error", "phase": phase, **error_info(error, filename)})
    except BaseException as error:
        try:
            connection.send({"type": "error", "phase": phase, **error_info(error, filename)})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        api._bind(None)
        connection.close()
