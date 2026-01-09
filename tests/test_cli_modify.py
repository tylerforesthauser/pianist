"""Tests for the modify command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import mido

from pianist.cli import main
from pianist.schema import NoteEvent, validate_composition_dict

if TYPE_CHECKING:
    from pathlib import Path


# Import shared test helper from conftest
from conftest import valid_composition_json as _valid_composition_json


def _write_test_midi(path: Path) -> None:
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)

    tr.append(mido.MetaMessage("track_name", name="Piano", time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))

    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_on", note=64, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=0))

    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(path)


def test_cli_modify_supports_transpose_and_prompt_out(tmp_path: Path, monkeypatch) -> None:
    """Test modify with transpose and prompt output."""

    # Mock AI provider - return composition with transposed notes [62, 66]
    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return (
            "{"
            '"title":"Test",'
            '"bpm":120,'
            '"time_signature":{"numerator":4,"denominator":4},'
            '"ppq":480,'
            '"tracks":[{"name":"Piano","channel":0,"program":0,"events":['
            '{"type":"note","start":0,"duration":1,"pitches":[62,66],"velocity":80}'
            "]}]"
            "}"
        )

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    # First import MIDI
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    imported_json = tmp_path / "imported.json"
    rc = main(["import", "-i", str(midi_path), "-o", str(imported_json)])
    assert rc == 0

    # Then modify with transpose
    out_json = tmp_path / "seed.json"
    prompt_path = tmp_path / "prompt.txt"
    rc = main(
        [
            "modify",
            "-i",
            str(imported_json),
            "-o",
            str(out_json),
            "--transpose",
            "2",
            "-p",
            str(prompt_path),
            "--instructions",
            "Make it more lyrical and add an 8-beat coda.",
            "--provider",
            "openrouter",
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert prompt_path.exists()

    # JSON output is valid and transposed.
    data = json.loads(out_json.read_text(encoding="utf-8"))
    comp = validate_composition_dict(data)
    note = next(
        e for e in comp.tracks[0].events if isinstance(e, NoteEvent) and e.pitches == [62, 66]
    )
    assert note is not None

    # Prompt includes requested instructions and seed marker text.
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "REQUESTED CHANGES" in prompt
    assert "Make it more lyrical and add an 8-beat coda." in prompt


def test_cli_modify_accepts_json_input_and_empty_events(tmp_path: Path, monkeypatch) -> None:
    """Test modify with JSON input and empty events."""

    # Mock AI provider - preserve the input composition's title and empty events
    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return (
            "{"
            '"title":"Empty Seed",'
            '"bpm":120,'
            '"time_signature":{"numerator":4,"denominator":4},'
            '"ppq":480,'
            '"tracks":[{"name":"Piano","channel":0,"program":0,"events":[]}]'
            "}"
        )

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    # A minimal, valid composition with no events.
    seed = {
        "title": "Empty Seed",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"name": "Piano", "program": 0, "channel": 0, "events": []}],
    }
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(seed), encoding="utf-8")

    out_json = tmp_path / "seed_out.json"
    rc = main(["modify", "-i", str(seed_path), "-o", str(out_json), "--provider", "openrouter"])
    assert rc == 0
    data = json.loads(out_json.read_text(encoding="utf-8"))
    comp = validate_composition_dict(data)
    assert comp.title == "Empty Seed"
    assert comp.tracks[0].events == []


def test_cli_modify_provider_saves_raw_and_renders(tmp_path: Path, monkeypatch) -> None:
    """Test modify with AI provider saves raw response and renders MIDI."""
    out_json = tmp_path / "seed_updated.json"
    out_midi = tmp_path / "out.mid"

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        assert model
        assert "SYSTEM PROMPT" in prompt
        assert "REQUESTED CHANGES" in prompt
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Make it more lyrical.",
            "-o",
            str(out_json),
            "--render",
            "-m",
            str(out_midi),
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert out_midi.exists()
    # Default raw path: <out>.openrouter.txt
    assert (tmp_path / "seed_updated.json.openrouter.txt").exists()


def test_cli_modify_provider_with_verbose(tmp_path: Path, monkeypatch) -> None:
    """Test that --verbose flag is passed to generate_text."""
    out_json = tmp_path / "seed_updated.json"

    verbose_called = []

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        verbose_called.append(verbose)
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Make it more lyrical.",
            "-o",
            str(out_json),
            "-v",
        ]
    )
    assert rc == 0
    assert verbose_called == [True]


def test_cli_modify_provider_without_verbose(tmp_path: Path, monkeypatch) -> None:
    """Test that verbose defaults to False when not specified."""
    out_json = tmp_path / "seed_updated.json"

    verbose_called = []

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        verbose_called.append(verbose)
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Make it more lyrical.",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    assert verbose_called == [False]


def test_cli_modify_optional_instructions_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test that modify works when --provider is used without --instructions."""

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "-o",
            str(out_json),
        ]
    )
    # Should succeed now that instructions are optional
    assert rc == 0
    assert out_json.exists()


