"""The synchronous teaching API. Importing it never opens audio."""
from __future__ import annotations
from math import isfinite
from numbers import Real
from threading import Lock
from typing import Protocol
from .instruments import PROGRAMS
from .scales import Scale, major_scale, natural_minor_scale, pentatonic_scale, pentatonic_minor_scale
from .samples import Sample, validate_play


class Runtime(Protocol):
    """Execution context used by musical commands; independent of any editor."""

    def note(self, instrument: str, pitches: list[int], volume: float, duration: float, block: bool) -> None: ...
    def load_sample(self, path) -> Sample: ...
    def sample(self, sample: Sample, volume, duration, start, rate, env, block) -> None: ...
    def wait(self, beats: float) -> None: ...
    def tempo(self, bpm: float) -> None: ...
    def run(self, function, args: tuple, kwargs: dict) -> str | None: ...
    def launch_mode(self, mode: str) -> None: ...
    def stop(self, part: str) -> None: ...
    def stop_all(self) -> None: ...
    def status(self) -> dict: ...


_runtime: Runtime | None = None
_runtime_lock = Lock()


def _bind(runtime: Runtime | None) -> None:
    """Attach this interpreter's runtime. Each worker has its own binding."""
    global _runtime
    _runtime = runtime


def _number(value: Real, name: str, minimum: float, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value < minimum or (maximum is not None and value > maximum):
        interval = f"{minimum} to {maximum}" if maximum is not None else f"at least {minimum}"
        raise ValueError(f"{name} must be {interval}")
    return float(value)


def _context() -> Runtime:
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:
                from .session import DefaultRuntime
                _runtime = DefaultRuntime()
    return _runtime


def start_immediate() -> None:
    """Launch subsequent parts as soon as they are ready."""
    _context().launch_mode("immediate")


def start_on_beat() -> None:
    """Launch subsequent parts on the next beat."""
    _context().launch_mode("beat")


def start_on_bar() -> None:
    """Launch subsequent parts on the next four-beat bar."""
    _context().launch_mode("bar")


def stop(part: str) -> None:
    """Stop a launched part by its returned name or full part ID."""
    if _runtime is not None:
        _runtime.stop(part)


def stop_all() -> None:
    """Stop every part and all directly queued notes."""
    if _runtime is not None:
        _runtime.stop_all()


def status() -> dict:
    """Return the shared clock, launch mode, and part states."""
    if _runtime is None:
        return {"beat": 0.0, "bpm": 60.0, "launchMode": "beat", "directNotes": 0,
                "directCursor": 0.0, "pendingTempo": None, "parts": []}
    return _runtime.status()


def wait(beats: float) -> None:
    """Advance this part by beats while other parts continue playing."""
    _context().wait(_number(beats, "Beats", 0))


def tempo(bpm: float) -> None:
    """Change the shared tempo on the next available beat (20–400 BPM)."""
    _context().tempo(_number(bpm, "Tempo", 20, 400))


def run(function, *args, **kwargs) -> str | None:
    """Start an independent, numbered instance of a Python function.

    The function receives any supplied arguments. Playback continues without
    advancing the caller's beat cursor. Returns the instance name, or None
    when the 32-part limit prevents launch.
    """
    name = getattr(function, "__name__", None)
    if not callable(function) or not isinstance(name, str) or not name.isidentifier():
        raise ValueError("run() needs a named function, for example run(melody)")
    return _context().run(function, args, kwargs)


def load_sample(path) -> Sample:
    """Load a WAV; unpack the result as (sample, length_ms) if needed.

    Relative paths use the script directory, or the REPL's current directory.
    """
    return _context().load_sample(path)


def sampl(sample, volume, duration, *, start=None, rate=1.0, env=None, block=True) -> None:
    """Play a sample: duration in beats, start in seconds, negative rate reverses.

    An omitted start selects the beginning, or the last frame for reverse
    playback. Envelope points are equally spaced across the duration. Playback
    stops at the file boundary without looping; block=False overlaps voices.
    """
    values = validate_play(sample, volume, duration, start, rate, env, block)
    _context().sample(sample, *values)


def _player(instrument: str):
    def play(note, vol, dur, block=True):
        pitches = list(note) if isinstance(note, (list, tuple)) else [note]
        if not pitches:
            raise ValueError("A chord needs at least one note")
        for pitch in pitches:
            if (
                isinstance(pitch, bool)
                or not isinstance(pitch, Real)
                or not isfinite(pitch)
                or int(pitch) != pitch
                or not 0 <= pitch <= 127
            ):
                raise ValueError("Notes must be whole MIDI pitches from 0 to 127; microtonal pitches are not supported")
        volume = _number(vol, "Volume", 0, 1)
        duration = _number(dur, "Duration", 0)
        if duration == 0:
            raise ValueError("Duration must be greater than zero")
        if not isinstance(block, bool):
            raise TypeError("block must be True or False")
        _context().note(instrument, [int(p) for p in pitches], volume, duration, block)
    play.__name__ = instrument
    play.__qualname__ = instrument
    play.__doc__ = f"Play {instrument}: MIDI note (or chord), volume 0–1, duration in beats."
    return play


def _setup(instrument: str):
    def setup():
        """Compatibility helper. Instruments load automatically when played."""
        return None
    setup.__name__ = f"set_{instrument}"
    return setup


for _name in PROGRAMS:
    globals()[_name] = _player(_name)
    globals()[f"set_{_name}"] = _setup(_name)


def set_drums3():
    """Compatibility helper; uses the bundled pyChanga drum kit."""
    return None


def drumSeq(seq: str, dur: float = 0.25) -> None:
    """Play k=kick, s=snare, h=hi-hat, c=cymbal, t=tom, o=openHat, m=mutedHat, -=rest."""
    mapping = {"k": 36, "s": 37, "h": 48, "c": 65, "t": 55, "o": 68, "m": 50}
    _sequence(seq, dur, drums, mapping, "Drum")


def chipSeq(seq: str, dur: float = 0.25) -> None:
    """Play k=kick, s=snare, h=hi-hat, c=clave, t=tom, o=openHat, m=mutedHat, -=rest."""
    mapping = {"k": 60, "s": 62, "h": 63, "c": 65, "t": 64, "o": 67, "m": 66}
    _sequence(seq, dur, chip, mapping, "Chip")


def _sequence(seq, dur, instrument, mapping, label):
    """Validate the complete pattern before playing its first step."""
    _number(dur, "Duration", 0)
    if dur == 0:
        raise ValueError("Duration must be greater than zero")
    if not isinstance(seq, str) or any(c != "-" and c not in mapping for c in seq):
        raise ValueError(f"{label} sequences use only k, s, h, c, t, o, m and -")
    for character in seq:
        if character == "-":
            wait(dur)
        else:
            instrument(mapping[character], 0.7, dur)


def char2ascii(char):
    """Legacy course helper: test whether a character is alphanumeric."""
    return char.isalnum()


__all__ = [*PROGRAMS, *(f"set_{name}" for name in PROGRAMS), "set_drums3", "wait", "tempo", "run",
           "load_sample", "sampl",
           "start_immediate", "start_on_beat", "start_on_bar", "stop", "stop_all", "status",
           "Scale", "major_scale", "natural_minor_scale", "pentatonic_scale", "pentatonic_minor_scale",
           "drumSeq", "chipSeq", "char2ascii"]
