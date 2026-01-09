"""Tests for the analyze command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import mido

from pianist.cli import main

if TYPE_CHECKING:
    from pathlib import Path


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


def _write_test_midi(path: Path) -> None:
    """Create a minimal test MIDI file."""
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(path)


def test_cli_analyze_gemini_writes_json_raw_and_midi(tmp_path: Path, monkeypatch) -> None:
    """Test analyze with AI provider writes JSON, raw response, and MIDI."""
    # Build a tiny MIDI file.
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "composition.json"
    out_raw = tmp_path / "composition.raw.txt"
    out_midi = tmp_path / "composition.mid"

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        assert model
        assert "REFERENCE ANALYSIS" in prompt
        assert "REQUESTED COMPOSITION" in prompt
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Compose something similar.",
            "-o",
            str(out_json),
            "-r",
            str(out_raw),
            "--render",
            "-m",
            str(out_midi),
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert out_raw.exists()
    assert out_midi.exists()


def test_cli_analyze_with_provider_verbose(tmp_path: Path, monkeypatch) -> None:
    """Test that --verbose flag is passed to generate_text in analyze command."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "composition.json"

    verbose_called = []

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        verbose_called.append(verbose)
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Compose something similar.",
            "-o",
            str(out_json),
            "-v",
        ]
    )
    assert rc == 0
    assert verbose_called == [True]


def test_cli_analyze_optional_instructions_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze works when --provider is used without --instructions."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "-o",
            str(out_json),
        ]
    )
    # Should succeed now that instructions are optional
    assert rc == 0
    assert out_json.exists()


def test_cli_analyze_render_auto_generates_midi(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze auto-generates MIDI path when --render is used without --midi."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--render",
        ]
    )
    # Should succeed - MIDI path auto-generated
    assert rc == 0
    # Check that MIDI file was created in output directory
    from pathlib import Path

    output_dir = Path("output") / "in" / "analyze"
    assert any(output_dir.glob("*.mid"))


def test_cli_analyze_render_requires_provider(tmp_path: Path) -> None:
    """Test that analyze errors when --render is used without --provider."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--render",
            "-m",
            str(tmp_path / "out.mid"),
        ]
    )
    assert rc == 1


def test_cli_analyze_rejects_non_midi_file(tmp_path: Path) -> None:
    """Test that analyze errors when input is not a MIDI file."""
    text_file = tmp_path / "not_midi.txt"
    text_file.write_text("not a midi file", encoding="utf-8")

    rc = main(["analyze", "-i", str(text_file)])
    assert rc == 1


def test_cli_analyze_format_prompt_stdout(tmp_path: Path, capsys) -> None:
    """Test that analyze outputs prompt to stdout when --format prompt and no --out."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    rc = main(["analyze", "-i", str(midi_path), "-f", "prompt"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "REFERENCE ANALYSIS" in captured.out or "Output MUST be valid JSON" in captured.out


def test_cli_analyze_format_json_only(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze outputs only JSON when --format json."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        # Return minimal valid JSON for AI insights
        return '{"suggested_name": "Test", "suggested_style": "Classical", "suggested_description": "A test composition"}'

    # Patch both locations for AI insights
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "analysis.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-f",
            "json",
            "-o",
            str(out_json),
            "--ai-provider",
            "openrouter",
        ]
    )
    assert rc == 0
    assert out_json.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    # New structure has filename, filepath, quality, technical, musical_analysis, improvement_suggestions, ai_insights
    assert "filename" in data
    assert "filepath" in data
    assert "technical" in data


