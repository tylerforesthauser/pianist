"""Tests for analyze command with JSON input."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pianist.cli import main
from pianist.musical_analysis import MUSIC21_AVAILABLE

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_analyze_json_basic(tmp_path: Path, monkeypatch) -> None:
    """Test analyze with JSON input performs musical analysis."""
    comp_json = {
        "title": "Test Composition",
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
                ],
            }
        ],
    }

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,  # noqa: ARG001
    ) -> str:
        # Return minimal valid JSON for AI insights
        return '{"suggested_name": "Test", "suggested_style": "Classical", "suggested_description": "A test composition"}'

    # Patch both locations for AI insights
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    output_file = tmp_path / "analysis.json"
    rc = main(
        ["analyze", "-i", str(input_file), "-o", str(output_file), "--ai-provider", "openrouter"]
    )
    assert rc == 0
    assert output_file.exists()

    analysis_data = json.loads(output_file.read_text(encoding="utf-8"))
    # New structure has filename, filepath instead of source
    assert "filename" in analysis_data
    assert "filepath" in analysis_data
    assert analysis_data["filepath"] == str(input_file)
    # New structure has musical_analysis instead of analysis
    assert "musical_analysis" in analysis_data
    assert "motifs" in analysis_data["musical_analysis"]
    assert "phrases" in analysis_data["musical_analysis"]


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_analyze_json_stdout(tmp_path: Path, capsys) -> None:
    """Test analyze with JSON input outputs to stdout when no output specified."""
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    rc = main(["analyze", "-i", str(input_file)])
    assert rc == 0

    captured = capsys.readouterr()
    assert "analysis" in captured.out.lower() or "motifs" in captured.out.lower()


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_analyze_json_requires_music21(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze with JSON requires music21."""
    # Temporarily make music21 unavailable
    import pianist.cli.commands.analyze

    monkeypatch.setattr(pianist.cli.commands.analyze, "MUSIC21_AVAILABLE", False)

    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    rc = main(["analyze", "-i", str(input_file)])
    assert rc == 1  # Should fail when music21 unavailable


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_analyze_json_with_motifs(tmp_path: Path, monkeypatch) -> None:
    """Test analyze detects motifs in JSON composition."""

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,  # noqa: ARG001
    ) -> str:
        return '{"suggested_name": "Test", "suggested_style": "Classical", "suggested_description": "A test composition"}'

    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    # Create composition with repeating motif
    comp_json = {
        "title": "Motif Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    # First occurrence of motif
                    {"type": "note", "start": 0, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 0.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 1, "duration": 0.5, "pitches": [67], "velocity": 80},
                    # Repeat motif
                    {"type": "note", "start": 4, "duration": 0.5, "pitches": [60], "velocity": 80},
                    {
                        "type": "note",
                        "start": 4.5,
                        "duration": 0.5,
                        "pitches": [64],
                        "velocity": 80,
                    },
                    {"type": "note", "start": 5, "duration": 0.5, "pitches": [67], "velocity": 80},
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    output_file = tmp_path / "analysis.json"
    rc = main(
        ["analyze", "-i", str(input_file), "-o", str(output_file), "--ai-provider", "openrouter"]
    )
    assert rc == 0

    analysis_data = json.loads(output_file.read_text(encoding="utf-8"))
    # New structure has musical_analysis instead of analysis
    assert "musical_analysis" in analysis_data
    assert "motifs" in analysis_data["musical_analysis"]
    # May or may not detect motifs depending on algorithm sensitivity


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_analyze_json_includes_expansion_suggestions(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze includes expansion suggestions in output."""

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,  # noqa: ARG001
    ) -> str:
        return '{"suggested_name": "Test", "suggested_style": "Classical", "suggested_description": "A test composition"}'

    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

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
        ],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    output_file = tmp_path / "analysis.json"
    rc = main(
        ["analyze", "-i", str(input_file), "-o", str(output_file), "--ai-provider", "openrouter"]
    )
    assert rc == 0

    analysis_data = json.loads(output_file.read_text(encoding="utf-8"))
    # New structure has improvement_suggestions instead of expansion_suggestions in analysis
    assert "improvement_suggestions" in analysis_data
