"""
Pianist: convert AI-generated composition specs into MIDI.
"""

from __future__ import annotations

__all__ = [
    "__version__",
    # schema
    "Composition",
    "Event",
    "NoteEvent",
    "PedalEvent",
    "TempoEvent",
    "TimeSignature",
    "Track",
    "validate_composition_dict",
    # parsing
    "parse_composition_from_text",
]

__version__ = "0.1.0"

from .schema import (  # noqa: E402
    Composition,
    Event,
    NoteEvent,
    PedalEvent,
    TempoEvent,
    TimeSignature,
    Track,
    validate_composition_dict,
)
from .parser import parse_composition_from_text  # noqa: E402
