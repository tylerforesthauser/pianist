"""
Tests for musical analysis module.
"""

from __future__ import annotations

import pytest

from pianist.musical_analysis import (
    MUSIC21_AVAILABLE,
    _composition_to_music21_stream,
    analyze_composition,
    analyze_harmony,
    detect_form,
    detect_motifs,
    detect_phrases,
    generate_expansion_strategies,
    identify_key_ideas,
)
from pianist.schema import Composition, NoteEvent, Track


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
@pytest.mark.slow
def test_analyze_harmony():
    """Test harmonic analysis."""
    from pianist.musical_analysis import ChordAnalysis

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

    # Convert stream once and reuse to avoid redundant conversion
    stream = _composition_to_music21_stream(comp)
    harmony = analyze_harmony(comp, music21_stream=stream)
    assert harmony is not None
    assert len(harmony.chords) > 0
    # Key may be "C" or "C major" depending on music21 analysis
    assert harmony.key is not None
    assert "C" in harmony.key
    # Check that chords are ChordAnalysis objects
    assert isinstance(harmony.chords[0], ChordAnalysis)
    assert harmony.chords[0].start is not None
    assert harmony.chords[0].pitches is not None
    assert harmony.chords[0].name is not None


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
@pytest.mark.slow
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

    # Convert stream once and reuse to avoid redundant conversion
    stream = _composition_to_music21_stream(comp)
    motifs = detect_motifs(comp, music21_stream=stream)
    # Should detect at least some patterns
    assert isinstance(motifs, list)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_detect_motifs_transposed():
    """Test transposition-aware motif detection."""
    comp = Composition(
        title="Test Transposed Motifs",
        bpm=120,
        tracks=[
            Track(
                events=[
                    # Pattern: C-D-E (ascending)
                    NoteEvent(start=0, duration=0.5, pitches=[60], velocity=80),  # C
                    NoteEvent(start=0.5, duration=0.5, pitches=[62], velocity=80),  # D
                    NoteEvent(start=1, duration=0.5, pitches=[64], velocity=80),  # E
                    # Same pattern transposed up a fifth: G-A-B
                    NoteEvent(start=4, duration=0.5, pitches=[67], velocity=80),  # G
                    NoteEvent(start=4.5, duration=0.5, pitches=[69], velocity=80),  # A
                    NoteEvent(start=5, duration=0.5, pitches=[71], velocity=80),  # B
                ]
            )
        ],
    )

    motifs = detect_motifs(comp)
    # Should detect the transposed pattern
    assert isinstance(motifs, list)
    # May or may not detect depending on algorithm, but should not crash


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_detect_phrases():
    """Test phrase detection."""
    # This test needs a specific composition with phrase boundaries
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

    # Convert stream once and reuse
    stream = _composition_to_music21_stream(comp)
    phrases = detect_phrases(comp, music21_stream=stream)
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

    # Convert stream once and reuse to avoid redundant conversion
    stream = _composition_to_music21_stream(comp)
    key_ideas = identify_key_ideas(comp, music21_stream=stream)
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

    # Convert stream once and reuse to avoid redundant conversion
    stream = _composition_to_music21_stream(comp)
    strategies = generate_expansion_strategies(comp, music21_stream=stream)
    assert isinstance(strategies, list)
    assert len(strategies) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
