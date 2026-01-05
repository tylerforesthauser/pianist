"""
Pianist: A framework for converting AI model responses into functional MIDI files.

This package provides tools for parsing AI-generated music descriptions and converting
them into playable MIDI files, supporting music theory concepts and classical composition forms.
"""

__version__ = "0.1.0"

from .music_theory import Note, Scale, Chord, TimeSignature, Tempo
from .composition import Motif, Phrase, Section, Composition
from .midi_generator import MIDIGenerator
from .parser import MusicParser

__all__ = [
    "Note",
    "Scale", 
    "Chord",
    "TimeSignature",
    "Tempo",
    "Motif",
    "Phrase",
    "Section",
    "Composition",
    "MIDIGenerator",
    "MusicParser",
]
