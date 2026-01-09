"""Integration tests for modify CLI command.

These tests make real API calls and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API keys are available

To run these tests:
    pytest -m integration tests/test_cli_modify_integration.py

To run all tests except integration:
    pytest -m "not integration"
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from conftest import valid_composition_json
from integration_helpers import skip_if_no_provider

from pianist.cli import main

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_modify_with_openrouter_modifies_composition(tmp_path: Path) -> None:
    """Test that modify command modifies composition with OpenRouter."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"

    rc = main(
        [
            "modify",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "Make it faster and more energetic",
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
def test_cli_modify_with_openrouter_and_transpose(tmp_path: Path) -> None:
    """Test that modify command works with transpose option."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"

    rc = main(
        [
            "modify",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--transpose",
            "5",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "Add more dynamics",
        ]
    )

    assert rc == 0
    assert output_file.exists()

    # Verify output is valid
    data = json.loads(output_file.read_text())
    assert "tracks" in data


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_modify_with_openrouter_and_render(tmp_path: Path) -> None:
    """Test that modify command can render to MIDI."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"
    midi_file = tmp_path / "output.mid"

    rc = main(
        [
            "modify",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "--render",
            "Make it more expressive",
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
def test_cli_modify_with_openrouter_saves_raw(tmp_path: Path) -> None:
    """Test that modify command saves raw AI response."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"
    raw_file = tmp_path / "output.raw.txt"

    rc = main(
        [
            "modify",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "-r",
            str(raw_file),
            "Add more variation",
        ]
    )

    assert rc == 0
    assert output_file.exists()
    assert raw_file.exists()

    # Verify raw file has content
    raw_content = raw_file.read_text()
    assert len(raw_content) > 0
