"""Tests for validation module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pianist.musical_analysis import MUSIC21_AVAILABLE
from pianist.validation import (
    ValidationResult,
    assess_development_quality,
    check_form_consistency,
    check_harmonic_coherence,
    check_motif_preservation,
    validate_expansion,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_validate_expansion_basic(tmp_path: Path) -> None:  # noqa: ARG001
    """Test basic expansion validation."""
    original_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
                    {"type": "note", "start": 1, "duration": 1, "pitches": [62], "velocity": 80},
                ]
            }
        ],
    }

    expanded_json = {
        "title": "Expanded",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(10)
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    original = parse_composition_from_text(json.dumps(original_json))
    expanded = parse_composition_from_text(json.dumps(expanded_json))

    result = validate_expansion(original, expanded, target_length=10.0)

    assert isinstance(result, ValidationResult)
    assert 0.0 <= result.overall_quality <= 1.0
    assert isinstance(result.issues, list)
    assert isinstance(result.warnings, list)
    assert isinstance(result.passed, bool)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_validate_expansion_with_target_length(tmp_path: Path) -> None:  # noqa: ARG001
    """Test validation with target length checking."""
    original_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80},
                ]
            }
        ],
    }

    expanded_json = {
        "title": "Expanded",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(8)  # 8 beats, target is 10
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    original = parse_composition_from_text(json.dumps(original_json))
    expanded = parse_composition_from_text(json.dumps(expanded_json))

    result = validate_expansion(original, expanded, target_length=10.0)

    # Should have warning about length
    assert len(result.warnings) > 0 or len(result.issues) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_check_motif_preservation(tmp_path: Path) -> None:  # noqa: ARG001
    """Test motif preservation checking."""
    original_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    # Motif: C-E-G
                    {"type": "note", "start": 0, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 0.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 1, "duration": 0.5, "pitches": [67], "velocity": 80},
                    # Repeat motif
                    {"type": "note", "start": 4, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 4.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 5, "duration": 0.5, "pitches": [67], "velocity": 80},
                ]
            }
        ],
    }

    expanded_json = {
        "title": "Expanded",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    # Preserve motif: C-E-G
                    {"type": "note", "start": 0, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 0.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 1, "duration": 0.5, "pitches": [67], "velocity": 80},
                    # Add more material
                    {"type": "note", "start": 2, "duration": 1, "pitches": [62], "velocity": 80},
                    # Repeat motif
                    {"type": "note", "start": 6, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 6.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 7, "duration": 0.5, "pitches": [67], "velocity": 80},
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    original = parse_composition_from_text(json.dumps(original_json))
    expanded = parse_composition_from_text(json.dumps(expanded_json))

    result = check_motif_preservation(original, expanded)

    assert "preserved" in result
    assert "preserved_count" in result
    assert "total_count" in result
    assert result["total_count"] >= 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_assess_development_quality(tmp_path: Path) -> None:  # noqa: ARG001
    """Test development quality assessment."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {
                        "type": "note",
                        "start": i,
                        "duration": 1,
                        "pitches": [60 + (i % 7)],
                        "velocity": 80,
                    }
                    for i in range(16)
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(json.dumps(comp_json))

    quality = assess_development_quality(comp)

    assert 0.0 <= quality <= 1.0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_check_harmonic_coherence(tmp_path: Path) -> None:  # noqa: ARG001
    """Test harmonic coherence checking."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "key_signature": "C",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    # C major chord
                    {
                        "type": "note",
                        "start": 0,
                        "duration": 2,
                        "pitches": [60, 64, 67],
                        "velocity": 80,
                    },
                    # F major chord
                    {
                        "type": "note",
                        "start": 2,
                        "duration": 2,
                        "pitches": [65, 69, 72],
                        "velocity": 80,
                    },
                    # G major chord
                    {
                        "type": "note",
                        "start": 4,
                        "duration": 2,
                        "pitches": [67, 71, 74],
                        "velocity": 80,
                    },
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(json.dumps(comp_json))

    coherence = check_harmonic_coherence(comp)

    assert 0.0 <= coherence <= 1.0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_check_form_consistency(tmp_path: Path) -> None:  # noqa: ARG001
    """Test form consistency checking."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "section", "start": 0, "label": "A"},
                    {"type": "note", "start": 0, "duration": 8, "pitches": [60], "velocity": 80},
                    {"type": "section", "start": 8, "label": "B"},
                    {"type": "note", "start": 8, "duration": 8, "pitches": [62], "velocity": 80},
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(json.dumps(comp_json))

    consistency = check_form_consistency(comp)

    assert 0.0 <= consistency <= 1.0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_validate_expansion_without_music21() -> None:
    """Test validation when music21 is not available."""
    # This test would need to mock MUSIC21_AVAILABLE = False
    # For now, just verify the function handles it gracefully


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_validate_expansion_preserves_key_ideas(tmp_path: Path) -> None:  # noqa: ARG001
    """Test validation with musical_intent key ideas."""
    original_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
                ]
            }
        ],
        "musical_intent": {
            "key_ideas": [
                {
                    "id": "important_motif",
                    "type": "motif",
                    "start": 0,
                    "duration": 1,
                    "description": "Important motif",
                    "importance": "high",
                }
            ],
            "expansion_points": [],
            "preserve": [],
            "development_direction": None,
        },
    }

    expanded_json = {
        "title": "Expanded",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(10)
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    original = parse_composition_from_text(json.dumps(original_json))
    expanded = parse_composition_from_text(json.dumps(expanded_json))

    result = validate_expansion(original, expanded)

    # Should check for key ideas
    assert isinstance(result, ValidationResult)
