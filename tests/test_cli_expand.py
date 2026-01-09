"""Tests for the expand command."""

from __future__ import annotations

import json
from pathlib import Path

from pianist.cli import main
from pianist.schema import validate_composition_dict


def test_cli_expand_basic(tmp_path: Path, monkeypatch) -> None:
    """Test expand command with provider."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    # Mock AI provider
    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        # Return expanded composition
        expanded = comp_json.copy()
        expanded["tracks"][0]["events"].append(
            {"type": "note", "start": 32, "duration": 32, "pitches": [62], "velocity": 80}
        )
        return json.dumps(expanded)

    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)

    # With provider, should expand composition
    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "--target-length",
            "120",
            "--provider",
            "openrouter",
        ]
    )
    assert rc == 0


def test_cli_expand_with_provider(tmp_path: Path, monkeypatch) -> None:
    """Test expand command with AI provider."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        # Return expanded composition
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                        for i in range(120)
                    ]
                }
            ],
        }
        return json.dumps(expanded)

    # Double-patch pattern
    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)
    import pianist.cli.commands.expand

    monkeypatch.setattr(
        pianist.cli.commands.expand, "generate_text_unified", fake_generate_text_unified
    )

    # Use absolute path to avoid output directory resolution
    output_file = output_file.absolute()

    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = captured_stdout = StringIO()

    try:
        rc = main(
            [
                "expand",
                "-i",
                str(input_file),
                "-o",
                str(output_file),
                "--target-length",
                "120",
                "--provider",
                "openrouter",
            ]
        )
    finally:
        sys.stdout = old_stdout

    assert rc == 0, f"Command failed with return code {rc}"
    # The command prints the actual output path to stdout
    stdout_text = captured_stdout.getvalue().strip()
    if stdout_text:
        # Use the path printed by the command (may be versioned)
        actual_output_file = Path(stdout_text.split("\n")[0].strip())
        if actual_output_file.exists():
            output_file = actual_output_file

    # If file still doesn't exist, check if it was written to output directory
    if not output_file.exists():
        # Check output directory structure
        from pianist.cli.util import derive_base_name_from_path, get_output_base_dir

        base_name = derive_base_name_from_path(input_file, "expand-output")
        output_dir = get_output_base_dir(base_name, "expand")
        potential_file = output_dir / output_file.name
        if potential_file.exists():
            output_file = potential_file

    assert output_file.exists(), (
        f"Output file not found. Checked: {output_file}, stdout: {stdout_text[:200] if stdout_text else 'empty'}"
    )

    # Verify output is valid
    data = json.loads(output_file.read_text(encoding="utf-8"))
    validate_composition_dict(data)


def test_cli_expand_with_preserve_motifs(tmp_path: Path, monkeypatch) -> None:
    """Test expand with --preserve-motifs flag."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        # Verify preserve-motifs is in prompt
        assert "preserve" in prompt.lower() or "motif" in prompt.lower()
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                        for i in range(120)
                    ]
                }
            ],
        }
        return json.dumps(expanded)

    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)

    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--target-length",
            "120",
            "--provider",
            "openrouter",
            "--preserve-motifs",
        ]
    )
    assert rc == 0


def test_cli_expand_with_preserve_list(tmp_path: Path, monkeypatch) -> None:
    """Test expand with --preserve flag."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                        for i in range(120)
                    ]
                }
            ],
        }
        return json.dumps(expanded)

    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)

    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--target-length",
            "120",
            "--provider",
            "openrouter",
            "--preserve",
            "motif_1,phrase_A",
        ]
    )
    assert rc == 0


def test_cli_expand_requires_target_length(tmp_path: Path) -> None:
    """Test that expand requires --target-length."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}],
    }

    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    rc = main(["expand", "-i", str(input_file)])
    assert rc != 0  # Should fail - missing --target-length (argparse uses exit code 2)


def test_cli_expand_with_render(tmp_path: Path, monkeypatch) -> None:
    """Test expand with --render flag."""
    comp_json = {
        "title": "Sketch",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [
            {
                "events": [
                    {"type": "note", "start": 0, "duration": 32, "pitches": [60], "velocity": 80}
                ]
            }
        ],
    }

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(comp_json), encoding="utf-8")

    def fake_generate_text_unified(
        *, provider: str, model: str, prompt: str, verbose: bool = False  # noqa: ARG001
    ) -> str:
        expanded = {
            "title": "Expanded",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": i, "duration": 1, "pitches": [60], "velocity": 80}
                        for i in range(120)
                    ]
                }
            ],
        }
        return json.dumps(expanded)

    monkeypatch.setattr("pianist.ai_providers.generate_text_unified", fake_generate_text_unified)

    rc = main(
        [
            "expand",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "--target-length",
            "120",
            "--provider",
            "openrouter",
            "--render",
        ]
    )
    assert rc == 0
    # MIDI file should be created in output directory
    from pathlib import Path

    output_dir = Path("output") / "input" / "expand"
    assert any(output_dir.glob("*.mid"))
