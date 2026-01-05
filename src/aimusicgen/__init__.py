"""
aimusicgen

A small framework for converting AI-generated music specifications into MIDI files.
"""

from .schema import Composition
from .parser import parse_composition_from_text
from .midi import render_midi

__all__ = ["Composition", "parse_composition_from_text", "render_midi"]

