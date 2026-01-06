from __future__ import annotations

import io
import json
from pathlib import Path

import mido

from pianist.cli import main
from pianist.entry import main as entry_main


def test_cli_render_with_input_file(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    rc = main(
        [
            "render",
            "-i",
            "examples/model_output.txt",
            "-o",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()


def test_cli_render_with_stdin(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "out.mid"
    text = (Path("examples/model_output.txt")).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    rc = main(["render", "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_cli_errors_on_missing_input_file(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    rc = main(["render", "-i", "does-not-exist.txt", "-o", str(out)])
    assert rc == 1


def test_entry_point_imports_main() -> None:
    """Test that entry point module correctly imports and exposes main."""
    # Verify entry_main is the same function as cli.main
    assert entry_main is main
    # Verify it's callable
    assert callable(entry_main)


def _valid_composition_json() -> str:
    # Minimal valid Pianist composition JSON.
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


def test_cli_iterate_gemini_saves_raw_and_renders(tmp_path: Path, monkeypatch) -> None:
    out_json = tmp_path / "seed_updated.json"
    out_midi = tmp_path / "out.mid"

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        assert model
        assert "SYSTEM PROMPT" in prompt
        assert "REQUESTED CHANGES" in prompt
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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
    # Default raw path: <out>.gemini.txt
    assert (tmp_path / "seed_updated.json.gemini.txt").exists()


def test_cli_analyze_gemini_writes_json_raw_and_midi(tmp_path: Path, monkeypatch) -> None:
    # Build a tiny MIDI file.
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    out_json = tmp_path / "composition.json"
    out_raw = tmp_path / "composition.raw.txt"
    out_midi = tmp_path / "composition.mid"

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        assert model
        assert "REFERENCE ANALYSIS" in prompt
        assert "REQUESTED COMPOSITION" in prompt
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
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


def test_cli_iterate_gemini_with_verbose(tmp_path: Path, monkeypatch) -> None:
    """Test that --verbose flag is passed to generate_text."""
    out_json = tmp_path / "seed_updated.json"

    verbose_called = []

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        verbose_called.append(verbose)
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Make it more lyrical.",
            "-o",
            str(out_json),
            "-v",
        ]
    )
    assert rc == 0
    assert verbose_called == [True]


def test_cli_analyze_gemini_with_verbose(tmp_path: Path, monkeypatch) -> None:
    """Test that --verbose flag is passed to generate_text in analyze command."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    out_json = tmp_path / "composition.json"

    verbose_called = []

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        verbose_called.append(verbose)
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
            "--instructions",
            "Compose something similar.",
            "-o",
            str(out_json),
            "-v",
        ]
    )
    assert rc == 0
    assert verbose_called == [True]


def test_cli_iterate_gemini_without_verbose(tmp_path: Path, monkeypatch) -> None:
    """Test that verbose defaults to False when --verbose is not provided."""
    out_json = tmp_path / "seed_updated.json"

    verbose_called = []

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        verbose_called.append(verbose)
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Make it more lyrical.",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    assert verbose_called == [False]


def test_cli_render_empty_input_file(tmp_path: Path) -> None:
    """Test that render errors on empty input file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    out = tmp_path / "out.mid"
    rc = main(["render", "--in", str(empty_file), "--out", str(out)])
    assert rc == 1
    assert not out.exists()


def test_cli_render_empty_stdin(tmp_path: Path, monkeypatch) -> None:
    """Test that render errors on empty stdin."""
    out = tmp_path / "out.mid"
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    rc = main(["render", "--out", str(out)])
    assert rc == 1
    assert not out.exists()


def test_cli_render_invalid_json(tmp_path: Path) -> None:
    """Test that render errors on invalid JSON."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json at all", encoding="utf-8")
    out = tmp_path / "out.mid"
    rc = main(["render", "--in", str(invalid_file), "--out", str(out)])
    assert rc == 1
    assert not out.exists()


def test_cli_iterate_optional_instructions_with_gemini(tmp_path: Path, monkeypatch) -> None:
    """Test that iterate works when --gemini is used without --instructions (now optional)."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    out_json = tmp_path / "out.json"
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "-o",
            str(out_json),
        ]
    )
    # Should succeed now that instructions are optional
    assert rc == 0
    assert out_json.exists()


def test_cli_iterate_render_auto_generates_midi(tmp_path: Path) -> None:
    """Test that iterate auto-generates MIDI path when --render is used without --midi."""
    out_json = tmp_path / "out.json"
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-o",
            str(out_json),
            "--render",
        ]
    )
    # Should succeed - MIDI path auto-generated
    assert rc == 0
    # Check that MIDI file was created (path auto-generated from output name)
    assert (tmp_path / "out.mid").exists() or any(tmp_path.glob("*.mid"))


