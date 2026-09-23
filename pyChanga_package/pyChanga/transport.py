"""Piecewise-linear mapping between absolute beats and monotonic seconds."""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    beat: float
    seconds: float
    bpm: float


class Transport:
    def __init__(self, origin: float, bpm: float = 60):
        self.segments = [Segment(0, origin, bpm)]

    def beat_at(self, seconds: float) -> float:
        segment = next((s for s in reversed(self.segments) if s.seconds <= seconds), self.segments[0])
        return segment.beat + (seconds - segment.seconds) * segment.bpm / 60

    def time_at(self, beat: float) -> float:
        segment = next((s for s in reversed(self.segments) if s.beat <= beat), self.segments[0])
        return segment.seconds + (beat - segment.beat) * 60 / segment.bpm

    def bpm_at(self, seconds: float) -> float:
        return next((s.bpm for s in reversed(self.segments) if s.seconds <= seconds), self.segments[0].bpm)

    def boundary(self, earliest: float, quantum: float) -> float:
        beat = self.beat_at(earliest)
        return beat if quantum == 0 else math.ceil((beat - 1e-10) / quantum) * quantum

    def set_tempo(self, bpm: float, beat: float) -> None:
        if not math.isfinite(bpm) or not 20 <= bpm <= 400:
            raise ValueError("Tempo must be between 20 and 400 BPM")
        seconds = self.time_at(beat)
        self.segments = [s for s in self.segments if s.beat < beat]
        self.segments.append(Segment(beat, seconds, bpm))
