"""Tests for the diff command."""

from __future__ import annotations

import json
from pathlib import Path

from pianist.cli import main


def test_cli_diff_basic(tmp_path: Path) -> None:
    """Test basic diff command."""
    comp1_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    comp2_json = {
        "title": "Modified",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
                {"type": "note", "start": 2, "duration": 1, "pitches": [64], "velocity": 80}
            ]
        }]
    }
    
    file1 = tmp_path / "comp1.json"
    file2 = tmp_path / "comp2.json"
    file1.write_text(json.dumps(comp1_json), encoding="utf-8")
    file2.write_text(json.dumps(comp2_json), encoding="utf-8")
    
    rc = main(["diff", str(file1), str(file2)])
    assert rc == 0


def test_cli_diff_with_output(tmp_path: Path) -> None:
    """Test diff command with output file."""
    comp1_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    comp2_json = {
        "title": "Modified",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    file1 = tmp_path / "comp1.json"
    file2 = tmp_path / "comp2.json"
    out_file = tmp_path / "diff.txt"
    file1.write_text(json.dumps(comp1_json), encoding="utf-8")
    file2.write_text(json.dumps(comp2_json), encoding="utf-8")
    
    rc = main(["diff", str(file1), str(file2), "-o", str(out_file)])
    assert rc == 0
    assert out_file.exists()


def test_cli_diff_json_format(tmp_path: Path) -> None:
    """Test diff command with JSON format."""
    comp1_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    comp2_json = {
        "title": "Modified",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    file1 = tmp_path / "comp1.json"
    file2 = tmp_path / "comp2.json"
    file1.write_text(json.dumps(comp1_json), encoding="utf-8")
    file2.write_text(json.dumps(comp2_json), encoding="utf-8")
    
    rc = main(["diff", str(file1), str(file2), "--format", "json"])
    assert rc == 0


def test_cli_diff_markdown_format(tmp_path: Path) -> None:
    """Test diff command with markdown format."""
    comp1_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    comp2_json = {
        "title": "Modified",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    file1 = tmp_path / "comp1.json"
    file2 = tmp_path / "comp2.json"
    file1.write_text(json.dumps(comp1_json), encoding="utf-8")
    file2.write_text(json.dumps(comp2_json), encoding="utf-8")
    
    rc = main(["diff", str(file1), str(file2), "--format", "markdown"])
    assert rc == 0


def test_cli_diff_show_preserved(tmp_path: Path) -> None:
    """Test diff command with --show-preserved flag."""
    comp1_json = {
        "title": "Original",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    comp2_json = {
        "title": "Modified",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    file1 = tmp_path / "comp1.json"
    file2 = tmp_path / "comp2.json"
    file1.write_text(json.dumps(comp1_json), encoding="utf-8")
    file2.write_text(json.dumps(comp2_json), encoding="utf-8")
    
    rc = main(["diff", str(file1), str(file2), "--show-preserved"])
    assert rc == 0