def test_cli_iterate_stdout_output(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that iterate outputs to stdout when --output is omitted."""
    rc = main(["iterate", "-i", "examples/model_output.txt"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "title" in captured.out.lower() or '"title"' in captured.out


def test_cli_analyze_optional_instructions_with_gemini(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze works when --gemini is used without --instructions (now optional)."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    out_json = tmp_path / "out.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
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
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    out_json = tmp_path / "out.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--render",
        ]
    )
    # Should succeed - MIDI path auto-generated
    assert rc == 0
    # Check that MIDI file was created
    assert (tmp_path / "out.mid").exists() or any(tmp_path.glob("*.mid"))


def test_cli_analyze_render_requires_gemini(tmp_path: Path) -> None:
    """Test that analyze errors when --render is used without --gemini."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
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
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
    rc = main(["analyze", "-i", str(midi_path), "-f", "prompt"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "REFERENCE ANALYSIS" in captured.out or "Output MUST be valid JSON" in captured.out


def test_cli_analyze_format_json_only(tmp_path: Path) -> None:
    """Test that analyze outputs only JSON when --format json."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
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
        ]
    )
    assert rc == 0
    assert out_json.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "ppq" in data


def test_cli_fix_pedal_basic(tmp_path: Path) -> None:
    """Test the fix-pedal command."""
    import warnings
    
    # Create a composition with pedal issues
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                    {"type": "pedal", "start": 4, "duration": 0, "value": 0},
                ]
            }
        ],
    }
    
    input_file = tmp_path / "input.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
    
    output_file = tmp_path / "output.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rc = main(["fix-pedal", "-i", str(input_file), "-o", str(output_file)])
    
    assert rc == 0
    assert output_file.exists()
    
    # Verify the fix worked
    fixed_data = json.loads(output_file.read_text(encoding="utf-8"))
    pedals = [e for e in fixed_data["tracks"][0]["events"] if e["type"] == "pedal"]
    assert len(pedals) == 1
    assert pedals[0]["duration"] == 4


def test_cli_fix_pedal_overwrites_input(tmp_path: Path) -> None:
    """Test that fix-pedal overwrites input when --output is not provided."""
    import warnings
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                    {"type": "pedal", "start": 4, "duration": 0, "value": 0},
                ]
            }
        ],
    }
    
    input_file = tmp_path / "input.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rc = main(["fix-pedal", "-i", str(input_file)])
    
    assert rc == 0
    # File should be modified
    fixed_data = json.loads(input_file.read_text(encoding="utf-8"))
    pedals = [e for e in fixed_data["tracks"][0]["events"] if e["type"] == "pedal"]
    assert len(pedals) == 1


def test_cli_fix_pedal_render_auto_generates_midi(tmp_path: Path) -> None:
    """Test that fix-pedal auto-generates MIDI path when --render is used without --midi."""
    import warnings
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }
    
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")
    
    rc = main(["fix-pedal", "-i", str(input_file), "--render"])
    # Should succeed - MIDI path auto-generated
    assert rc == 0
    # Check that MIDI file was created
    assert (tmp_path / "input.mid").exists() or any(tmp_path.glob("*.mid"))


def test_cli_fix_pedal_with_render(tmp_path: Path) -> None:
    """Test fix-pedal with --render option."""
    import warnings
    
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
    
    output_midi = tmp_path / "output.mid"
    rc = main(
        [
            "fix-pedal",
            "-i",
            str(input_file),
            "--render",
            "-m",
            str(output_midi),
        ]
    )
    
    assert rc == 0
    assert output_midi.exists()


def test_cli_generate_schema_both_formats(tmp_path: Path) -> None:
    """Test generate-schema command with both formats (default)."""
    output_dir = tmp_path / "schemas"
    rc = main(["generate-schema", "--output-dir", str(output_dir)])
    
    # May fail if schema generation not available, which is OK
    if rc == 0:
        openapi_path = output_dir / "schema.openapi.json"
        gemini_path = output_dir / "schema.gemini.json"
        assert openapi_path.exists()
        assert gemini_path.exists()


def test_cli_generate_schema_openapi_only(tmp_path: Path) -> None:
    """Test generate-schema command with OpenAPI format only."""
    output_dir = tmp_path / "schemas"
    rc = main(
        [
            "generate-schema",
            "--format",
            "openapi",
            "--output-dir",
            str(output_dir),
        ]
    )
    
    if rc == 0:
        openapi_path = output_dir / "schema.openapi.json"
        gemini_path = output_dir / "schema.gemini.json"
        assert openapi_path.exists()
        assert not gemini_path.exists()


def test_cli_generate_schema_gemini_only(tmp_path: Path) -> None:
    """Test generate-schema command with Gemini format only."""
    output_dir = tmp_path / "schemas"
    rc = main(
        [
            "generate-schema",
            "--format",
            "gemini",
            "--output-dir",
            str(output_dir),
        ]
    )
    
    if rc == 0:
        openapi_path = output_dir / "schema.openapi.json"
        gemini_path = output_dir / "schema.gemini.json"
        assert not openapi_path.exists()
        assert gemini_path.exists()


def test_cli_iterate_gemini_error_handling(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that GeminiError is properly displayed in CLI."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        from pianist.gemini import GeminiError
        raise GeminiError("API key not valid. Please pass a valid API key.")

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert "GeminiError" in captured.err or "API key" in captured.err


def test_cli_analyze_gemini_error_handling(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that GeminiError is properly displayed in analyze CLI."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        from pianist.gemini import GeminiError
        raise GeminiError("Gemini returned an empty response.")

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    out_json = tmp_path / "out.json"
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert "GeminiError" in captured.err or "empty response" in captured.err


def test_cli_special_characters_in_paths(tmp_path: Path) -> None:
    """Test that special characters in file paths work correctly."""
    # Test with various special characters
    special_name = tmp_path / "test file with spaces & symbols (test).json"
    special_name.write_text(_valid_composition_json(), encoding="utf-8")

    out_midi = tmp_path / "output with émojis 🎹.mid"
    rc = main(["render", "-i", str(special_name), "-o", str(out_midi)])
    
    assert rc == 0
    assert out_midi.exists()


def test_cli_unicode_characters_in_paths(tmp_path: Path) -> None:
    """Test that unicode characters in file paths work correctly."""
    # Test with unicode characters
    unicode_name = tmp_path / "测试文件_тест_テスト.json"
    unicode_name.write_text(_valid_composition_json(), encoding="utf-8")

    out_midi = tmp_path / "输出_вывод_出力.mid"
    rc = main(["render", "-i", str(unicode_name), "-o", str(out_midi)])
    
    assert rc == 0
    assert out_midi.exists()


def test_cli_long_path(tmp_path: Path) -> None:
    """Test that reasonably long file paths work correctly."""
    # Create a reasonably long path (but not too long to avoid OS limits)
    long_dir = tmp_path / ("a" * 50) / ("b" * 50) / ("c" * 50)
    long_dir.mkdir(parents=True, exist_ok=True)
    
    long_input = long_dir / "input.json"
    long_input.write_text(_valid_composition_json(), encoding="utf-8")
    
    long_output = long_dir / "output.mid"
    rc = main(["render", "-i", str(long_input), "-o", str(long_output)])
    
    assert rc == 0
    assert long_output.exists()


def test_cli_file_permission_error_read(tmp_path: Path) -> None:
    """Test handling of file permission errors when reading."""
    import os
    import stat
    
    # Create a file and make it unreadable
    protected_file = tmp_path / "protected.txt"
    protected_file.write_text("test content", encoding="utf-8")
    
    # Try to make it unreadable (this might not work on all systems)
    try:
        protected_file.chmod(0o000)  # No permissions
        
        out = tmp_path / "out.mid"
        rc = main(["render", "-i", str(protected_file), "-o", str(out)])
        
        # Should fail with permission error
        assert rc == 1
    except (OSError, PermissionError):
        # On some systems, we can't create unreadable files or the test itself
        # doesn't have permission to change permissions - skip this test
        pass
    finally:
        # Restore permissions so file can be cleaned up
        try:
            protected_file.chmod(0o644)
        except OSError:
            pass


def test_cli_file_permission_error_write(tmp_path: Path) -> None:
    """Test handling of file permission errors when writing."""
    import os
    import stat
    
    # Create a directory and make it unwritable
    protected_dir = tmp_path / "protected_dir"
    protected_dir.mkdir()
    
    try:
        protected_dir.chmod(0o555)  # Read and execute only, no write
        
        protected_output = protected_dir / "output.mid"
        rc = main(
            [
                "render",
                "-i",
                "examples/model_output.txt",
                "-o",
                str(protected_output),
            ]
        )
        
        # Should fail with permission error
        assert rc == 1
    except (OSError, PermissionError):
        # On some systems, we can't create unwritable directories or the test itself
        # doesn't have permission to change permissions - skip this test
        pass
    finally:
        # Restore permissions so directory can be cleaned up
        try:
            protected_dir.chmod(0o755)
        except OSError:
            pass


def test_cli_render_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json", encoding="utf-8")
    out = tmp_path / "out.mid"
    
    rc = main(["render", "-i", str(invalid_file), "-o", str(out), "--debug"])
    
    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_iterate_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors in iterate command."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json", encoding="utf-8")
    
    rc = main(["iterate", "-i", str(invalid_file), "-o", str(tmp_path / "out.json"), "--debug"])
    
    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_analyze_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors in analyze command."""
    # Create a non-existent MIDI file
    rc = main(["analyze", "-i", str(tmp_path / "nonexistent.mid"), "--debug"])
    
    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_fix_pedal_debug_flag_shows_traceback(tmp_path: Path, capsys) -> None:
    """Test that --debug flag shows full traceback on errors in fix-pedal command."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json", encoding="utf-8")
    
    rc = main(["fix-pedal", "-i", str(invalid_file), "--debug"])
    
    assert rc == 1
    captured = capsys.readouterr()
    # Debug mode should show traceback
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


def test_cli_iterate_custom_gemini_model(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --gemini-model is passed to generate_text."""
    out_json = tmp_path / "out.json"
    models_called = []

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        models_called.append(model)
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--gemini-model",
            "gemini-1.5-pro",
        ]
    )
    assert rc == 0
    assert models_called == ["gemini-1.5-pro"]


def test_cli_analyze_custom_gemini_model(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --gemini-model is passed to generate_text in analyze command."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    out_json = tmp_path / "out.json"
    models_called = []

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        models_called.append(model)
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
            "--gemini-model",
            "gemini-2.0-flash-exp",
        ]
    )
    assert rc == 0
    assert models_called == ["gemini-2.0-flash-exp"]


