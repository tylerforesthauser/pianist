"""Tests for the expand command."""

from __future__ import annotations

import json
from pathlib import Path

from pianist.cli import main
from pianist.schema import validate_composition_dict


def test_cli_expand_basic(tmp_path: Path) -> None:
    """Test expand command (without provider - just strategy)."""
    comp_json = {
        "title": "Sketch",
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
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    # Without provider, should show strategy
    rc = main([
        "expand",
        "-i", str(input_file),
        "--target-length", "120"
    ])
    # Should succeed (even if just showing strategy)
    assert rc == 0


def test_cli_expand_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test expand command with AI provider."""
    comp_json = {
        "title": "Sketch",
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
                    for i in range(120)
                ]
            }]
        }
        return json.dumps(expanded)
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "120",
        "--provider", "gemini"
    ])
    assert rc == 0
    assert output_file.exists()
    
    # Verify output is valid
    data = json.loads(output_file.read_text(encoding="utf-8"))
    validate_composition_dict(data)


def test_cli_expand_with_preserve_motifs(tmp_path: Path, monkeypatch) -> None:
    """Test expand with --preserve-motifs flag."""
    comp_json = {
        "title": "Sketch",
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
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        # Verify preserve-motifs is in prompt
        assert "preserve" in prompt.lower() or "motif" in prompt.lower()
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [{
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(120)
                ]
            }]
        }
        return json.dumps(expanded)
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "120",
        "--provider", "gemini",
        "--preserve-motifs"
    ])
    assert rc == 0


def test_cli_expand_with_preserve_list(tmp_path: Path, monkeypatch) -> None:
    """Test expand with --preserve flag."""
    comp_json = {
        "title": "Sketch",
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
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [{
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(120)
                ]
            }]
        }
        return json.dumps(expanded)
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "120",
        "--provider", "gemini",
        "--preserve", "motif_1,phrase_A"
    ])
    assert rc == 0


def test_cli_expand_requires_target_length(tmp_path: Path) -> None:
    """Test that expand requires --target-length."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main([
        "expand",
        "-i", str(input_file)
    ])
    assert rc != 0  # Should fail - missing --target-length (argparse uses exit code 2)


def test_cli_expand_with_render(tmp_path: Path, monkeypatch) -> None:
    """Test expand with --render flag."""
    comp_json = {
        "title": "Sketch",
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
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [{
                "events": [
                    {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                    for i in range(120)
                ]
            }]
        }
        return json.dumps(expanded)
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main([
        "expand",
        "-i", str(input_file),
        "-o", str(output_file),
        "--target-length", "120",
        "--provider", "gemini",
        "--render"
    ])
    assert rc == 0
    # MIDI file should be created in output directory
    from pathlib import Path
    output_dir = Path("output") / "input" / "expand"
    assert any(output_dir.glob("*.mid"))

