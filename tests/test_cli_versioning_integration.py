"""Integration tests for output versioning behavior across commands.

These tests verify that all AI-enabled commands consistently handle
versioning and sidecar files.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import mido

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


def test_modify_versioning_with_provider(tmp_path: Path) -> None:
    """Test modify command creates versioned files when output exists."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "output.json"
    
    # Mock the AI provider
    with patch("pianist.cli.generate_text_unified") as mock_gen:
        mock_gen.return_value = _valid_composition_json()
        
        # First run - creates output.json
        rc = main([
            "modify",
            "-i", str(input_json),
            "-o", str(output_json),
            "--provider", "gemini",
            "--instructions", "Test modification"
        ])
        assert rc == 0
        
        # Should create primary and sidecar
        assert output_json.exists()
        sidecar1 = tmp_path / "output.json.gemini.txt"
        assert sidecar1.exists()
        
        # Second run - should create .v2 versions
        rc = main([
            "modify",
            "-i", str(input_json),
            "-o", str(output_json),
            "--provider", "gemini",
            "--instructions", "Test modification 2"
        ])
        assert rc == 0
        
        # Should create versioned files
        output_v2 = tmp_path / "output.v2.json"
        sidecar2 = tmp_path / "output.v2.json.gemini.txt"
        assert output_v2.exists()
        assert sidecar2.exists()
        
        # Original files should still exist
        assert output_json.exists()
        assert sidecar1.exists()


def test_modify_overwrite_flag(tmp_path: Path) -> None:
    """Test modify command overwrites files when --overwrite is set."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "output.json"
    
    with patch("pianist.cli.generate_text_unified") as mock_gen:
        # First run to create initial files
        first_composition = json.loads(_valid_composition_json())
        first_composition["title"] = "First Title"
        mock_gen.return_value = json.dumps(first_composition)
        
        rc = main([
            "modify",
            "-i", str(input_json),
            "-o", str(output_json),
            "--provider", "gemini",
            "--instructions", "Test"
        ])
        assert rc == 0
        assert output_json.exists()
        sidecar = tmp_path / "output.json.gemini.txt"
        assert sidecar.exists()
        
        # Delete the sidecar to force a new API call
        sidecar.unlink()
        
        # Second run with --overwrite should overwrite, not version
        second_composition = json.loads(_valid_composition_json())
        second_composition["title"] = "Second Title"
        mock_gen.return_value = json.dumps(second_composition)
        
        rc = main([
            "modify",
            "-i", str(input_json),
            "-o", str(output_json),
            "--provider", "gemini",
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
        assert not (tmp_path / "output.v2.json.gemini.txt").exists()


def test_analyze_versioning_with_provider(tmp_path: Path) -> None:
    """Test analyze command creates versioned files when output exists."""
    midi_path = tmp_path / "test.mid"
    _write_test_midi(midi_path)
    
    output_json = tmp_path / "analysis.json"
    
    with patch("pianist.cli.generate_text_unified") as mock_gen:
        mock_gen.return_value = _valid_composition_json()
        
        # First run
        rc = main([
            "analyze",
            "-i", str(midi_path),
            "-o", str(output_json),
            "--provider", "gemini",
            "--instructions", "Analyze"
        ])
        assert rc == 0
        
        assert output_json.exists()
        sidecar1 = tmp_path / "analysis.json.gemini.txt"
        assert sidecar1.exists()
        
        # Second run - should create .v2 versions
        rc = main([
            "analyze",
            "-i", str(midi_path),
            "-o", str(output_json),
            "--provider", "gemini",
            "--instructions", "Analyze again"
        ])
        assert rc == 0
        
        output_v2 = tmp_path / "analysis.v2.json"
        sidecar2 = tmp_path / "analysis.v2.json.gemini.txt"
        assert output_v2.exists()
        assert sidecar2.exists()


def test_expand_versioning_with_provider(tmp_path: Path) -> None:
    """Test expand command creates versioned files when output exists (bug fix)."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "expanded.json"
    
    with patch("pianist.cli.generate_text_unified") as mock_gen:
        mock_gen.return_value = _valid_composition_json()
        
        # First run
        rc = main([
            "expand",
            "-i", str(input_json),
            "-o", str(output_json),
            "--target-length", "16",
            "--provider", "gemini"
        ])
        assert rc == 0
        
        assert output_json.exists()
        sidecar1 = tmp_path / "expanded.json.gemini.txt"
        assert sidecar1.exists()
        
        # Second run - should create .v2 versions with matching sidecar
        rc = main([
            "expand",
            "-i", str(input_json),
            "-o", str(output_json),
            "--target-length", "16",
            "--provider", "gemini"
        ])
        assert rc == 0
        
        # This is the key fix: expand should now version both files consistently
        output_v2 = tmp_path / "expanded.v2.json"
        sidecar2 = tmp_path / "expanded.v2.json.gemini.txt"
        assert output_v2.exists()
        assert sidecar2.exists(), "Bug: expand should version sidecar to match primary file"


def test_generate_versioning_with_provider(tmp_path: Path) -> None:
    """Test generate command creates versioned files when output exists."""
    output_json = tmp_path / "generated.json"
    
    with patch("pianist.cli.generate_text_unified") as mock_gen:
        mock_gen.return_value = _valid_composition_json()
        
        # First run
        rc = main([
            "generate",
            "Create a simple piano piece",
            "-o", str(output_json),
            "--provider", "gemini"
        ])
        assert rc == 0
        
        assert output_json.exists()
        sidecar1 = tmp_path / "generated.json.gemini.txt"
        assert sidecar1.exists()
        
        # Second run - should version
        rc = main([
            "generate",
            "Create another piece",
            "-o", str(output_json),
            "--provider", "gemini"
        ])
        assert rc == 0
        
        output_v2 = tmp_path / "generated.v2.json"
        sidecar2 = tmp_path / "generated.v2.json.gemini.txt"
        assert output_v2.exists()
        assert sidecar2.exists()


def test_different_providers_create_different_sidecars(tmp_path: Path) -> None:
    """Test that different providers create different sidecar files."""
    input_json = tmp_path / "input.json"
    input_json.write_text(_valid_composition_json())
    
    output_json = tmp_path / "output.json"
    
    with patch("pianist.cli.generate_text_unified") as mock_gen:
        mock_gen.return_value = _valid_composition_json()
        
        # Run with gemini
        rc = main([
            "modify",
            "-i", str(input_json),
            "-o", str(output_json),
            "--provider", "gemini",
            "--instructions", "Test",
            "--overwrite"
        ])
        assert rc == 0
        
        gemini_sidecar = tmp_path / "output.json.gemini.txt"
        assert gemini_sidecar.exists()
        
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
        assert gemini_sidecar.exists()
        assert ollama_sidecar.exists()
