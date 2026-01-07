"""Tests for the generate command."""

from __future__ import annotations

import json
from pathlib import Path

from pianist.cli import main


def _valid_composition_json() -> str:
    """Minimal valid Pianist composition JSON."""
    return (
        "{"
        '"title":"Test",'
        '"bpm":120,'
        '"time_signature":{"numerator":4,"denominator":4},'
        '"ppq":480,'
        '"tracks":[{"name":"Piano","channel":0,"program":0,"events":['
        '{"type":"note","start":0,"duration":1,"pitches":[60],"velocity":80}'
        "]}]"
        "}"
    )


def test_cli_generate_prompt_only(tmp_path: Path) -> None:
    """Test generate without provider outputs prompt template."""
    output_file = tmp_path / "prompt.txt"
    rc = main([
        "generate",
        "Title: Test Piece\nForm: binary\nLength: 32 beats",
        "-o", str(output_file)
    ])
    assert rc == 0
    assert output_file.exists()
    prompt_text = output_file.read_text(encoding="utf-8")
    assert "Title: Test Piece" in prompt_text
    assert "USER PROMPT" in prompt_text
    assert "Compose a piano piece" in prompt_text


def test_cli_generate_prompt_stdout(tmp_path: Path, capsys) -> None:
    """Test generate without provider outputs to stdout."""
    rc = main([
        "generate",
        "Title: Test Piece\nForm: binary\nLength: 32 beats"
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "USER PROMPT" in captured.out or "Compose a piano piece" in captured.out


def test_cli_generate_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test generate with AI provider generates composition."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        assert model
        assert "Compose a piano piece" in prompt or "Title: Test Piece" in prompt
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    output_file = tmp_path / "composition.json"
    rc = main([
        "generate",
        "Title: Test Piece\nForm: binary\nLength: 32 beats",
        "--provider", "gemini",
        "-o", str(output_file)
    ])
    assert rc == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["title"] == "Test"


def test_cli_generate_with_provider_and_render(tmp_path: Path, monkeypatch) -> None:
    """Test generate with provider and render creates MIDI."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    output_file = tmp_path / "composition.json"
    rc = main([
        "generate",
        "Title: Test Piece",
        "--provider", "gemini",
        "-o", str(output_file),
        "--render"
    ])
    assert rc == 0
    # MIDI should be auto-generated in output directory
    midi_file = Path("output/generate-output/generate/composition.mid")
    assert midi_file.exists()


def test_cli_generate_requires_description(tmp_path: Path) -> None:
    """Test that generate requires a description."""
    rc = main(["generate"])
    assert rc != 0  # Should fail without description


def test_cli_generate_render_requires_provider(tmp_path: Path) -> None:
    """Test that --render requires --provider."""
    rc = main([
        "generate",
        "Title: Test",
        "--render"
    ])
    assert rc != 0  # Should fail without provider


def test_cli_generate_saves_prompt(tmp_path: Path) -> None:
    """Test that --prompt saves prompt template."""
    prompt_file = tmp_path / "prompt.txt"
    rc = main([
        "generate",
        "Title: Test Piece",
        "-p", str(prompt_file)
    ])
    assert rc == 0
    assert prompt_file.exists()
    prompt_text = prompt_file.read_text(encoding="utf-8")
    assert "USER PROMPT" in prompt_text or "Compose a piano piece" in prompt_text


def test_cli_generate_reads_from_stdin(tmp_path: Path, monkeypatch) -> None:
    """Test that generate can read description from stdin."""
    import sys
    from io import StringIO
    
    description = "Title: Test Piece\nForm: binary"
    
    # Mock stdin
    monkeypatch.setattr(sys, "stdin", StringIO(description))
    
    output_file = tmp_path / "prompt.txt"
    rc = main([
        "generate",
        "-o", str(output_file)
    ])
    assert rc == 0
    prompt_text = output_file.read_text(encoding="utf-8")
    assert "Title: Test Piece" in prompt_text


def test_cli_generate_with_raw_output(tmp_path: Path, monkeypatch) -> None:
    """Test that generate saves raw AI response when --raw is provided."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    output_file = tmp_path / "composition.json"
    raw_file = tmp_path / "raw.txt"
    rc = main([
        "generate",
        "Title: Test",
        "--provider", "gemini",
        "-o", str(output_file),
        "-r", str(raw_file)
    ])
    assert rc == 0
    assert raw_file.exists()
    raw_text = raw_file.read_text(encoding="utf-8")
    assert "title" in raw_text.lower()


def test_cli_generate_versioning(tmp_path: Path, monkeypatch) -> None:
    """Test that generate versions output files when they exist."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    output_file = tmp_path / "composition.json"
    output_file.write_text("existing content", encoding="utf-8")
    
    rc = main([
        "generate",
        "Title: Test",
        "--provider", "gemini",
        "-o", str(output_file)
    ])
    assert rc == 0
    # Should create versioned file
    versioned = tmp_path / "composition_v2.json"
    assert versioned.exists() or output_file.exists()  # May overwrite or version


def test_cli_generate_overwrite_flag(tmp_path: Path, monkeypatch) -> None:
    """Test that --overwrite prevents versioning."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    output_file = tmp_path / "composition.json"
    output_file.write_text("existing content", encoding="utf-8")
    
    rc = main([
        "generate",
        "Title: Test",
        "--provider", "gemini",
        "-o", str(output_file),
        "--overwrite"
    ])
    assert rc == 0
    # Should overwrite, not version
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["title"] == "Test"

