"""One disposable interpreter per part. No audio or clock lives here."""
from __future__ import annotations
import io
import linecache
import os
from pathlib import Path
import sys
import time

from . import api
from .errors import error_info
from .function_capture import capture_function, restore_function
from .samples import read_sample


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

    def load_sample(self, path):
        sample = read_sample(path)
        self.request({"type": "sample_load", "sample": sample.to_dict()})
        while not self.request({"type": "sample_ready", "sample": sample.to_dict()})["ready"]:
            time.sleep(.01)
        return sample

    def sample(self, sample, volume, duration, start, rate, env, block):
        if self.preparing:
            raise RuntimeError("Put sampl() in a musical part, not setup. load_sample() belongs in setup.")
        next_cursor = self.cursor + duration if block else self.cursor
        self.request({"type": "sample", "sample": sample.to_dict(), "volume": volume,
                      "duration": duration, "offset": start, "rate": rate, "env": env,
                      "block": block, "cursor": self.cursor, "next": next_cursor})
        self.cursor = next_cursor

    def tempo(self, bpm):
        if self.preparing:
            self.initial_tempo = bpm
        else:
            self.request({"type": "tempo", "bpm": bpm, "cursor": self.cursor})

    def run(self, function, args, kwargs):
        if self.preparing:
            raise RuntimeError("Put run() in a musical part, not setup")
        function_payload = capture_function(function, args, kwargs)
        reply = self.request({"type": "run", "name": function.__name__, "function": function_payload,
                              "line": getattr(getattr(function, "__code__", None), "co_firstlineno", 1),
                              "cursor": self.cursor})
        return reply["name"]

    def launch_mode(self, mode):
        self.request({"type": "launch_mode", "mode": mode})

    def stop(self, part):
        self.request({"type": "stop", "partId": part})

    def stop_all(self):
        self.request({"type": "stop_all"})

    def status(self):
        return self.request({"type": "status"})["status"]


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


def run_worker(connection, payload):
    filename = payload.get("filename", "<worker>")
    runtime = PartRuntime(connection)
    phase = "setup"
    try:
        # Keep os.write(), extension modules and subprocess output off the
        # service's JSON protocol pipe. Ordinary print() uses the private pipe.
        null = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(null, 1)
            os.dup2(null, 2)
        finally:
            # A spawned worker may start with fd 1 or 2 closed. In that case
            # opening the null device occupies that fd, so closing it here
            # would undo the redirection.
            if null not in (1, 2):
                os.close(null)
        api._bind(runtime)
        sys.stdout, sys.stderr = Output(runtime, "stdout"), Output(runtime, "stderr")
        sys.stdin = io.StringIO("")
        source = payload["source"]
        linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)
        directory = Path(filename).parent
        if directory.is_dir():
            os.chdir(directory)
            sys.path.insert(0, str(directory.resolve()))
        namespace = {"__name__": "__main__", "__file__": filename, "__builtins__": __builtins__}
        if "function" in payload:
            function, args, kwargs = restore_function(payload["function"])
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
