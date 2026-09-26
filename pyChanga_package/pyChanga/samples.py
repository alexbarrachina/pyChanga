"""Portable sample handles and validation. This module never imports Pyo."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from numbers import Real
from pathlib import Path
import wave

MAX_SAMPLE_BYTES = 64 * 1024 * 1024
MAX_CACHE_BYTES = 256 * 1024 * 1024
MAX_VOICES = 256
MAX_SAMPLES = 1024


@dataclass(frozen=True)
class Sample:
    """A serializable sample handle that can also unpack as (sample, length_ms)."""

    path: str
    frames: int
    sample_rate: int
    channels: int
    file_size: int
    modified_ns: int

    @property
    def duration(self):
        return self.frames / self.sample_rate

    @property
    def duration_ms(self):
        return self.frames * 1000 / self.sample_rate

    def __iter__(self):
        yield self
        yield self.duration_ms

    @property
    def key(self):
        return hashlib.sha256(repr(self).encode()).hexdigest()

    def to_dict(self):
        return asdict(self)


def read_sample(path):
    """Read a WAV header without opening audio or copying its samples."""
    path = Path(path).expanduser().resolve()
    stat = path.stat()
    try:
        with wave.open(str(path), "rb") as sound:
            frames, rate, channels = sound.getnframes(), sound.getframerate(), sound.getnchannels()
            if channels not in (1, 2) or frames < 2 or rate <= 0:
                raise ValueError("Samples must be nonempty mono or stereo PCM WAV files")
            if frames * channels * 4 > MAX_SAMPLE_BYTES:
                raise ValueError("A sample may use at most 64 MiB of decoded audio")
            # Reject truncated data without reading the entire recording.
            sound.setpos(frames - 1)
            if len(sound.readframes(1)) != channels * sound.getsampwidth():
                raise ValueError("The WAV file is truncated")
    except (wave.Error, EOFError) as error:
        raise ValueError(f"Could not read {path.name}: use a mono or stereo PCM WAV file") from error
    return Sample(str(path), frames, rate, channels, stat.st_size, stat.st_mtime_ns)


def sample_from_dict(value):
    try:
        sample = Sample(**value)
        if not isinstance(sample.path, str) or not Path(sample.path).is_absolute():
            raise ValueError()
        for number in (sample.frames, sample.sample_rate, sample.channels, sample.file_size, sample.modified_ns):
            if type(number) is not int or number < 0:
                raise ValueError()
        if sample.frames < 2 or sample.sample_rate <= 0 or sample.channels not in (1, 2):
            raise ValueError()
        if sample.frames * sample.channels * 4 > MAX_SAMPLE_BYTES:
            raise ValueError()
        return sample
    except (TypeError, ValueError):
        raise ValueError("Invalid sample handle; use load_sample(path)") from None


def number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is out of range")
    return float(value)


def validate_play(sample, volume, duration, start, rate, env, block):
    if not isinstance(sample, Sample):
        raise TypeError("sampl() needs a sample returned by load_sample()")
    volume = number(volume, "Volume", 0, 1)
    duration = number(duration, "Duration", 0)
    rate = number(rate, "Rate")
    if duration == 0 or rate == 0:
        raise ValueError("Duration must be positive and rate must be nonzero")
    if not isinstance(block, bool):
        raise TypeError("block must be True or False")
    last_frame = (sample.frames - 1) / sample.sample_rate
    start = (0.0 if rate > 0 else last_frame) if start is None else number(start, "Start", 0)
    if start >= sample.duration:
        raise ValueError("Start must be before the end of the sample (in seconds)")
    if env is not None:
        if not isinstance(env, (list, tuple)) or not 2 <= len(env) <= 128:
            raise ValueError("env needs 2 to 128 amplitude points between 0 and 1")
        env = tuple(number(value, "Envelope amplitude", 0, 1) for value in env)
    return volume, duration, start, rate, env, block


def envelope_points(transport, start, end, env):
    """Absolute seconds/amplitude pairs, including tempo changes between points."""
    values = env or (1.0, 1.0)
    beats = {start + (end - start) * i / (len(values) - 1) for i in range(len(values))}
    beats.update(s.beat for s in transport.segments if start < s.beat < end)
    result = []
    for beat in sorted(beats):
        position = min(len(values) - 1, (beat - start) / (end - start) * (len(values) - 1))
        index = min(int(position), len(values) - 2)
        value = values[index] + (values[index + 1] - values[index]) * (position - index)
        result.append((transport.time_at(beat), value))
    return result
