"""
Pianist: A framework for converting AI model responses into functional MIDI files.

This package provides tools for parsing AI-generated music descriptions and converting
them into playable MIDI files, built on top of the music21 library.
"""

__version__ = "0.2.0"

# Re-export music21 core classes for convenience
from music21 import note, chord, scale, tempo, meter, stream

# Our custom parser for AI responses
from .parser import MusicParser

__all__ = [
    # music21 re-exports
    "note",
    "chord", 
    "scale",
    "tempo",
    "meter",
    "stream",
    # Our custom classes
    "MusicParser",
]
