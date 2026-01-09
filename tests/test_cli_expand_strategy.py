"""Tests for expand command strategy generation (without provider)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pianist.cli import main
from pianist.musical_analysis import MUSIC21_AVAILABLE

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_with_provider_expands_composition(tmp_path: Path, monkeypatch) -> None:
    """Test that expand with provider expands the composition."""
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

    # Mock AI provider
    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,  # noqa: ARG001
    ) -> str:
        # Return expanded composition with more events to meet target length
        # Deep copy to avoid modifying original
        expanded = json.loads(json.dumps(comp_json))
        # Add many more events to ensure expansion
        expanded["tracks"][0]["events"].extend(
            [
                {
                    "type": "note",
                    "start": i,
                    "duration": 1,
                    "pitches": [60 + (i % 7)],
                    "velocity": 80,
                }
                for i in range(2, 20)  # Add 18 more events
            ]
        )
        return json.dumps(expanded)

    # Double-patch pattern
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.expand

    monkeypatch.setattr(
        pianist.cli.commands.expand, "generate_text_unified", fake_generate_text_unified
    )

    output_file = (tmp_path / "output.json").absolute()
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
        ]
    )
    assert rc == 0
    # Check if file exists at specified path or versioned path
    if not output_file.exists():
        versioned = output_file.parent / f"{output_file.stem}.v2{output_file.suffix}"
        if versioned.exists():
            output_file = versioned
    assert output_file.exists(), f"Output file not found at {output_file} or versioned location"

    # Composition should be expanded
    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(output_data["tracks"][0]["events"]) > len(comp_json["tracks"][0]["events"])


@pytest.mark.skipif(not MUSIC21_AVAILABLE, reason="music21 not installed")
def test_cli_expand_with_provider_saves_expanded_composition(tmp_path: Path, monkeypatch) -> None:
    """Test that expand with provider saves the expanded composition."""
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

    # Mock AI provider
    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,  # noqa: ARG001
    ) -> str:
        # Return expanded composition with more events to meet target length
        # Deep copy to avoid modifying original
        expanded = json.loads(json.dumps(comp_json))
        # Add many more events to ensure expansion
        expanded["tracks"][0]["events"].extend(
            [
                {
                    "type": "note",
                    "start": i,
                    "duration": 1,
                    "pitches": [60 + (i % 7)],
                    "velocity": 80,
                }
                for i in range(1, 20)  # Add 19 more events
            ]
        )
        return json.dumps(expanded)

    # Double-patch pattern
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.expand

    monkeypatch.setattr(
        pianist.cli.commands.expand, "generate_text_unified", fake_generate_text_unified
    )

    output_file = (tmp_path / "output.json").absolute()
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
        ]
    )
    assert rc == 0
    assert output_file.exists()

    # Composition should be expanded
    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert output_data["title"] == "Test"
    assert len(output_data["tracks"][0]["events"]) > len(comp_json["tracks"][0]["events"])
