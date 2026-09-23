"""The synchronous teaching API. Importing it never opens audio."""
from __future__ import annotations
from math import isfinite
from numbers import Real
from typing import Protocol
from .instruments import PROGRAMS
from .scales import Scale, major_scale, natural_minor_scale, pentatonic_scale, pentatonic_minor_scale


class Runtime(Protocol):
    def note(self, instrument: str, pitches: list[int], volume: float, duration: float, block: bool) -> None: ...
    def wait(self, beats: float) -> None: ...
    def tempo(self, bpm: float) -> None: ...


_runtime: Runtime | None = None


def _bind(runtime: Runtime | None) -> None:
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
    if _runtime is None:
        raise RuntimeError("Run your code in pyChangaIDE, or use: python -m pyChanga lesson.py")
    return _runtime


def wait(beats: float) -> None:
    """Advance this part by beats while other parts continue playing."""
    _context().wait(_number(beats, "Beats", 0))


def tempo(bpm: float) -> None:
    """Change the shared tempo on the next available beat (20–400 BPM)."""
    _context().tempo(_number(bpm, "Tempo", 20, 400))


def _player(instrument: str):
    def play(note, vol, dur, block=True):
        pitches = list(note) if isinstance(note, (list, tuple)) else [note]
        if not pitches:
            raise ValueError("A chord needs at least one note")
        for pitch in pitches:
            if isinstance(pitch, bool) or not isinstance(pitch, Real) or not isfinite(pitch) or int(pitch) != pitch or not 0 <= pitch <= 127:
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
    """Compatibility helper; uses the bundled General MIDI drum kit."""
    return None


def drumSeq(seq: str, dur: float = 0.25) -> None:
    """Play k=kick, s=snare, h=hi-hat, c=cymbal, t=tom, -=rest."""
    _number(dur, "Duration", 0)
    if dur == 0:
        raise ValueError("Duration must be greater than zero")
    mapping = {"k": 36, "s": 38, "h": 42, "c": 49, "t": 45}
    if not isinstance(seq, str) or any(c not in "kshct-" for c in seq):
        raise ValueError("Drum sequences use only k, s, h, c, t and -")
    for character in seq:
        if character == "-":
            wait(dur)
        else:
            drums(mapping[character], 0.7, dur)


def char2ascii(char):
    """Legacy course helper: test whether a character is alphanumeric."""
    return char.isalnum()


__all__ = [*PROGRAMS, *(f"set_{name}" for name in PROGRAMS), "set_drums3", "wait", "tempo",
           "Scale", "major_scale", "natural_minor_scale", "pentatonic_scale", "pentatonic_minor_scale",
           "drumSeq", "char2ascii"]
