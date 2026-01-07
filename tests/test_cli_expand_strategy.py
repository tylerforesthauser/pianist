"""Tests for expand command strategy generation (without provider)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pianist.cli import main
from pianist.musical_analysis import MUSIC21_AVAILABLE


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_without_provider_generates_strategy(tmp_path: Path, capsys) -> None:
    """Test that expand without provider generates and displays expansion strategy."""
    comp_json = {
        "title": "Test",
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
        ]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    output_file = tmp_path / "output.json"
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "16.0"
    ])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "Expansion Strategy" in captured.out
    assert "Current length" in captured.out
    assert "Target length" in captured.out
    assert "Overall Approach" in captured.out or "approach" in captured.out.lower()


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_without_provider_saves_composition(tmp_path: Path) -> None:
    """Test that expand without provider still saves the composition."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
                ]
            }
        ]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    output_file = tmp_path / "output.json"
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "16.0"
    ])
    assert rc == 0
    assert output_file.exists()
    
    # Composition should be unchanged (no AI to expand it)
    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert output_data["title"] == "Test"

