"""Tests for the annotate command."""

from __future__ import annotations

import json
from pathlib import Path

from pianist.cli import main
from pianist.schema import validate_composition_dict


def test_cli_annotate_show(tmp_path: Path) -> None:
    """Test annotate --show command."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main(["annotate", "-i", str(input_file), "--show"])
    assert rc == 0


def test_cli_annotate_show_with_annotations(tmp_path: Path) -> None:
    """Test annotate --show with existing annotations."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
        "musical_intent": {
            "key_ideas": [
                {
                    "id": "motif_1",
                    "type": "motif",
                    "start": 0,
                    "duration": 4,
                    "description": "Opening motif",
                    "importance": "high"
                }
            ],
            "expansion_points": [],
            "preserve": [],
            "development_direction": None
        }
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main(["annotate", "-i", str(input_file), "--show"])
    assert rc == 0


def test_cli_annotate_mark_motif(tmp_path: Path) -> None:
    """Test annotate with --mark-motif."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-motif", "0-4", "Opening motif"
    ])
    assert rc == 0
    assert output_file.exists()
    
    # Verify annotation was added
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "musical_intent" in data
    assert len(data["musical_intent"]["key_ideas"]) == 1
    assert data["musical_intent"]["key_ideas"][0]["type"] == "motif"
    assert data["musical_intent"]["key_ideas"][0]["description"] == "Opening motif"


def test_cli_annotate_mark_motif_with_importance(tmp_path: Path) -> None:
    """Test annotate with --mark-motif and --importance."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-motif", "0-4", "Opening motif",
        "--importance", "high"
    ])
    assert rc == 0
    
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["musical_intent"]["key_ideas"][0]["importance"] == "high"


def test_cli_annotate_mark_phrase(tmp_path: Path) -> None:
    """Test annotate with --mark-phrase."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 16, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-phrase", "0-16", "Opening phrase"
    ])
    assert rc == 0
    
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(data["musical_intent"]["key_ideas"]) == 1
    assert data["musical_intent"]["key_ideas"][0]["type"] == "phrase"


def test_cli_annotate_mark_harmonic_progression(tmp_path: Path) -> None:
    """Test annotate with --mark-harmonic-progression."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 8, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-harmonic-progression", "0-8", "I-V-vi-IV"
    ])
    assert rc == 0
    
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(data["musical_intent"]["key_ideas"]) == 1
    assert data["musical_intent"]["key_ideas"][0]["type"] == "harmonic_progression"


def test_cli_annotate_mark_rhythmic_pattern(tmp_path: Path) -> None:
    """Test annotate with --mark-rhythmic-pattern."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 2, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-rhythmic-pattern", "0-2", "Syncopated rhythm"
    ])
    assert rc == 0
    
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(data["musical_intent"]["key_ideas"]) == 1
    assert data["musical_intent"]["key_ideas"][0]["type"] == "rhythmic_pattern"


def test_cli_annotate_mark_expansion(tmp_path: Path) -> None:
    """Test annotate with --mark-expansion."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-expansion", "A",
        "--target-length", "120",
        "--development-strategy", "Develop opening motif"
    ])
    assert rc == 0
    assert output_file.exists()
    
    # Verify expansion point was added
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "musical_intent" in data
    assert len(data["musical_intent"]["expansion_points"]) == 1
    assert data["musical_intent"]["expansion_points"][0]["section"] == "A"
    assert data["musical_intent"]["expansion_points"][0]["suggested_length"] == 120


def test_cli_annotate_mark_expansion_requires_target_length(tmp_path: Path) -> None:
    """Test that --mark-expansion requires --target-length."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "--mark-expansion", "A",
        "--development-strategy", "Develop"
    ])
    assert rc == 1  # Should fail - missing --target-length


def test_cli_annotate_mark_expansion_requires_strategy(tmp_path: Path) -> None:
    """Test that --mark-expansion requires --development-strategy."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "--mark-expansion", "A",
        "--target-length", "120"
    ])
    assert rc == 1  # Should fail - missing --development-strategy


def test_cli_annotate_multiple_annotations(tmp_path: Path) -> None:
    """Test annotate with multiple annotations."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "-o", str(output_file),
        "--mark-motif", "0-4", "Opening motif",
        "--mark-phrase", "0-16", "Opening phrase",
        "--overall-direction", "Expand while preserving motifs"
    ])
    assert rc == 0
    
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(data["musical_intent"]["key_ideas"]) == 2
    assert data["musical_intent"]["development_direction"] == "Expand while preserving motifs"


def test_cli_annotate_overwrites_input(tmp_path: Path) -> None:
    """Test that annotate overwrites input when --output is not provided."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "annotate",
        "-i", str(input_file),
        "--mark-motif", "0-4", "Opening motif"
    ])
    assert rc == 0
    
    # File should be modified
    data = json.loads(input_file.read_text(encoding="utf-8"))
    assert "musical_intent" in data
    assert len(data["musical_intent"]["key_ideas"]) == 1

