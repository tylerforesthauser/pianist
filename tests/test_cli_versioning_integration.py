"""Integration tests for output versioning behavior across commands.

These tests verify that all AI-enabled commands consistently handle
versioning and sidecar files.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import mido
import pytest

from pianist.cli import main


def _write_test_midi(path: Path) -> None:
    """Create a minimal test MIDI file."""
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)

    tr.append(mido.MetaMessage("track_name", name="Piano", time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))

    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))

    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(path)


def _valid_composition_json() -> str:
    """Minimal valid Pianist composition JSON."""
    return json.dumps({
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "name": "Piano",
            "channel": 0,
            "program": 0,
            "events": [{
                "type": "note",
                "start": 0,
                "duration": 1,
                "pitches": [60],
                "velocity": 80
            }]
        }]
    })


def test_modify_versioning_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test modify command creates versioned files when output exists."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "output.json"
    
    # Mock the AI provider - double patch pattern
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify
    monkeypatch.setattr(pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified)
    
    # First run - creates output.json
    rc = main([
        "modify",
        "-i", str(input_json),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Test modification"
    ])
    assert rc == 0
    
    # Should create primary and sidecar
    assert output_json.exists()
    sidecar1 = tmp_path / "output.json.openrouter.txt"
    assert sidecar1.exists()
    
    # Second run - should create .v2 versions
    rc = main([
        "modify",
        "-i", str(input_json),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Test modification 2"
    ])
    assert rc == 0
    
    # Should create versioned files
    output_v2 = tmp_path / "output.v2.json"
    sidecar2 = tmp_path / "output.v2.json.openrouter.txt"
    assert output_v2.exists()
    assert sidecar2.exists()
    
    # Original files should still exist
    assert output_json.exists()
    assert sidecar1.exists()


def test_modify_overwrite_flag(tmp_path: Path, monkeypatch) -> None:
    """Test modify command overwrites files when --overwrite is set."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "output.json"
    
    # Track calls to return different compositions
    call_count = {"count": 0}
    
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        call_count["count"] += 1
        comp = json.loads(_valid_composition_json())
        comp["title"] = "First Title" if call_count["count"] == 1 else "Second Title"
        return json.dumps(comp)
    
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify
    monkeypatch.setattr(pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified)
    
    # First run to create initial files
    rc = main([
        "modify",
        "-i", str(input_json),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Test"
    ])
    assert rc == 0
    assert output_json.exists()
    sidecar = tmp_path / "output.json.openrouter.txt"
    assert sidecar.exists()
    
    # Delete the sidecar to force a new API call
    sidecar.unlink()
    
    # Second run with --overwrite should overwrite, not version
    rc = main([
        "modify",
        "-i", str(input_json),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Test",
        "--overwrite"
    ])
    assert rc == 0
    
    # Should overwrite original files, not create versioned ones
    assert output_json.exists()
    result_json = json.loads(output_json.read_text())
    assert result_json["title"] == "Second Title"
    
    # No .v2 versions should exist
    assert not (tmp_path / "output.v2.json").exists()
    assert not (tmp_path / "output.v2.json.openrouter.txt").exists()


def test_analyze_versioning_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test analyze command creates versioned files when output exists."""
    midi_path = tmp_path / "test.mid"
    _write_test_midi(midi_path)
    
    output_json = tmp_path / "analysis.json"
    
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze
    monkeypatch.setattr(pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified)
    
    # First run
    rc = main([
        "analyze",
        "-i", str(midi_path),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Analyze"
    ])
    assert rc == 0
    
    assert output_json.exists()
    sidecar1 = tmp_path / "analysis.json.openrouter.txt"
    assert sidecar1.exists()
    
    # Second run - should create .v2 versions
    rc = main([
        "analyze",
        "-i", str(midi_path),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Analyze again"
    ])
    assert rc == 0
    
    output_v2 = tmp_path / "analysis.v2.json"
    sidecar2 = tmp_path / "analysis.v2.json.openrouter.txt"
    assert output_v2.exists()
    assert sidecar2.exists()


def test_expand_versioning_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test expand command creates versioned files when output exists (bug fix)."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "expanded.json"
    
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        # Return an expanded composition that meets target length
        comp = json.loads(_valid_composition_json())
        # Add more events to meet target length of 16 beats
        for i in range(1, 16):
            comp["tracks"][0]["events"].append({
                "type": "note",
                "start": i,
                "duration": 1,
                "pitches": [60],
                "velocity": 80
            })
        return json.dumps(comp)
    
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.expand
    monkeypatch.setattr(pianist.cli.commands.expand, "generate_text_unified", fake_generate_text_unified)
    
    # First run
    rc = main([
        "expand",
        "-i", str(input_json),
        "-o", str(output_json),
        "--target-length", "16",
        "--provider", "openrouter"
    ])
    assert rc == 0
    
    assert output_json.exists()
    sidecar1 = tmp_path / "expanded.json.openrouter.txt"
    assert sidecar1.exists()
    
    # Second run - should create .v2 versions with matching sidecar
    rc = main([
        "expand",
        "-i", str(input_json),
        "-o", str(output_json),
        "--target-length", "16",
        "--provider", "openrouter"
    ])
    assert rc == 0
    
    # This is the key fix: expand should now version both files consistently
    output_v2 = tmp_path / "expanded.v2.json"
    sidecar2 = tmp_path / "expanded.v2.json.openrouter.txt"
    assert output_v2.exists()
    assert sidecar2.exists(), "Bug: expand should version sidecar to match primary file"


def test_generate_versioning_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test generate command creates versioned files when output exists."""
    output_json = tmp_path / "generated.json"
    
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.generate
    monkeypatch.setattr(pianist.cli.commands.generate, "generate_text_unified", fake_generate_text_unified)
    
    # First run
    rc = main([
        "generate",
        "Create a simple piano piece",
        "-o", str(output_json),
        "--provider", "openrouter"
    ])
    assert rc == 0
    
    assert output_json.exists()
    sidecar1 = tmp_path / "generated.json.openrouter.txt"
    assert sidecar1.exists()
    
    # Second run - should version
    rc = main([
        "generate",
        "Create another piece",
        "-o", str(output_json),
        "--provider", "openrouter"
    ])
    assert rc == 0
    
    output_v2 = tmp_path / "generated.v2.json"
    sidecar2 = tmp_path / "generated.v2.json.openrouter.txt"
    assert output_v2.exists()
    assert sidecar2.exists()


def test_different_providers_create_different_sidecars(tmp_path: Path, monkeypatch) -> None:
    """Test that different providers create different sidecar files."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "output.json"
    
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify
    monkeypatch.setattr(pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified)
    
    # Run with openrouter
    rc = main([
        "modify",
        "-i", str(input_json),
        "-o", str(output_json),
        "--provider", "openrouter",
        "--instructions", "Test",
        "--overwrite"
    ])
    assert rc == 0
    
    openrouter_sidecar = tmp_path / "output.json.openrouter.txt"
    assert openrouter_sidecar.exists()
    
    # Run with ollama (overwriting primary but creating new sidecar)
    rc = main([
        "modify",
        "-i", str(input_json),
        "-o", str(output_json),
        "--provider", "ollama",
        "--instructions", "Test",
        "--overwrite"
    ])
    assert rc == 0
    
    ollama_sidecar = tmp_path / "output.json.ollama.txt"
    assert ollama_sidecar.exists()
    
    # Both sidecars should exist
    assert openrouter_sidecar.exists()
    assert ollama_sidecar.exists()
