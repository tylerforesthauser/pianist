from __future__ import annotations

import io
from pathlib import Path

from pianist.cli import main
from pianist.entry import main as entry_main


def test_cli_render_with_input_file(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    rc = main(
        [
            "render",
            "--in",
            "examples/model_output.txt",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()


def test_cli_render_with_stdin(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "out.mid"
    text = (Path("examples/model_output.txt")).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    rc = main(["render", "--out", str(out)])
    assert rc == 0
    assert out.exists()


def test_cli_errors_on_missing_input_file(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    rc = main(["render", "--in", "does-not-exist.txt", "--out", str(out)])
    assert rc == 1


def test_entry_point_imports_main() -> None:
    """Test that entry point module correctly imports and exposes main."""
    # Verify entry_main is the same function as cli.main
    assert entry_main is main
    # Verify it's callable
    assert callable(entry_main)

