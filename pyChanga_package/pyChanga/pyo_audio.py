"""Pyo implementation, used only inside the optional sampler process.

Each voice has a file-position ramp, an amplitude envelope and a short safety
fade. Pyo computes all three in its native callback; Python only schedules them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
import time

from .samples import MAX_CACHE_BYTES, MAX_VOICES, read_sample

FADE = 0.003


def value_at(points, at):
    if at <= points[0][0]:
        return points[0][1]
    for (left, a), (right, b) in zip(points, points[1:]):
        if at <= right:
            return a + (b - a) * (at - left) / (right - left)
    return points[-1][1]


@dataclass
class SampleVoice:
    owner: str
    at: float
    source_end: float
    end: float
    volume: float
    position: object
    reader: object
    output: object
    controls: list = field(default_factory=list)


class PyoAudio:
    def __init__(self, audio=None):
        try:
            import pyo
        except ModuleNotFoundError as error:
            if error.name == "pyo":
                raise RuntimeError('The sampler needs Pyo. Install "pyChanga[sampler]" or use the bundled IDE. '
                                   'See the sampler installation instructions for supported Python versions.') from error
            raise RuntimeError(f"Pyo could not load a dependency: {error}") from error
        except (ImportError, OSError) as error:
            raise RuntimeError(f"Pyo is installed but its native libraries could not load: {error}") from error
        self.pyo = pyo
        self.tables, self.voices = {}, {}
        self.cache_bytes = 0
        self.manual = audio == "manual"
        self.server = pyo.Server(sr=48000, nchnls=2, buffersize=128, duplex=0,
                                 audio=audio or os.environ.get("PYCHANGA_PYO_AUDIO", "portaudio"),
                                 winhost="wasapi")
        try:
            self.server.setVerbosity(0)
            self.server.deactivateMidi()
            self.server.boot()
            if not self.server.getIsBooted():
                raise RuntimeError("Could not open the sampler audio output")
            self.server.start()
            if not self.manual:
                initial = self.server.getCurrentTimeInSamples()
                deadline = time.monotonic() + 2
                while self.server.getCurrentTimeInSamples() == initial:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("The sampler audio output is not advancing; check your output device")
                    time.sleep(.01)
        except BaseException:
            self.server.shutdown()
            raise

    def now(self):
        return self.server.getCurrentTimeInSamples() / self.server.getSamplingRate() if self.manual else time.monotonic()

    def load(self, sample):
        if sample.key in self.tables:
            return
        if read_sample(sample.path) != sample:
            raise ValueError("The sample file changed; call load_sample() again")
        size = sample.frames * sample.channels * 4
        if self.cache_bytes + size > MAX_CACHE_BYTES:
            raise ValueError("The sample cache is full (256 MiB); restart playback to clear it")
        table = self.pyo.SndTable(sample.path)
        if table.getSize() != sample.frames or len(table) != sample.channels:
            raise ValueError("Could not decode the complete WAV file")
        self.tables[sample.key] = table
        self.cache_bytes += size

    def _line(self, points, at, line=None):
        """Start a native ramp at a future deadline, or resume an active ramp."""
        now = self.now()
        begin = max(now, at)
        clipped = [(0.0, value_at(points, begin))]
        clipped += [(when - begin, value) for when, value in points if when > begin]
        if len(clipped) == 1:
            clipped.append((1 / 48000, clipped[0][1]))
        if line is None:
            line = self.pyo.Linseg(clipped, loop=False, initToFirstVal=True)
        else:
            line.setList(clipped)
        line.play(delay=max(0.0, begin - now))
        return line

    def play(self, identity, owner, sample, volume, offset, rate, at, end, points):
        if identity in self.voices:
            return
        self.reap()
        if len(self.voices) >= MAX_VOICES:
            raise RuntimeError("At most 256 sample voices can overlap; use shorter grains or add wait()")
        table = self.tables[sample.key]
        last = (sample.frames - 1) / sample.sample_rate
        offset = min(offset, last)
        source_duration = ((sample.duration - offset) if rate > 0 else (offset + 1 / sample.sample_rate)) / abs(rate)
        source_end = at + source_duration
        if min(source_end, end) <= self.now():
            return
        # Hold the last valid frame instead of wrapping the table at its edge.
        travel = abs((last if rate > 0 else 0) - offset) / abs(rate)
        position = self._line([(at, offset / sample.duration),
                               (at + max(travel, 1 / 48000), (last if rate > 0 else 0) / sample.duration)], at)
        reader = self.pyo.Pointer2(table, position, interp=2, autosmooth=False).stop()
        voice = SampleVoice(owner, at, source_end, min(end, source_end), volume, position, reader, None)
        self.voices[identity] = voice
        self.update(identity, end, points)
        delay = max(0.0, at - self.now())
        reader.play(delay=delay)
        voice.output.out(delay=delay)

    def update(self, identity, end, points):
        voice = self.voices.get(identity)
        if voice is None:
            return
        voice.end = min(end, voice.source_end)
        if voice.end <= self.now():
            self._stop(identity)
            return
        duration = voice.end - voice.at
        fade = min(FADE, duration / 3)
        safety = [(voice.at, 0), (voice.at + fade, 1), (voice.end - fade, 1), (voice.end, 0)]
        if voice.controls:
            self._line(points, voice.at, voice.controls[0])
            self._line(safety, voice.at, voice.controls[1])
        else:
            envelope = self._line(points, voice.at)
            gate = self._line(safety, voice.at)
            gain = envelope * gate * voice.volume
            voice.controls = [envelope, gate, gain]
            # Pyo processes objects in construction order: the output must be
            # created after its controls to avoid a buffer of envelope latency.
            voice.output = self.pyo.Mix(voice.reader, voices=2, mul=gain).stop()

    def _stop(self, identity):
        voice = self.voices.pop(identity)
        for node in [voice.output, voice.reader, voice.position, *voice.controls]:
            if node is not None:
                node.stop()

    def remove_future(self, owner):
        now = self.now()
        for identity, voice in list(self.voices.items()):
            if voice.owner == owner and voice.at > now:
                self._stop(identity)

    def release_owner(self, owner):
        now = self.now()
        for identity, voice in list(self.voices.items()):
            if voice.owner == owner:
                if voice.at > now:
                    self._stop(identity)
                else:
                    # Keep all graph objects alive through the brief release.
                    level = voice.controls[1].get()
                    voice.controls[1].setList([(0, level), (FADE, 0)])
                    voice.controls[1].play()
                    voice.end = now + FADE

    def reap(self):
        # Native envelopes reach zero at the deadline; cleanup may happen later.
        now = self.now() - 2 * self.server.getBufferSize() / self.server.getSamplingRate()
        for identity, voice in list(self.voices.items()):
            if voice.end <= now:
                self._stop(identity)

    def close(self):
        for identity in list(self.voices):
            self._stop(identity)
        self.tables.clear()
        self.server.stop()
        self.server.shutdown()
