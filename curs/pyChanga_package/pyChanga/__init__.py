"""Compatibility bridge: always use the canonical top-level pyChanga package."""
from pathlib import Path as _Path

__path__ = [str(_Path(__file__).resolve().parents[3] / "pyChanga_package" / "pyChanga")]
from .api import *
from .api import __all__
__version__ = "1.0.0"
