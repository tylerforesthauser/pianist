"""Integration tests for generate CLI command.

These tests make real API calls and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API keys are available

To run these tests:
    pytest -m integration tests/test_cli_generate_integration.py

To run all tests except integration:
    pytest -m "not integration"
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from integration_helpers import skip_if_no_provider

from pianist.cli import main

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_generate_with_openrouter_creates_composition(tmp_path: Path) -> None:
    """Test that generate command creates valid composition with OpenRouter."""
    skip_if_no_provider("openrouter")

    output_file = tmp_path / "composition.json"

    rc = main(
        [
            "generate",
            "Title: Test Piece\nForm: binary\nLength: 16 beats",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "-o",
            str(output_file),
        ]
    )

    assert rc == 0
    assert output_file.exists()

    # Verify output is valid JSON composition
    data = json.loads(output_file.read_text())
    assert "title" in data
    assert "tracks" in data
    assert len(data["tracks"]) > 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_generate_with_openrouter_and_render(tmp_path: Path) -> None:
    """Test that generate command can also render to MIDI."""
    skip_if_no_provider("openrouter")

    output_file = tmp_path / "composition.json"
    midi_file = tmp_path / "composition.mid"

    rc = main(
        [
            "generate",
            "Title: Test Piece\nForm: binary\nLength: 8 beats",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "-o",
            str(output_file),
            "--render",
        ]
    )

    assert rc == 0
    assert output_file.exists()
    assert midi_file.exists()

    # Verify MIDI file is valid
    import mido

    mid = mido.MidiFile(midi_file)
    assert len(mid.tracks) > 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_generate_with_openrouter_saves_raw(tmp_path: Path) -> None:
    """Test that generate command saves raw AI response."""
    skip_if_no_provider("openrouter")

    output_file = tmp_path / "composition.json"
    raw_file = tmp_path / "composition.raw.txt"

    rc = main(
        [
            "generate",
            "Title: Test Piece\nForm: binary\nLength: 8 beats",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "-o",
            str(output_file),
            "-r",
            str(raw_file),
        ]
    )

    assert rc == 0
    assert output_file.exists()
    assert raw_file.exists()

    # Verify raw file has content
    raw_content = raw_file.read_text()
    assert len(raw_content) > 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_generate_with_openrouter_versioning(tmp_path: Path) -> None:
    """Test that generate command handles file versioning correctly."""
    skip_if_no_provider("openrouter")

    output_file = tmp_path / "composition.json"

    # First generation
    rc1 = main(
        [
            "generate",
            "Title: Test Piece v1\nForm: binary\nLength: 8 beats",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "-o",
            str(output_file),
        ]
    )

    assert rc1 == 0
    assert output_file.exists()

    # Second generation (should create .v2.json)
    rc2 = main(
        [
            "generate",
            "Title: Test Piece v2\nForm: binary\nLength: 8 beats",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "-o",
            str(output_file),
        ]
    )

    assert rc2 == 0
    assert output_file.exists()  # Original still exists
    v2_file = tmp_path / "composition.v2.json"
    assert v2_file.exists()  # Versioned file created


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_generate_with_openrouter_stdout(tmp_path: Path, capsys) -> None:
    """Test that generate command can output to stdout."""
    skip_if_no_provider("openrouter")

    rc = main(
        [
            "generate",
            "Title: Test Piece\nForm: binary\nLength: 8 beats",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
        ]
    )

    assert rc == 0

    # Verify stdout has JSON output
    captured = capsys.readouterr()
    stdout_text = captured.out
    assert len(stdout_text) > 0

    # Verify it's valid JSON
    data = json.loads(stdout_text)
    assert "title" in data
    assert "tracks" in data
