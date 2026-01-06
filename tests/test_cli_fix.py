"""Tests for the fix command."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from pianist.cli import main


def test_cli_fix_pedal_basic(tmp_path: Path) -> None:
    """Test the fix --pedal command."""
    # Create a composition with pedal issues
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                    {"type": "pedal", "start": 4, "duration": 0, "value": 0},
                ]
            }
        ],
    }
    
    input_file = tmp_path / "input.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    output_file = tmp_path / "output.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rc = main(["fix", "--pedal", "-i", str(input_file), "-o", str(output_file)])
    
    assert rc == 0
    assert output_file.exists()
    
    # Verify the fix worked
    fixed_data = json.loads(output_file.read_text(encoding="utf-8"))
    pedals = [e for e in fixed_data["tracks"][0]["events"] if e["type"] == "pedal"]
    assert len(pedals) == 1
    assert pedals[0]["duration"] == 4


def test_cli_fix_pedal_overwrites_input(tmp_path: Path) -> None:
    """Test that fix --pedal overwrites input when --output is not provided."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                    {"type": "pedal", "start": 4, "duration": 0, "value": 0},
                ]
            }
        ],
    }
    
    input_file = tmp_path / "input.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rc = main(["fix", "--pedal", "-i", str(input_file)])
    
    assert rc == 0
    # File should be modified
    fixed_data = json.loads(input_file.read_text(encoding="utf-8"))
    pedals = [e for e in fixed_data["tracks"][0]["events"] if e["type"] == "pedal"]
    assert len(pedals) == 1


def test_cli_fix_pedal_render_auto_generates_midi(tmp_path: Path) -> None:
    """Test that fix --pedal auto-generates MIDI path when --render is used without --midi."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main(["fix", "--pedal", "-i", str(input_file), "--render"])
    # Should succeed - MIDI path auto-generated
    assert rc == 0
    # Check that MIDI file was created in output directory
    from pathlib import Path
    output_dir = Path("output") / "input" / "fix"
    assert any(output_dir.glob("*.mid"))


def test_cli_fix_pedal_with_render(tmp_path: Path) -> None:
    """Test fix --pedal with --render option."""
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
        ],
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    output_midi = tmp_path / "output.mid"
    rc = main(
        [
            "fix", "--pedal",
            "-i",
            str(input_file),
            "--render",
            "-m",
            str(output_midi),
        ]
    )
    
    assert rc == 0
    assert output_midi.exists()


def test_cli_fix_pedal_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors in fix command."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json", encoding="utf-8")
    
    rc = main(["fix", "--pedal", "-i", str(invalid_file), "--debug"])
    
    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_fix_requires_flag(tmp_path: Path) -> None:
    """Test that fix command requires a fix flag."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main(["fix", "-i", str(input_file)])
    assert rc == 1  # Should fail - no fix flag specified

