"""Tests for the render command."""

from __future__ import annotations

import io
from pathlib import Path

# Import shared test helper from conftest
from conftest import valid_composition_json as _valid_composition_json

from pianist.cli import main


def test_cli_render_with_input_file(tmp_path: Path) -> None:
    """Test render with input file."""
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
    """Test render with stdin input."""
    out = tmp_path / "out.mid"
    text = (Path("examples/model_output.txt")).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    rc = main(["render", "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_cli_render_errors_on_missing_input_file(tmp_path: Path) -> None:
    """Test render errors on missing input file."""
    out = tmp_path / "out.mid"
    rc = main(["render", "-i", "does-not-exist.txt", "-o", str(out)])
    assert rc == 1


def test_cli_render_empty_input_file(tmp_path: Path) -> None:
    """Test render with empty input file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    out = tmp_path / "out.mid"
    rc = main(["render", "-i", str(empty_file), "-o", str(out)])
    assert rc == 1  # Should fail - empty input


def test_cli_render_empty_stdin(tmp_path: Path, monkeypatch) -> None:
    """Test render with empty stdin."""
    out = tmp_path / "out.mid"
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    rc = main(["render", "-o", str(out)])
    assert rc == 1  # Should fail - empty input


def test_cli_render_invalid_json(tmp_path: Path) -> None:
    """Test render with invalid JSON."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("not valid json", encoding="utf-8")
    out = tmp_path / "out.mid"
    rc = main(["render", "-i", str(invalid_file), "-o", str(out)])
    assert rc == 1  # Should fail - invalid JSON


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


def test_cli_render_special_characters_in_paths(tmp_path: Path) -> None:
    """Test that special characters in file paths work correctly."""
    # Test with various special characters
    special_name = tmp_path / "test file with spaces & symbols (test).json"
    special_name.write_text(_valid_composition_json(), encoding="utf-8")

    out_midi = tmp_path / "output with émojis 🎹.mid"
    rc = main(["render", "-i", str(special_name), "-o", str(out_midi)])

    assert rc == 0
    assert out_midi.exists()


def test_cli_render_unicode_characters_in_paths(tmp_path: Path) -> None:
    """Test that unicode characters in file paths work correctly."""
    # Test with unicode characters
    unicode_name = tmp_path / "测试文件_тест_テスト.json"
    unicode_name.write_text(_valid_composition_json(), encoding="utf-8")

    out_midi = tmp_path / "输出_вывод_出力.mid"
    rc = main(["render", "-i", str(unicode_name), "-o", str(out_midi)])

    assert rc == 0
    assert out_midi.exists()


def test_cli_render_long_path(tmp_path: Path) -> None:
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
