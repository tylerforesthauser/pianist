"""Tests for annotate --auto-detect functionality."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pianist.cli import main
from pianist.musical_analysis import MUSIC21_AVAILABLE

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_annotate_auto_detect(tmp_path: Path) -> None:
    """Test annotate --auto-detect command."""
    # Create a composition with a repeating motif
    comp_json = {
        "title": "Test with Motif",
        "bpm": 120,
        "key_signature": "C",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "name": "Piano",
                "events": [
                    {"type": "note", "start": 0, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 0.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 1, "duration": 0.5, "pitches": [67], "velocity": 80},
                    # Repeat the motif
                    {"type": "note", "start": 4, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 4.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 5, "duration": 0.5, "pitches": [67], "velocity": 80},
                ],
            }
        ],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    output_file = tmp_path / "output.json"
    rc = main(["annotate", "-i", str(input_file), "-o", str(output_file), "--auto-detect"])
    assert rc == 0

    # Verify annotations were added
    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "musical_intent" in output_data
    assert "key_ideas" in output_data["musical_intent"]
    # Should have at least some auto-detected ideas (motifs or phrases)
    assert len(output_data["musical_intent"]["key_ideas"]) > 0


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_annotate_auto_detect_verbose(tmp_path: Path) -> None:
    """Test annotate --auto-detect with --verbose."""
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
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    output_file = tmp_path / "output.json"
    rc = main(
        ["annotate", "-i", str(input_file), "-o", str(output_file), "--auto-detect", "--verbose"]
    )
    assert rc == 0


@pytest.mark.skipif(MUSIC21_AVAILABLE, reason="Test requires music21 to be unavailable")
def test_cli_annotate_auto_detect_requires_music21(tmp_path: Path) -> None:
    """Test that auto-detect fails gracefully when music21 is not available."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    output_file = tmp_path / "output.json"
    rc = main(["annotate", "-i", str(input_file), "-o", str(output_file), "--auto-detect"])
    assert rc == 1  # Should fail when music21 is not available
