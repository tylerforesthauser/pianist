"""Tests for unified output utilities."""
from __future__ import annotations

from pathlib import Path

from pianist.output_util import (
    version_path_if_exists,
    derive_sidecar_path,
    write_output_with_sidecar,
)


def test_version_path_if_exists_returns_original_when_not_exists(tmp_path: Path) -> None:
    """If file doesn't exist, return original path."""
    path = tmp_path / "file.json"
    assert version_path_if_exists(path) == path


def test_version_path_if_exists_returns_v2_when_exists(tmp_path: Path) -> None:
    """If file exists, return .v2 version."""
    path = tmp_path / "file.json"
    path.write_text("original")
    
    versioned = version_path_if_exists(path)
    assert versioned == tmp_path / "file.v2.json"
    assert not versioned.exists()


def test_version_path_if_exists_increments_to_v3(tmp_path: Path) -> None:
    """If .v2 exists, return .v3 version."""
    path = tmp_path / "file.json"
    path.write_text("original")
    (tmp_path / "file.v2.json").write_text("v2")
    
    versioned = version_path_if_exists(path)
    assert versioned == tmp_path / "file.v3.json"


def test_version_path_if_exists_finds_next_available_version(tmp_path: Path) -> None:
    """Find next available version even with gaps."""
    path = tmp_path / "file.json"
    path.write_text("original")
    (tmp_path / "file.v2.json").write_text("v2")
    (tmp_path / "file.v3.json").write_text("v3")
    (tmp_path / "file.v4.json").write_text("v4")
    
    versioned = version_path_if_exists(path)
    assert versioned == tmp_path / "file.v5.json"


def test_version_path_if_exists_with_timestamp(tmp_path: Path) -> None:
    """Timestamp versioning creates unique paths."""
    path = tmp_path / "file.json"
    path.write_text("original")
    
    versioned = version_path_if_exists(path, use_timestamp=True)
    assert versioned.parent == tmp_path
    assert versioned.suffix == ".json"
    assert versioned.stem.startswith("file.")
    assert not versioned.exists()


def test_derive_sidecar_path_with_provider() -> None:
    """Sidecar path includes provider name."""
    path = Path("output/song.json")
    sidecar = derive_sidecar_path(path, provider="gemini")
    assert sidecar == Path("output/song.json.gemini.txt")


def test_derive_sidecar_path_without_provider() -> None:
    """Sidecar path without provider uses generic .txt."""
    path = Path("output/song.json")
    sidecar = derive_sidecar_path(path)
    assert sidecar == Path("output/song.json.txt")


def test_derive_sidecar_path_preserves_version() -> None:
    """Sidecar path preserves version from primary file."""
    path = Path("output/song.v2.json")
    sidecar = derive_sidecar_path(path, provider="gemini")
    assert sidecar == Path("output/song.v2.json.gemini.txt")


def test_write_output_with_sidecar_basic(tmp_path: Path) -> None:
    """Write primary and sidecar files."""
    primary_path = tmp_path / "output.json"
    result = write_output_with_sidecar(
        primary_path,
        '{"test": true}',
        sidecar_content="raw response",
        provider="gemini",
        overwrite=False,
    )
    
    assert result.primary_path == primary_path
    assert result.primary_path.read_text() == '{"test": true}'
    assert result.sidecar_path == tmp_path / "output.json.gemini.txt"
    assert result.sidecar_path.read_text() == "raw response"


def test_write_output_with_sidecar_creates_directory(tmp_path: Path) -> None:
    """Automatically create parent directories."""
    primary_path = tmp_path / "subdir" / "output.json"
    result = write_output_with_sidecar(
        primary_path,
        '{"test": true}',
        sidecar_content="raw",
        overwrite=False,
    )
    
    assert result.primary_path.exists()
    assert result.primary_path.parent.exists()


