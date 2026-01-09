"""
Pianist: convert AI-generated composition specs into MIDI.
"""

from __future__ import annotations

__all__ = [
    # schema
    "Composition",
    "Event",
    # analysis
    "MidiAnalysis",
    "NoteEvent",
    "PedalEvent",
    "TempoEvent",
    "TimeSignature",
    "Track",
    "__version__",
    "analysis_prompt_template",
    "analyze_midi",
    # iteration helpers
    "composition_from_midi",
    "composition_to_canonical_json",
    "iteration_prompt_template",
    # parsing
    "parse_composition_from_text",
    "transpose_composition",
    "validate_composition_dict",
]

__version__ = "0.1.0"

from .analyze import (
    MidiAnalysis,
    analysis_prompt_template,
    analyze_midi,
)
from .iterate import (
    composition_from_midi,
    composition_to_canonical_json,
    iteration_prompt_template,
    transpose_composition,
)
from .parser import parse_composition_from_text
from .schema import (
    Composition,
    Event,
    NoteEvent,
    PedalEvent,
    TempoEvent,
    TimeSignature,
    Track,
    validate_composition_dict,
)
