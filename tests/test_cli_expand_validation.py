"""Tests for expand command validation functionality."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pianist.cli import main
from pianist.musical_analysis import MUSIC21_AVAILABLE

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_with_validate(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test expand command with --validate flag."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80},
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False
    ) -> str:
        # Return expanded composition
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                        for i in range(16)
                    ]
                }
            ],
        }
        return json.dumps(expanded)

    # Double-patch pattern
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.expand

    monkeypatch.setattr(
        pianist.cli.commands.expand, "generate_text_unified", fake_generate_text_unified
    )

    output_file = output_file.absolute()
    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--target-length",
            "16.0",
            "--provider",
            "openrouter",
            "--validate",
        ]
    )
    assert rc == 0

    capsys.readouterr()
    # Check if file exists at specified path or versioned path
    if not output_file.exists():
        versioned = output_file.parent / f"{output_file.stem}.v2{output_file.suffix}"
        if versioned.exists():
            output_file = versioned
    assert output_file.exists(), f"Output file not found at {output_file} or versioned location"


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_with_validate_verbose(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test expand command with --validate and --verbose flags."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 4, "pitches": [60], "velocity": 80},
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False
    ) -> str:
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                        for i in range(16)
                    ]
                }
            ],
        }
        return json.dumps(expanded)

    # Double-patch pattern
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.expand

    monkeypatch.setattr(
        pianist.cli.commands.expand, "generate_text_unified", fake_generate_text_unified
    )

    output_file = output_file.absolute()
    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--target-length",
            "16.0",
            "--provider",
            "openrouter",
            "--validate",
            "--verbose",
        ]
    )
    assert rc == 0

    captured = capsys.readouterr()
    # Verbose mode should show validation details
    # Validation output may be in stderr or stdout
    validation_found = (
        "Validation" in captured.err
        or "Quality" in captured.err
        or "Motifs" in captured.err
        or "Validation" in captured.out
        or "Quality" in captured.out
        or "Motifs" in captured.out
        or "overall_quality" in captured.err.lower()
        or "motifs_preserved" in captured.err.lower()
    )
    assert validation_found, (
        f"Expected validation output, got stderr: {captured.err[:200]}, stdout: {captured.out[:200]}"
    )