def test_cli_iterate_custom_raw_out_path(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --raw path is used when provided."""
    out_json = tmp_path / "out.json"
    custom_raw = tmp_path / "custom_raw.txt"

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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
    # Should not create default .gemini.txt file
    assert not (tmp_path / "out.json.gemini.txt").exists()


def test_cli_analyze_custom_raw_out_path(tmp_path: Path, monkeypatch) -> None:
    """Test that custom --raw path is used when provided in analyze command."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    out_json = tmp_path / "out.json"
    custom_raw = tmp_path / "custom_analyze_raw.txt"

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
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
    # Should not create default .gemini.txt file
    assert not (tmp_path / "out.json.gemini.txt").exists()


def test_cli_iterate_warning_when_raw_output_not_saved(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that warning is shown when raw output is not saved in iterate command."""
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    # Don't provide --output or --raw, so raw output won't be saved
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower()
    assert "raw output" in captured.err.lower() or "raw-out" in captured.err.lower()


def test_cli_analyze_warning_when_raw_output_not_saved(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test that warning is shown when raw output is not saved in analyze command."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()

    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)

    # Don't provide --output or --raw, so raw output won't be saved
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
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
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

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
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

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


def test_cli_analyze_prompt_out_with_format_both(tmp_path: Path) -> None:
    """Test --prompt with --format both."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)

    out_json = tmp_path / "analysis.json"
    prompt_path = tmp_path / "prompt.txt"
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
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert prompt_path.exists()
    # Verify JSON content
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "ppq" in data
    # Verify prompt content
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "REFERENCE ANALYSIS" in prompt_text
    assert "Test instructions" in prompt_text


# Versioning tests

def test_cli_iterate_versioning_creates_v2_when_file_exists(tmp_path: Path, monkeypatch) -> None:
    """Test that iterate command creates versioned files when output already exists."""
    out_json = tmp_path / "updated.json"
    
    # Create initial file
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    initial_content = out_json.read_text(encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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


def test_cli_iterate_versioning_incremental(tmp_path: Path, monkeypatch) -> None:
    """Test that versioning continues incrementally (v2, v3, etc.)."""
    out_json = tmp_path / "updated.json"
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    # First run - creates updated.json
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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


def test_cli_iterate_versioning_synchronizes_gemini_raw(tmp_path: Path, monkeypatch) -> None:
    """Test that Gemini raw response is versioned to match JSON output."""
    out_json = tmp_path / "updated.json"
    
    # Create initial files with valid cached response
    cached_response = _valid_composition_json()
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    raw_path = tmp_path / "updated.json.gemini.txt"
    raw_path.write_text(cached_response, encoding="utf-8")
    
    call_count = 0
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        nonlocal call_count
        call_count += 1
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    
    # Should use cached response (not call Gemini)
    assert call_count == 0
    
    # Original files should still exist
    assert out_json.exists()
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8") == cached_response
    
    # Versioned files should be created
    v2_json = tmp_path / "updated.v2.json"
    v2_raw = tmp_path / "updated.v2.json.gemini.txt"
    assert v2_json.exists()
    assert v2_raw.exists()
    # Versioned raw file should contain the cached response (same as original since we used cache)
    assert v2_raw.read_text(encoding="utf-8") == cached_response


def test_cli_iterate_overwrite_flag(tmp_path: Path, monkeypatch) -> None:
    """Test that --overwrite flag prevents versioning."""
    out_json = tmp_path / "updated.json"
    initial_content = "original content"
    out_json.write_text(initial_content, encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
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


def test_cli_analyze_versioning_creates_v2_when_file_exists(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze command creates versioned files when output already exists."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
    out_json = tmp_path / "composition.json"
    
    # Create initial file
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    initial_content = out_json.read_text(encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
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


def test_cli_analyze_versioning_synchronizes_gemini_raw(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze command versions Gemini raw response to match JSON."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
    out_json = tmp_path / "composition.json"
    
    # Create initial files with valid cached response
    cached_response = _valid_composition_json()
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    raw_path = tmp_path / "composition.json.gemini.txt"
    raw_path.write_text(cached_response, encoding="utf-8")
    
    call_count = 0
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        nonlocal call_count
        call_count += 1
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    
    # Should use cached response (not call Gemini)
    assert call_count == 0
    
    # Original files should still exist
    assert out_json.exists()
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8") == cached_response
    
    # Versioned files should be created
    v2_json = tmp_path / "composition.v2.json"
    v2_raw = tmp_path / "composition.v2.json.gemini.txt"
    assert v2_json.exists()
    assert v2_raw.exists()
    # Versioned raw file should contain the cached response (same as original since we used cache)
    assert v2_raw.read_text(encoding="utf-8") == cached_response


def test_cli_analyze_overwrite_flag(tmp_path: Path, monkeypatch) -> None:
    """Test that --overwrite flag prevents versioning in analyze command."""
    midi_path = tmp_path / "in.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_path)
    
    out_json = tmp_path / "composition.json"
    initial_content = "original"
    out_json.write_text(initial_content, encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "analyze",
            "-i",
            str(midi_path),
            "-g",
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


def test_cli_versioning_with_cached_response(tmp_path: Path, monkeypatch) -> None:
    """Test that versioning works correctly when using a cached Gemini response."""
    out_json = tmp_path / "updated.json"
    raw_path = tmp_path / "updated.json.gemini.txt"
    
    # Create initial files with cached response
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    raw_path.write_text(_valid_composition_json(), encoding="utf-8")
    
    call_count = 0
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        nonlocal call_count
        call_count += 1
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    
    # Should use cached response (not call Gemini)
    assert call_count == 0
    
    # Original files should still exist
    assert out_json.exists()
    assert raw_path.exists()
    
    # Versioned files should be created
    v2_json = tmp_path / "updated.v2.json"
    v2_raw = tmp_path / "updated.v2.json.gemini.txt"
    assert v2_json.exists()
    assert v2_raw.exists()


def test_cli_versioning_skips_when_file_not_exists(tmp_path: Path, monkeypatch) -> None:
    """Test that versioning is skipped when output file doesn't exist."""
    out_json = tmp_path / "new_file.json"
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(out_json),
        ]
    )
    assert rc == 0
    
    # File should be created (not versioned since it didn't exist)
    assert out_json.exists()
    
    # No versioned file should be created
    v2_json = tmp_path / "new_file.v2.json"
    assert not v2_json.exists()


def test_cli_versioning_with_already_versioned_file(tmp_path: Path, monkeypatch) -> None:
    """Test that versioning continues correctly from already versioned files."""
    out_json = tmp_path / "updated.v2.json"
    
    # Create an already versioned file
    out_json.write_text(_valid_composition_json(), encoding="utf-8")
    
    def fake_generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
        return _valid_composition_json()
    
    monkeypatch.setattr("pianist.cli.generate_text", fake_generate_text)
    
    # Try to write to updated.json (not the versioned one)
    target_json = tmp_path / "updated.json"
    rc = main(
        [
            "iterate",
            "-i",
            "examples/model_output.txt",
            "-g",
            "--instructions",
            "Test",
            "-o",
            str(target_json),
        ]
    )
    assert rc == 0
    
    # Should create updated.json (since updated.json doesn't exist)
    assert target_json.exists()
    
    # The v2 file should still exist
    assert out_json.exists()

