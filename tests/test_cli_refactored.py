"""Smoke tests for the refactored CLI structure."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

def test_cli_package_imports() -> None:
    """Test that CLI package imports work correctly."""
    from pianist.cli import main
    from pianist.cli.util import (
        get_output_base_dir,
        resolve_output_path,
        derive_base_name_from_path,
        read_text,
        write_text,
    )
    from pianist.cli.commands import render, import_, modify, fix, diff
    
    # Verify functions are callable
    assert callable(main)
    assert callable(get_output_base_dir)
    assert callable(resolve_output_path)
    assert callable(derive_base_name_from_path)
    assert callable(read_text)
    assert callable(write_text)
    
    # Verify command modules have required functions
    assert callable(render.setup_parser)
    assert callable(render.handle)
    assert callable(import_.setup_parser)
    assert callable(import_.handle)
    assert callable(modify.setup_parser)
    assert callable(modify.handle)
    assert callable(fix.setup_parser)
    assert callable(fix.handle)
    assert callable(diff.setup_parser)
    assert callable(diff.handle)


def test_cli_backward_compatibility_imports() -> None:
    """Test that backward compatibility imports work."""
    from pianist.cli import (
        _DEFAULT_OUTPUT_DIR,
        _derive_base_name_from_path,
        _get_output_base_dir,
        _read_text,
        _write_text,
        generate_text,
        generate_text_unified,
    )
    
    # Verify these exist and are callable
    assert callable(_derive_base_name_from_path)
    assert callable(_get_output_base_dir)
    assert callable(_read_text)
    assert callable(_write_text)
    assert callable(generate_text)
    assert callable(generate_text_unified)
    
    # Verify DEFAULT_OUTPUT_DIR is a Path
    assert isinstance(_DEFAULT_OUTPUT_DIR, Path)


def test_cli_help_via_subprocess() -> None:
    """Test that CLI help works via subprocess (integration smoke test)."""
    result = subprocess.run(
        [sys.executable, "-m", "pianist", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    
    assert result.returncode == 0
    assert "pianist" in result.stdout.lower()
    assert "render" in result.stdout
    assert "import" in result.stdout
    assert "modify" in result.stdout
    assert "analyze" in result.stdout
    assert "fix" in result.stdout
    assert "annotate" in result.stdout
    assert "expand" in result.stdout
    assert "diff" in result.stdout
    assert "generate" in result.stdout
    assert "reference" in result.stdout


def test_refactored_command_help() -> None:
    """Test that a refactored command shows help."""
    result = subprocess.run(
        [sys.executable, "-m", "pianist", "render", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    
    assert result.returncode == 0
    assert "render" in result.stdout.lower()
    assert "--input" in result.stdout or "-i" in result.stdout
    assert "--output" in result.stdout or "-o" in result.stdout


def test_legacy_command_help() -> None:
    """Test that a legacy command shows help."""
    result = subprocess.run(
        [sys.executable, "-m", "pianist", "analyze", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    
    assert result.returncode == 0
    assert "analyze" in result.stdout.lower()
    assert "--input" in result.stdout or "-i" in result.stdout
