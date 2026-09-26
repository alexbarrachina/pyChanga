"""One optional sampler process per engine; workers only exchange small handles.

Loading Pyo or a WAV can be slow. Keeping it here lets the conductor continue
scheduling FluidSynth while a part waits for its sample to become ready.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import queue
import time

from .samples import MAX_CACHE_BYTES, MAX_SAMPLES, read_sample


class RecordingSampler:
    """Silent counterpart used by the normal scheduler tests."""

    def __init__(self, clock, events):
        self.clock, self.events = clock, events
        self.samples = {}

    def load(self, sample):
        if sample.key not in self.samples:
            if len(self.samples) >= MAX_SAMPLES:
                raise ValueError("At most 1024 samples can be loaded; restart playback to clear the cache")
            if read_sample(sample.path) != sample:
                raise ValueError("The sample file changed; call load_sample() again")
            if sum(s.frames * s.channels * 4 for s in self.samples.values()) + sample.frames * sample.channels * 4 > MAX_CACHE_BYTES:
                raise ValueError("The sample cache is full (256 MiB); restart playback to clear it")
            self.samples[sample.key] = sample

    def ready(self, sample):
        if self.samples.get(sample.key) != sample:
            raise ValueError("This sample is not loaded in the current session; call load_sample() again")
        return True

    def play(self, identity, owner, sample, volume, offset, rate, at, end, points):
        self.ready(sample)
        self.events.append(dict(type="sample", id=identity, owner=owner, sample=sample,
                                volume=volume, offset=offset, rate=rate, at=at, end=end, points=points))

    def update(self, identity, end, points):
        self.events.append(dict(type="sample_update", id=identity, end=end, points=points, at=self.clock()))

    def remove_future(self, owner):
        now = self.clock()
        self.events[:] = [e for e in self.events if not (e.get("type") == "sample" and e["owner"] == owner and e["at"] > now)]

    def release_owner(self, owner):
        self.remove_future(owner)

    def poll(self):
        return []

    def close(self):
        self.samples.clear()


class SamplerHost:
    def __init__(self, clock):
        self.clock = clock
        self.process = None
        self.samples = {}
        self.errors = []
        self.pending_releases = set()

    def _start(self):
        context = mp.get_context("spawn")
        self.commands, self.replies = context.Queue(2048), context.Queue(2048)
        self.process = context.Process(target=_serve_sampler, args=(self.commands, self.replies),
                                       name="pyChanga sampler", daemon=True)
        # The service makes stdout/stderr non-inheritable. Keep these slots
        # occupied during spawn so queue locks cannot reuse fd 1 or 2. The child
        # redirects them before importing Pyo, and the parent flags are restored.
        streams = [(fd, os.get_inheritable(fd)) for fd in (1, 2)]
        try:
            for fd, _ in streams:
                os.set_inheritable(fd, True)
            self.process.start()
        finally:
            for fd, inherited in streams:
                os.set_inheritable(fd, inherited)

    def _send(self, kind, **fields):
        if not self.process or not self.process.is_alive():
            raise RuntimeError("The sampler stopped; restart playback")
        try:
            self.commands.put_nowait({"type": kind, **fields})
        except queue.Full:
            raise RuntimeError("Too many sampler commands; add wait() between grains") from None

    def load(self, sample):
        if sample.key in self.samples:
            return
        if len(self.samples) >= MAX_SAMPLES:
            raise ValueError("At most 1024 samples can be loaded; restart playback to clear the cache")
        if self.process is None:
            self._start()
        self._send("load", sample=sample)
        self.samples[sample.key] = {"sample": sample, "ready": False, "started": time.monotonic()}

    def ready(self, sample):
        self._receive()
        state = self.samples.get(sample.key)
        if state is None or state["sample"] != sample:
            raise ValueError("This sample is not loaded in the current session; call load_sample() again")
        if state.get("error"):
            raise RuntimeError(state["error"])
        if not self.process.is_alive():
            raise RuntimeError(f"The sampler stopped (exit code {self.process.exitcode}); restart playback")
        if not state["ready"] and time.monotonic() - state["started"] > 30:
            raise RuntimeError("The sampler took too long to load; restart playback")
        return state["ready"]

    def _times(self, end, points):
        # The conductor's clock follows FluidSynth's audio counter. Convert each
        # command to host monotonic time so Pyo does not accumulate clock drift.
        offset = time.monotonic() - self.clock()
        return end + offset, [(at + offset, value) for at, value in points], offset

    def play(self, identity, owner, sample, volume, offset, rate, at, end, points):
        if not self.ready(sample):
            raise RuntimeError("The sample is still loading")
        end, points, shift = self._times(end, points)
        self._send("play", identity=identity, owner=owner, sample=sample, volume=volume,
                   offset=offset, rate=rate, at=at + shift, end=end, points=points)

    def update(self, identity, end, points):
        end, points, _ = self._times(end, points)
        self._send("update", identity=identity, end=end, points=points)

    def remove_future(self, owner):
        if self.process and self.process.is_alive():
            self._send("remove_future", owner=owner)

    def release_owner(self, owner):
        if self.process and self.process.is_alive():
            self.pending_releases.add(owner)
            self._flush_releases()

    def _flush_releases(self):
        # An overloaded queue must not make stop() fail. Retry these few control
        # messages before the next batch of musical events.
        for owner in list(self.pending_releases):
            try:
                self.commands.put_nowait({"type": "release_owner", "owner": owner})
            except queue.Full:
                break
            self.pending_releases.remove(owner)

    def _receive(self):
        if not self.process:
            return
        for _ in range(2048):
            try:
                reply = self.replies.get_nowait()
            except queue.Empty:
                break
            if "key" in reply:
                self.samples[reply["key"]].update(reply)
            else:
                self.errors.append(reply)

    def poll(self):
        self._receive()
        if self.process and self.process.is_alive():
            self._flush_releases()
        errors, self.errors = self.errors, []
        if self.process and not self.process.is_alive() and not getattr(self, "reported_exit", False):
            self.reported_exit = True
            errors.append({"owner": None, "error": f"The sampler stopped (exit code {self.process.exitcode}); restart playback"})
        return errors

    def close(self):
        if self.process is None:
            return
        if self.process.is_alive():
            try:
                self._send("close")
            except RuntimeError:
                pass
            self.process.join(timeout=0.5)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=0.5)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=0.5)
        self.process.close()
        for channel in (self.commands, self.replies):
            channel.cancel_join_thread()
            channel.close()
        self.process = None


def _serve_sampler(commands, replies):
    # Pyo's import banner and native diagnostics must not reach the JSON pipe.
    quiet = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(quiet, 1)
        os.dup2(quiet, 2)
    finally:
        # Service children can start with stdout/stderr closed. In that case
        # opening the null device occupies fd 1 or 2; keep that descriptor open.
        if quiet not in (1, 2):
            os.close(quiet)
    audio = None
    try:
        while True:
            try:
                command = commands.get(timeout=0.005)
            except queue.Empty:
                if audio:
                    audio.reap()
                continue
            kind = command.pop("type")
            if kind == "close":
                break
            try:
                if audio is None:
                    from .pyo_audio import PyoAudio
                    audio = PyoAudio()
                if kind == "load":
                    audio.load(command["sample"])
                    replies.put({"key": command["sample"].key, "ready": True})
                else:
                    getattr(audio, kind)(**command)
                audio.reap()
            except Exception as error:
                if kind == "load":
                    replies.put({"key": command["sample"].key, "error": str(error)})
                else:
                    replies.put({"owner": command.get("owner"), "error": str(error)})
    finally:
        if audio:
            audio.close()