def test_cli_analyze_error_handling(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that AI provider errors are properly displayed in analyze CLI."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        from pianist.ai_providers import OpenRouterError

        raise OpenRouterError("AI provider returned an empty response.")

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert (
        "OpenRouterError" in captured.err
        or "empty response" in captured.err
        or "error:" in captured.err
    )


def test_cli_analyze_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors in analyze command."""
    # Create a non-existent MIDI file
    rc = main(["analyze", "-i", str(tmp_path / "nonexistent.mid"), "--debug"])

    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_analyze_custom_model(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --model is passed to generate_text in analyze command."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "out.json"
    models_called = []

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        models_called.append(model)
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--model",
            "gemini-2.0-flash-exp",
        ]
    )
    assert rc == 0
    assert models_called == ["gemini-2.0-flash-exp"]


def test_cli_analyze_custom_raw_out_path(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --raw path is used when provided in analyze command."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "out.json"
    custom_raw = tmp_path / "custom_analyze_raw.txt"

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "-r",
            str(custom_raw),
        ]
    )
    assert rc == 0
    assert custom_raw.exists()
    # Should not create default .openrouter.txt file
    assert not (tmp_path / "out.json.openrouter.txt").exists()


def test_cli_analyze_warning_when_raw_output_not_saved(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that warning is shown when raw output is not saved in analyze command."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    # Don't provide --output or --raw, so raw output won't be saved
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower()
    assert "raw output" in captured.err.lower() or "raw-out" in captured.err.lower()


def test_cli_analyze_prompt_out_with_format_prompt(tmp_path: Path) -> None:
    """Test --prompt with --format prompt."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    prompt_path = tmp_path / "prompt.txt"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-f",
            "prompt",
            "-p",
            str(prompt_path),
            "--instructions",
            "Test instructions",
        ]
    )
    assert rc == 0
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "REFERENCE ANALYSIS" in prompt_text
    assert "Test instructions" in prompt_text


def test_cli_analyze_prompt_out_with_format_json(tmp_path: Path) -> None:
    """Test --prompt with --format json.

    Note: When format is 'json', the prompt section is not executed,
    so --prompt is ignored. This is expected behavior.
    """
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "analysis.json"
    prompt_path = tmp_path / "prompt.txt"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-f",
            "json",
            "-o",
            str(out_json),
            "-p",
            str(prompt_path),
            "--instructions",
            "Test instructions",
        ]
    )
    assert rc == 0
    assert out_json.exists()
    # When format is 'json', prompt section is not executed, so --prompt is ignored
    # This is expected behavior - prompt is only generated when format includes 'prompt'
    assert not prompt_path.exists()


def test_cli_analyze_prompt_out_with_format_both(tmp_path: Path, monkeypatch) -> None:
    """Test --prompt with --format both."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        # Return minimal valid JSON for composition generation
        return _valid_composition_json()

    # Patch both locations for composition generation
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "analysis.json"
    prompt_path = tmp_path / "prompt.txt"
    # Use --provider to enable prompt generation with format "both"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-f",
            "both",
            "-o",
            str(out_json),
            "-p",
            str(prompt_path),
            "--instructions",
            "Test instructions",
            "--provider",
            "openrouter",
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert prompt_path.exists()
    # Verify JSON content - old analysis structure when using --provider
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "ppq" in data  # Old analysis structure
    # Verify prompt content
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "REFERENCE ANALYSIS" in prompt_text
    assert "Test instructions" in prompt_text


def test_cli_analyze_versioning_creates_v2_when_file_exists(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze command creates versioned files when output already exists."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "composition.json"

    # Create initial file
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    initial_content = out_json.read_text(encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0

    # Original file should still exist
    assert out_json.exists()
    assert out_json.read_text(encoding="utf-8") == initial_content

    # Versioned file should be created
    v2_json = tmp_path / "composition.v2.json"
    assert v2_json.exists()


def test_cli_analyze_versioning_synchronizes_raw_response(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze command versions raw response to match JSON."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "composition.json"

    # Create initial files with valid cached response
    cached_response = _valid_composition_json()
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    raw_path = tmp_path / "composition.json.openrouter.txt"
    raw_path.write_text(cached_response, encoding="utf-8")

    call_count = 0

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        nonlocal call_count
        call_count += 1
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0

    # Should use cached response (not call AI provider)
    assert call_count == 0

    # Original files should still exist
    assert out_json.exists()
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8") == cached_response

    # Versioned files should be created
    v2_json = tmp_path / "composition.v2.json"
    v2_raw = tmp_path / "composition.v2.json.openrouter.txt"
    assert v2_json.exists()
    assert v2_raw.exists()
    # Versioned raw file should contain the cached response (same as original since we used cache)
    assert v2_raw.read_text(encoding="utf-8") == cached_response


def test_cli_analyze_overwrite_flag(tmp_path: Path, monkeypatch) -> None:
    """Test that --overwrite flag prevents versioning in analyze command."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "composition.json"
    initial_content = "original"
    out_json.write_text(initial_content, encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.analyze

    monkeypatch.setattr(
        pianist.cli.commands.analyze, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--overwrite",
        ]
    )
    assert rc == 0

    # Original file should be overwritten
    assert out_json.exists()
    assert out_json.read_text(encoding="utf-8") != initial_content

    # No versioned file should be created
    v2_json = tmp_path / "composition.v2.json"
    assert not v2_json.exists()