def test_write_output_with_sidecar_versions_when_exists(tmp_path: Path) -> None:
    """Version both primary and sidecar when primary exists."""
    primary_path = tmp_path / "output.json"
    primary_path.write_text('{"original": true}')
    
    result = write_output_with_sidecar(
        primary_path,
        '{"new": true}',
        sidecar_content="new response",
        provider="gemini",
        overwrite=False,
    )
    
    # Both files should be versioned
    assert result.primary_path == tmp_path / "output.v2.json"
    assert result.sidecar_path == tmp_path / "output.v2.json.gemini.txt"
    
    # Original file should be unchanged
    assert primary_path.read_text() == '{"original": true}'
    
    # New versioned files should have new content
    assert result.primary_path.read_text() == '{"new": true}'
    assert result.sidecar_path.read_text() == "new response"


def test_write_output_with_sidecar_overwrites_when_requested(tmp_path: Path) -> None:
    """Overwrite existing files when overwrite=True."""
    primary_path = tmp_path / "output.json"
    sidecar_path = tmp_path / "output.json.gemini.txt"
    
    primary_path.write_text('{"original": true}')
    sidecar_path.write_text("original response")
    
    result = write_output_with_sidecar(
        primary_path,
        '{"new": true}',
        sidecar_content="new response",
        provider="gemini",
        overwrite=True,
    )
    
    # Should use original paths
    assert result.primary_path == primary_path
    assert result.sidecar_path == sidecar_path
    
    # Files should be overwritten
    assert primary_path.read_text() == '{"new": true}'
    assert sidecar_path.read_text() == "new response"


def test_write_output_with_sidecar_no_sidecar_content(tmp_path: Path) -> None:
    """Handle case with no sidecar content."""
    primary_path = tmp_path / "output.json"
    result = write_output_with_sidecar(
        primary_path,
        '{"test": true}',
        sidecar_content=None,
        overwrite=False,
    )
    
    assert result.primary_path.exists()
    assert result.sidecar_path is None


def test_write_output_with_sidecar_coordinated_versioning(tmp_path: Path) -> None:
    """Verify sidecar version always matches primary version."""
    primary_path = tmp_path / "output.json"
    
    # First write
    result1 = write_output_with_sidecar(
        primary_path,
        '{"v1": true}',
        sidecar_content="response 1",
        provider="gemini",
        overwrite=False,
    )
    assert result1.primary_path == primary_path
    assert result1.sidecar_path == tmp_path / "output.json.gemini.txt"
    
    # Second write (should version both)
    result2 = write_output_with_sidecar(
        primary_path,
        '{"v2": true}',
        sidecar_content="response 2",
        provider="gemini",
        overwrite=False,
    )
    assert result2.primary_path == tmp_path / "output.v2.json"
    assert result2.sidecar_path == tmp_path / "output.v2.json.gemini.txt"
    
    # Third write (should create v3)
    result3 = write_output_with_sidecar(
        primary_path,
        '{"v3": true}',
        sidecar_content="response 3",
        provider="gemini",
        overwrite=False,
    )
    assert result3.primary_path == tmp_path / "output.v3.json"
    assert result3.sidecar_path == tmp_path / "output.v3.json.gemini.txt"
    
    # All files should exist with correct content
    assert (tmp_path / "output.json").read_text() == '{"v1": true}'
    assert (tmp_path / "output.json.gemini.txt").read_text() == "response 1"
    assert (tmp_path / "output.v2.json").read_text() == '{"v2": true}'
    assert (tmp_path / "output.v2.json.gemini.txt").read_text() == "response 2"
    assert (tmp_path / "output.v3.json").read_text() == '{"v3": true}'
    assert (tmp_path / "output.v3.json.gemini.txt").read_text() == "response 3"


def test_write_output_with_sidecar_different_providers(tmp_path: Path) -> None:
    """Different provider names create different sidecar files."""
    primary_path = tmp_path / "output.json"
    
    result1 = write_output_with_sidecar(
        primary_path,
        '{"test": true}',
        sidecar_content="gemini response",
        provider="gemini",
        overwrite=True,
    )
    
    result2 = write_output_with_sidecar(
        primary_path,
        '{"test": true}',
        sidecar_content="ollama response",
        provider="ollama",
        overwrite=True,
    )
    
    # Different providers should create different sidecars
    assert result1.sidecar_path == tmp_path / "output.json.gemini.txt"
    assert result2.sidecar_path == tmp_path / "output.json.ollama.txt"
    assert result1.sidecar_path.read_text() == "gemini response"
    assert result2.sidecar_path.read_text() == "ollama response"
