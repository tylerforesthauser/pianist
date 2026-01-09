"""Integration tests for analyze CLI command.

These tests make real API calls and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API keys are available

To run these tests:
    pytest -m integration tests/test_cli_analyze_integration.py

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
def test_cli_analyze_json_with_ai_provider_generates_insights(tmp_path: Path) -> None:
    """Test that analyze command generates AI insights for JSON input."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "analysis.json"

    rc = main(
        [
            "analyze",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--ai-provider",
            "openrouter",
            "--ai-model",
            "mistralai/devstral-2512:free",
        ]
    )

    assert rc == 0
    assert output_file.exists()

    # Verify output has analysis data
    data = json.loads(output_file.read_text())
    # Analysis should have some structure
    assert isinstance(data, dict)
    # Should have some analysis fields (exact structure may vary)
    assert len(data) > 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_cli_analyze_with_ai_provider_and_provider(tmp_path: Path) -> None:
    """Test that analyze command can analyze and generate new composition."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"

    rc = main(
        [
            "analyze",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--ai-provider",
            "openrouter",
            "--ai-model",
            "mistralai/devstral-2512:free",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "--instructions",
            "Create a variation",
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
def test_cli_analyze_with_ai_provider_and_render(tmp_path: Path) -> None:
    """Test that analyze command can render generated composition."""
    skip_if_no_provider("openrouter")

    # Create input composition
    input_file = tmp_path / "input.json"
    input_file.write_text(valid_composition_json(), encoding="utf-8")

    output_file = tmp_path / "output.json"
    midi_file = tmp_path / "output.mid"

    rc = main(
        [
            "analyze",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--ai-provider",
            "openrouter",
            "--ai-model",
            "mistralai/devstral-2512:free",
            "--provider",
            "openrouter",
            "--model",
            "mistralai/devstral-2512:free",
            "--render",
            "--instructions",
            "Create a variation",
        ]
    )

    assert rc == 0
    assert output_file.exists()
    assert midi_file.exists()

    # Verify MIDI file is valid
    import mido

    mid = mido.MidiFile(midi_file)
    assert len(mid.tracks) > 0
