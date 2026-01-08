"""Pytest configuration for pianist tests.

This ensures the src directory is in the Python path so tests can import the pianist package.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path
# This is needed because Python 3.14+ may not process .pth files correctly in some cases
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import after path is set up
from pianist.schema import Composition, Track, NoteEvent
from pianist.musical_analysis import MUSIC21_AVAILABLE, _composition_to_music21_stream


@pytest.fixture
def simple_composition() -> Composition:
    """A simple test composition that can be reused across tests."""
    return Composition(
        title="Test",
        bpm=120,
        key_signature="C",
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60, 64, 67], velocity=80),  # C major
                    NoteEvent(start=1, duration=1, pitches=[62, 65, 69], velocity=80),  # D minor
                    NoteEvent(start=2, duration=1, pitches=[64, 67, 71], velocity=80),  # E minor
                    NoteEvent(start=3, duration=1, pitches=[65, 69, 72], velocity=80),  # F major
                ]
            )
        ],
    )


@pytest.fixture
def simple_composition_stream(simple_composition: Composition):
    """Pre-converted music21 stream for simple_composition (cached to avoid re-conversion)."""
    if not MUSIC21_AVAILABLE:
        pytest.skip("music21 not installed")
    try:
        return _composition_to_music21_stream(simple_composition)
    except Exception as e:
        pytest.skip(f"Failed to convert composition to music21 stream: {e}")


@pytest.fixture
def motif_test_composition() -> Composition:
    """A composition designed for motif detection tests."""
    return Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    # Repeating pattern: C-E-G
                    NoteEvent(start=0, duration=0.5, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=0.5, duration=0.5, pitches=[62, 65, 69], velocity=80),
                    NoteEvent(start=1, duration=0.5, pitches=[64, 67, 71], velocity=80),
                    # Repeat the pattern
                    NoteEvent(start=4, duration=0.5, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=4.5, duration=0.5, pitches=[62, 65, 69], velocity=80),
                    NoteEvent(start=5, duration=0.5, pitches=[64, 67, 71], velocity=80),
                ]
            )
        ],
    )


@pytest.fixture
def motif_test_composition_stream(motif_test_composition: Composition):
    """Pre-converted music21 stream for motif_test_composition."""
    if not MUSIC21_AVAILABLE:
        pytest.skip("music21 not installed")
    try:
        return _composition_to_music21_stream(motif_test_composition)
    except Exception as e:
        pytest.skip(f"Failed to convert composition to music21 stream: {e}")