def test_cli_modify_render_auto_generates_midi(tmp_path: Path) -> None:
    """Test that modify auto-generates MIDI path when --render is used without --midi."""
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(_valid_composition_json(), encoding="utf-8")

    rc = main(
        [
            "modify",
            "-i",
            str(seed_path),
            "--render",
        ]
    )
    # Should succeed - MIDI path auto-generated
    assert rc == 0
    # Check that MIDI file was created in output directory
    from pathlib import Path

    output_dir = Path("output") / "seed" / "modify"
    assert (output_dir / "seed.mid").exists() or any(output_dir.glob("*.mid"))


def test_cli_modify_stdout_output(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that modify outputs to stdout when --output is omitted."""

    # Mock AI provider
    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(["modify", "-i", "examples/model_output.txt", "--provider", "openrouter"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "title" in captured.out.lower() or '"title"' in captured.out


def test_cli_modify_provider_error_handling(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that AI provider errors are properly displayed in CLI."""

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        from pianist.ai_providers import OpenRouterError

        raise OpenRouterError("API key not valid. Please pass a valid API key.")

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
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
        "OpenRouterError" in captured.err or "API key" in captured.err or "error:" in captured.err
    )


def test_cli_modify_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors in modify command."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json", encoding="utf-8")

    rc = main(["modify", "-i", str(invalid_file), "-o", str(tmp_path / "out.json"), "--debug"])

    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_modify_custom_model(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --model is passed to generate_text."""
    out_json = tmp_path / "out.json"
    models_called = []

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        models_called.append(model)
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--model",
            "gemini-1.5-pro",
        ]
    )
    assert rc == 0
    assert models_called == ["gemini-1.5-pro"]


def test_cli_modify_custom_raw_out_path(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --raw path is used when provided."""
    out_json = tmp_path / "out.json"
    custom_raw = tmp_path / "custom_raw.txt"

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
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


def test_cli_modify_warning_when_raw_output_not_saved(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that warning is shown when raw output is not saved in modify command."""

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    # Don't provide --output or --raw, so raw output won't be saved
    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
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


def test_cli_modify_versioning_creates_v2_when_file_exists(tmp_path: Path, monkeypatch) -> None:
    """Test that modify command creates versioned files when output already exists."""
    out_json = tmp_path / "updated.json"

    # Create initial file
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    initial_content = out_json.read_text(encoding="utf-8")

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Make it different.",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0

    # Original file should still exist with original content
    assert out_json.exists()
    assert out_json.read_text(encoding="utf-8") == initial_content

    # Versioned file should be created
    v2_json = tmp_path / "updated.v2.json"
    assert v2_json.exists()
    assert v2_json.read_text(encoding="utf-8") != initial_content


def test_cli_modify_versioning_incremental(tmp_path: Path, monkeypatch) -> None:
    """Test that versioning continues incrementally (v2, v3, etc.)."""
    out_json = tmp_path / "updated.json"

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    # First run - creates updated.json
    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "First",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    assert out_json.exists()

    # Second run - creates updated.v2.json
    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Second",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    v2_json = tmp_path / "updated.v2.json"
    assert v2_json.exists()

    # Third run - creates updated.v3.json
    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
            "--provider",
            "openrouter",
            "--instructions",
            "Third",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    v3_json = tmp_path / "updated.v3.json"
    assert v3_json.exists()

    # All versions should exist
    assert out_json.exists()
    assert v2_json.exists()
    assert v3_json.exists()


def test_cli_modify_versioning_synchronizes_provider_raw(tmp_path: Path, monkeypatch) -> None:
    """Test that provider raw response is versioned to match JSON output."""
    out_json = tmp_path / "updated.json"

    # Create initial files with valid cached response
    cached_response = _valid_composition_json()
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    raw_path = tmp_path / "updated.json.openrouter.txt"
    raw_path.write_text(cached_response, encoding="utf-8")

    call_count = 0

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        nonlocal call_count
        call_count += 1
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
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
    v2_json = tmp_path / "updated.v2.json"
    v2_raw = tmp_path / "updated.v2.json.openrouter.txt"
    assert v2_json.exists()
    assert v2_raw.exists()
    # Versioned raw file should contain the cached response (same as original since we used cache)
    assert v2_raw.read_text(encoding="utf-8") == cached_response


def test_cli_modify_overwrite_flag(tmp_path: Path, monkeypatch) -> None:
    """Test that --overwrite flag prevents versioning."""
    out_json = tmp_path / "updated.json"
    initial_content = "original content"
    out_json.write_text(initial_content, encoding="utf-8")

    def fake_generate_text_unified(
        *,
        provider: str,
        model: str,
        prompt: str,
        verbose: bool = False,
    ) -> str:
        return _valid_composition_json()

    # Patch both locations
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.modify

    monkeypatch.setattr(
        pianist.cli.commands.modify, "generate_text_unified", fake_generate_text_unified
    )

    rc = main(
        [
            "modify",
            "-i",
            "examples/model_output.txt",
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

    # Original file should be overwritten (not versioned)
    assert out_json.exists()
    assert out_json.read_text(encoding="utf-8") != initial_content

    # No versioned file should be created
    v2_json = tmp_path / "updated.v2.json"
    assert not v2_json.exists()
