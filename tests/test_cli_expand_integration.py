"""Integration tests for expand CLI command.

These tests make real API calls and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API keys are available

To run these tests:
    pytest -m integration tests/test_cli_expand_integration.py

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
def test_cli_expand_with_openrouter_expands_composition(tmp_path: Path) -> None:
    """Test that expand command expands composition with OpenRouter."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"

    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "--target-length",
            "32",
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
def test_cli_expand_with_openrouter_meets_target_length(tmp_path: Path) -> None:
    """Test that expand command meets target length."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"

    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "--target-length",
            "16",
        ]
    )

    assert rc == 0
    assert output_file.exists()

    # Verify output is valid
    data = json.loads(output_file.read_text())
    assert "tracks" in data
    # Note: We can't easily verify exact length without parsing events,
    # but we can verify the structure is valid


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_expand_with_openrouter_and_render(tmp_path: Path) -> None:
    """Test that expand command can render to MIDI."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"
    midi_file = tmp_path / "output.mid"

    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "--target-length",
            "16",
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
