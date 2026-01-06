"""
Tests for musical analysis module.
"""

from __future__ import annotations

import pytest

from pianist.schema import Composition, Track, NoteEvent, TempoEvent
from pianist.musical_analysis import (
    analyze_composition,
    detect_motifs,
    detect_phrases,
    analyze_harmony,
    detect_form,
    identify_key_ideas,
    generate_expansion_strategies,
    MUSIC21_AVAILABLE,
    _composition_to_music21_stream,
)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_composition_to_music21_stream():
    """Test conversion of Composition to music21 Stream."""
    comp = Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    NoteEvent(
                        start=0,
                        duration=1,
                        pitches=[60, 64, 67],  # C major chord
                        velocity=80,
                    ),
                    NoteEvent(
                        start=2,
                        duration=1,
                        pitches=[62, 65, 69],  # D minor chord
                        velocity=80,
                    ),
                ]
            )
        ],
    )
    
    stream = _composition_to_music21_stream(comp)
    assert stream is not None
    # Check that stream has parts (using getElementsByClass)
    from music21 import stream as m21_stream
    parts = stream.getElementsByClass(m21_stream.Part)
    assert len(parts) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_analyze_harmony():
    """Test harmonic analysis."""
    comp = Composition(
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
    
    harmony = analyze_harmony(comp)
    assert harmony is not None
    assert len(harmony.chords) > 0
    assert harmony.key == "C"


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_detect_motifs():
    """Test motif detection."""
    comp = Composition(
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
    
    motifs = detect_motifs(comp)
    # Should detect at least some patterns
    assert isinstance(motifs, list)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_detect_phrases():
    """Test phrase detection."""
    comp = Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60], velocity=80),
                    NoteEvent(start=1, duration=1, pitches=[62], velocity=80),
                    NoteEvent(start=2, duration=1, pitches=[64], velocity=80),
                    NoteEvent(start=3, duration=1, pitches=[65], velocity=80),
                    # Gap (phrase boundary)
                    NoteEvent(start=6, duration=1, pitches=[67], velocity=80),
                    NoteEvent(start=7, duration=1, pitches=[69], velocity=80),
                ]
            )
        ],
    )
    
    phrases = detect_phrases(comp)
    assert isinstance(phrases, list)
    # Should detect at least one phrase
    assert len(phrases) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_detect_form():
    """Test form detection."""
    from pianist.schema import SectionEvent
    
    comp = Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    SectionEvent(start=0, label="A"),
                    NoteEvent(start=0, duration=4, pitches=[60], velocity=80),
                    SectionEvent(start=4, label="B"),
                    NoteEvent(start=4, duration=4, pitches=[62], velocity=80),
                    SectionEvent(start=8, label="A"),
                    NoteEvent(start=8, duration=4, pitches=[60], velocity=80),
                ]
            )
        ],
    )
    
    form = detect_form(comp)
    # Should detect ternary form (A-B-A)
    assert form == "ternary"


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_identify_key_ideas():
    """Test key idea identification."""
    comp = Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=1, duration=1, pitches=[62, 65, 69], velocity=80),
                ]
            )
        ],
    )
    
    key_ideas = identify_key_ideas(comp)
    assert isinstance(key_ideas, list)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_generate_expansion_strategies():
    """Test expansion strategy generation."""
    comp = Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=1, duration=1, pitches=[62, 65, 69], velocity=80),
                ]
            )
        ],
    )
    
    strategies = generate_expansion_strategies(comp)
    assert isinstance(strategies, list)
    assert len(strategies) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_analyze_composition():
    """Test complete composition analysis."""
    comp = Composition(
        title="Test",
        bpm=120,
        key_signature="C",
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=1, duration=1, pitches=[62, 65, 69], velocity=80),
                    NoteEvent(start=2, duration=1, pitches=[64, 67, 71], velocity=80),
                ]
            )
        ],
    )
    
    analysis = analyze_composition(comp)
    assert analysis is not None
    assert analysis.motifs is not None
    assert analysis.phrases is not None
    assert analysis.harmonic_progression is not None
    assert analysis.expansion_suggestions is not None


@pytest.mark.skipif(MUSIC21_AVAILABLE, reason="Test requires music21 to be unavailable")
def test_analysis_requires_music21():
    """Test that analysis functions raise ImportError when music21 is not available."""
    comp = Composition(
        title="Test",
        bpm=120,
        tracks=[Track(events=[])],
    )
    
    with pytest.raises(ImportError, match="music21"):
        analyze_composition(comp)
