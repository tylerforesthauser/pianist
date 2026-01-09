"""Tests for expansion strategy generation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pianist.expansion_strategy import (
    ExpansionStrategy,
    generate_expansion_strategy,
    suggest_motif_development,
    suggest_phrase_extension,
    suggest_section_expansion,
)
from pianist.musical_analysis import (
    MUSIC21_AVAILABLE,
    _composition_to_music21_stream,
    analyze_composition,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_generate_expansion_strategy_basic(tmp_path: Path) -> None:
    """Test basic expansion strategy generation."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "key_signature": "C",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
                    {"type": "note", "start": 1, "duration": 1, "pitches": [62], "velocity": 80},
                    {"type": "note", "start": 2, "duration": 1, "pitches": [64], "velocity": 80},
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(input_file.read_text(encoding="utf-8"))

    strategy = generate_expansion_strategy(comp, target_length=16.0)

    assert isinstance(strategy, ExpansionStrategy)
    assert strategy.motif_developments is not None
    assert strategy.section_expansions is not None
    assert strategy.transitions is not None
    assert strategy.preserve is not None
    assert strategy.overall_approach is not None
    assert len(strategy.overall_approach) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_generate_expansion_strategy_with_analysis(tmp_path: Path) -> None:  # noqa: ARG001
    """Test expansion strategy generation with pre-computed analysis."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "key_signature": "C",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
                ]
            }
        ],
    }

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(json.dumps(comp_json))

    # Pre-compute analysis with pre-converted stream to avoid redundant conversion
    stream = _composition_to_music21_stream(comp)
    analysis = analyze_composition(comp, music21_stream=stream)

    strategy = generate_expansion_strategy(comp, target_length=16.0, analysis=analysis)

    assert isinstance(strategy, ExpansionStrategy)
    assert strategy.overall_approach is not None


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_generate_expansion_strategy_with_expansion_points(tmp_path: Path) -> None:  # noqa: ARG001
    """Test expansion strategy with explicit expansion points."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "key_signature": "C",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 8, "pitches": [60], "velocity": 80},
                ]
            }
        ],
        "musical_intent": {
            "key_ideas": [],
            "expansion_points": [
                {
                    "section": "A",
                    "current_length": 8.0,
                    "suggested_length": 16.0,
                    "development_strategy": "Develop opening motif",
                    "preserve": [],
                }
            ],
            "preserve": [],
            "development_direction": None,
        },
    }

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(json.dumps(comp_json))

    strategy = generate_expansion_strategy(comp, target_length=16.0)

    assert len(strategy.section_expansions) > 0
    assert any(exp.section_name == "A" for exp in strategy.section_expansions)


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_suggest_motif_development(tmp_path: Path) -> None:  # noqa: ARG001
    """Test motif development suggestion."""
    from pianist.musical_analysis import Motif

    motif = Motif(start=0.0, duration=2.0, pitches=[60, 64, 67], description="Test motif")

    suggestion = suggest_motif_development(motif, target_length=16.0)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0
    assert "Develop motif" in suggestion or "motif" in suggestion.lower()


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_suggest_phrase_extension(tmp_path: Path) -> None:  # noqa: ARG001
    """Test phrase extension suggestion."""
    from pianist.musical_analysis import Phrase

    phrase = Phrase(start=0.0, duration=4.0, description="Test phrase")

    suggestion = suggest_phrase_extension(phrase, target_length=16.0)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0
    assert "Extend phrase" in suggestion or "phrase" in suggestion.lower()


def test_suggest_section_expansion() -> None:
    """Test section expansion suggestion."""
    suggestion = suggest_section_expansion("A", current_length=8.0, target_length=16.0)
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0
    assert "section" in suggestion.lower() or "A" in suggestion


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_expansion_strategy_preserve_list(tmp_path: Path) -> None:  # noqa: ARG001
    """Test that expansion strategy includes preserve list."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "key_signature": "C",
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
            "preserve": ["key_idea:important_motif"],
            "development_direction": None,
        },
    }

    from pianist.parser import parse_composition_from_text

    comp = parse_composition_from_text(json.dumps(comp_json))

    strategy = generate_expansion_strategy(comp, target_length=16.0)

    assert len(strategy.preserve) > 0
    assert any("important_motif" in item or "key_idea" in item for item in strategy.preserve)
