"""Unbounded scale degrees, including negative indices and bounded slices."""
from dataclasses import dataclass
from numbers import Integral


@dataclass(frozen=True)
class Scale:
    root: int
    intervals: tuple[int, ...]

    def __post_init__(self):
        if isinstance(self.root, bool) or not isinstance(self.root, Integral):
            raise ValueError("A scale root must be a whole MIDI pitch")

    def __getitem__(self, degree):
        if isinstance(degree, slice):
            if degree.stop is None:
                raise ValueError("A scale slice needs an end, for example scale[:8]")
            return [self[i] for i in range(0 if degree.start is None else degree.start,
                                          degree.stop, 1 if degree.step is None else degree.step)]
        if not isinstance(degree, Integral):
            raise TypeError("Scale degrees must be integers")
        octave, index = divmod(degree, len(self.intervals))
        return self.root + 12 * octave + self.intervals[index]


def major_scale(root):
    return Scale(root, (0, 2, 4, 5, 7, 9, 11))


def natural_minor_scale(root):
    return Scale(root, (0, 2, 3, 5, 7, 8, 10))


def pentatonic_scale(root):
    return Scale(root, (0, 2, 4, 7, 9))


def pentatonic_minor_scale(root):
    return Scale(root, (0, 3, 5, 7, 10))
