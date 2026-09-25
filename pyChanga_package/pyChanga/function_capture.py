"""Capture run() calls for independent workers, in the REPL and in parts."""
from __future__ import annotations

import random

from ._vendor import cloudpickle

MAX_FUNCTION_BYTES = 1_000_000


def capture_function(function, args: tuple, kwargs: dict) -> bytes:
    """Freeze a function and its arguments before starting another process."""
    try:
        # Helpers imported from random are bound to its default generator.
        # Include that generator in the same pickle so the worker can reseed
        # its captured copy without changing explicitly seeded Random objects.
        payload = cloudpickle.dumps((function, args, kwargs, random.randint.__self__))
    except Exception as error:
        raise ValueError(f"Could not launch {function.__name__}: {error}") from error
    if len(payload) > MAX_FUNCTION_BYTES:
        raise ValueError("A launched function and its arguments must fit within 1 MB")
    return payload


def restore_function(payload: bytes) -> tuple:
    """Restore a call with an independent default random stream in the worker."""
    function, args, kwargs, captured_default_rng = cloudpickle.loads(payload)
    random.seed()
    captured_default_rng.seed()
    return function, args, kwargs
