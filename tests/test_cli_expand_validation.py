"""Tests for expand command validation functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pianist.cli import main
from pianist.musical_analysis import MUSIC21_AVAILABLE


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_with_validate(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test expand command with --validate flag."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80},
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        # Return expanded composition
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [{
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(16)
                ]
            }]
        }
        return json.dumps(expanded)
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "16.0",
        "--provider", "gemini",
        "--validate"
    ])
    assert rc == 0
    
    captured = capsys.readouterr()
    # Should have validation output (either in stdout or stderr)
    # Validation messages go to stderr
    assert output_file.exists()


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_with_validate_verbose(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test expand command with --validate and --verbose flags."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80},
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [{
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(16)
                ]
            }]
        }
        return json.dumps(expanded)
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "16.0",
        "--provider", "gemini",
        "--validate",
        "--verbose"
    ])
    assert rc == 0
    
    captured = capsys.readouterr()
    # Verbose mode should show validation details
    assert "Validation" in captured.err or "Quality" in captured.err or "Motifs" in captured.err

