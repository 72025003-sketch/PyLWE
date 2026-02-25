"""
pylwe
=====

A library for parsing and generating IEC 61162-450 (Lightweight Ethernet) packets.
"""

from .exceptions import LweError, LweParseError, LweTagError, LweChecksumError
from .parser import parse
from .generator import generate

__all__ = [
    "LweError",
    "LweParseError",
    "LweTagError",
    "LweChecksumError",
    "parse",
    "generate",
]

__version__ = "0.1.0"
