from __future__ import annotations

import io
from pathlib import Path

from pianist.cli import main


def test_cli_render_with_input_file_music21(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    rc = main(
        [
            "render",
            "--backend",
            "music21",
            "--in",
            "examples/model_output.txt",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()


def test_cli_render_with_stdin_mido(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "out.mid"
    text = (Path("examples/model_output.txt")).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    rc = main(["render", "--backend", "mido", "--out", str(out)])
    assert rc == 0
    assert out.exists()


def test_cli_errors_on_missing_input_file(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    rc = main(["render", "--in", "does-not-exist.txt", "--out", str(out)])
    assert rc == 1

