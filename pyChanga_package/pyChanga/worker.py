"""One disposable interpreter per part. No audio or clock lives here."""
from __future__ import annotations
import io
import linecache
import os
from pathlib import Path
import random
import sys
import traceback

from . import api
from ._vendor import cloudpickle


class PartRuntime:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = 0.0
        self.preparing = True
        self.initial_tempo = None

    def request(self, message):
        self.connection.send(message)
        reply = self.connection.recv()
        if reply.get("type") == "error":
            raise RuntimeError(reply["message"])
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

    def run(self, function, args, kwargs):
        if self.preparing:
            raise RuntimeError("Put run() in a musical part, not setup")
        try:
            # Imported helpers such as `from random import randint` are bound
            # to the module's default generator. Keep that generator in the
            # same pickle memo so the child can reseed its captured copy.
            function_payload = cloudpickle.dumps((function, args, kwargs, random.randint.__self__))
        except Exception as error:
            raise ValueError(f"Could not launch {function.__name__}: {error}") from error
        if len(function_payload) > 1_000_000:
            raise ValueError("A launched function and its arguments must fit within 1 MB")
        reply = self.request({"type": "run", "name": function.__name__, "function": function_payload,
                              "line": getattr(getattr(function, "__code__", None), "co_firstlineno", 1),
                              "cursor": self.cursor})
        return reply["name"]


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
        if "function" in payload:
            function, args, kwargs, captured_default_rng = cloudpickle.loads(payload["function"])
            random.seed()
            captured_default_rng.seed()
        else:
            setup = compile(payload["setup"], filename, "exec")
            body = compile(payload["body"], filename, "exec")
            exec(setup, namespace, namespace)
        runtime.request({"type": "ready", "tempo": runtime.initial_tempo})
        runtime.preparing = False
        phase = "runtime"
        if "function" in payload:
            function(*args, **kwargs)
        else:
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