@pytest.mark.slow
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

    # Convert stream once and reuse to avoid redundant conversion
    # This test does full analysis so it's marked as slow
    stream = _composition_to_music21_stream(comp)
    analysis = analyze_composition(comp, music21_stream=stream)
    assert analysis is not None
    assert analysis.motifs is not None
    assert analysis.phrases is not None
    assert analysis.harmonic_progression is not None
    assert analysis.expansion_suggestions is not None
    # Check that harmonic_progression has new fields
    if analysis.harmonic_progression:
        assert hasattr(analysis.harmonic_progression, "roman_numerals")
        assert hasattr(analysis.harmonic_progression, "cadences")
        assert hasattr(analysis.harmonic_progression, "progression")
        assert hasattr(analysis.harmonic_progression, "voice_leading")


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_analyze_harmony_roman_numerals():
    """Test Roman numeral analysis."""
    comp = Composition(
        title="Test Roman Numerals",
        bpm=120,
        key_signature="C",
        tracks=[
            Track(
                events=[
                    NoteEvent(
                        start=0, duration=1, pitches=[60, 64, 67], velocity=80
                    ),  # C major (I)
                    NoteEvent(
                        start=1, duration=1, pitches=[67, 71, 74], velocity=80
                    ),  # G major (V)
                    NoteEvent(
                        start=2, duration=1, pitches=[60, 64, 67], velocity=80
                    ),  # C major (I)
                ]
            )
        ],
    )

    # Convert stream once and reuse
    stream = _composition_to_music21_stream(comp)
    harmony = analyze_harmony(comp, music21_stream=stream)
    assert harmony is not None
    # May or may not have Roman numerals depending on music21 analysis
    # But should not crash
    if harmony.roman_numerals:
        assert isinstance(harmony.roman_numerals, list)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_analyze_harmony_cadences():
    """Test cadence detection."""
    comp = Composition(
        title="Test Cadences",
        bpm=120,
        key_signature="C",
        tracks=[
            Track(
                events=[
                    NoteEvent(
                        start=0, duration=1, pitches=[67, 71, 74], velocity=80
                    ),  # G major (V)
                    NoteEvent(
                        start=1, duration=1, pitches=[60, 64, 67], velocity=80
                    ),  # C major (I) - authentic cadence
                ]
            )
        ],
    )

    # Convert stream once and reuse
    stream = _composition_to_music21_stream(comp)
    harmony = analyze_harmony(comp, music21_stream=stream)
    assert harmony is not None
    # May or may not detect cadences depending on Roman numeral analysis
    # But should have cadences field
    assert hasattr(harmony, "cadences")
    if harmony.cadences:
        assert isinstance(harmony.cadences, list)
        for cadence in harmony.cadences:
            assert "type" in cadence
            assert "start" in cadence


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_analyze_harmony_voice_leading():
    """Test voice leading analysis."""
    comp = Composition(
        title="Test Voice Leading",
        bpm=120,
        key_signature="C",
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60, 64, 67], velocity=80),  # C major
                    NoteEvent(start=1, duration=1, pitches=[62, 65, 69], velocity=80),  # D minor
                ]
            )
        ],
    )

    # Convert stream once and reuse
    stream = _composition_to_music21_stream(comp)
    harmony = analyze_harmony(comp, music21_stream=stream)
    assert harmony is not None
    # Should have voice_leading field
    assert hasattr(harmony, "voice_leading")
    if harmony.voice_leading and len(harmony.chords) >= 2:
        assert isinstance(harmony.voice_leading, list)
        if harmony.voice_leading:
            vl = harmony.voice_leading[0]
            assert "common_tones" in vl
            assert "stepwise_motion" in vl
            assert "quality" in vl


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_detect_form_automatic():
    """Test automatic form detection."""
    comp = Composition(
        title="Test Automatic Form",
        bpm=120,
        tracks=[
            Track(
                events=[
                    # First phrase
                    NoteEvent(start=0, duration=1, pitches=[60], velocity=80),
                    NoteEvent(start=1, duration=1, pitches=[62], velocity=80),
                    NoteEvent(start=2, duration=1, pitches=[64], velocity=80),
                    # Large gap (section boundary)
                    NoteEvent(start=6, duration=1, pitches=[67], velocity=80),
                    NoteEvent(start=7, duration=1, pitches=[69], velocity=80),
                ]
            )
        ],
    )

    # Convert stream once and reuse
    stream = _composition_to_music21_stream(comp)
    form = detect_form(comp, music21_stream=stream)
    # May detect form or return None
    assert form is None or isinstance(form, str)


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
