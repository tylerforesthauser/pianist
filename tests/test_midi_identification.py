"""Tests for midi_identification module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pianist.midi_identification import (
    identify_from_directory,
    identify_from_filename,
    identify_from_metadata_json,
    identify_midi_file,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_identify_from_filename_classical() -> None:
    """Test identification of classical works from filename."""
    # Standard format
    result = identify_from_filename("J.S. Bach - Invention No. 1 BWV 772.mid")
    assert result.composer == "J.S. Bach"
    assert result.title is not None
    assert "invention" in result.title.lower() or "invention" in result.title.lower()
    assert result.catalog_number == "BWV 772"
    assert result.is_classical is True
    assert result.confidence > 0.5

    # Hyphenated format
    result = identify_from_filename("chopin-prelude-op28-no7.mid")
    assert result.composer == "Chopin"
    assert result.is_classical is True

    # With opus
    result = identify_from_filename("Mozart - Sonata K. 545.mid")
    assert result.composer == "Mozart"
    assert result.catalog_number == "K. 545"
    assert result.is_classical is True


def test_identify_from_filename_modern() -> None:
    """Test identification of modern works from filename."""
    # Film soundtrack
    result = identify_from_filename("Hans Zimmer - Interstellar (Main Theme).mid")
    assert result.composer == "Hans Zimmer"
    assert result.title is not None
    assert "interstellar" in result.title.lower()
    assert result.is_classical is False
    assert result.confidence > 0.5

    # Pop song with double dash
    result = identify_from_filename("what-was-i-made-for--billie-eilish.mid")
    assert result.composer == "Billie Eilish"
    assert result.title is not None
    assert result.is_classical is False

    # Modern composer
    result = identify_from_filename("River Flows in You - Yiruma.mid")
    assert result.composer == "Yiruma"
    assert result.is_classical is False


def test_identify_from_filename_generic() -> None:
    """Test identification of generic filenames."""
    result = identify_from_filename("output4_unknown.mid")
    assert result.composer is None
    assert result.title is None
    assert result.confidence < 0.5

    result = identify_from_filename("track1.mid")
    assert result.composer is None
    assert result.confidence < 0.5


def test_identify_from_metadata_json(tmp_path: Path) -> None:
    """Test identification from companion JSON metadata file."""
    # Create MIDI file
    midi_file = tmp_path / "test.mid"
    midi_file.write_bytes(b"dummy midi content")

    # Create companion JSON
    json_file = tmp_path / "test.mid.json"
    json_file.write_text(
        '{"composer": "Hans Zimmer", "title": "Interstellar (Main Theme)", "is_classical": false}',
        encoding="utf-8",
    )

    result = identify_from_metadata_json(midi_file)
    assert result is not None
    assert result.composer == "Hans Zimmer"
    assert result.title == "Interstellar (Main Theme)"
    assert result.is_classical is False
    assert result.confidence == 1.0  # JSON metadata is authoritative


def test_identify_from_directory(tmp_path: Path) -> None:
    """Test identification from directory structure."""
    # Create directory structure
    composer_dir = tmp_path / "Hans Zimmer"
    composer_dir.mkdir()
    midi_file = composer_dir / "interstellar.mid"
    midi_file.write_bytes(b"dummy midi content")

    result = identify_from_directory(midi_file)
    assert result is not None
    assert result.composer == "Hans Zimmer"
    assert result.is_classical is False
    assert result.confidence > 0.5


def test_identify_midi_file_priority(tmp_path: Path) -> None:
    """Test that identify_midi_file uses correct priority order."""
    # Create directory structure
    composer_dir = tmp_path / "Test Composer"
    composer_dir.mkdir()
    midi_file = composer_dir / "test.mid"
    midi_file.write_bytes(b"dummy midi content")

    # Create JSON metadata (should take priority over directory)
    json_file = composer_dir / "test.mid.json"
    json_file.write_text(
        '{"composer": "JSON Composer", "title": "JSON Title", "is_classical": true}',
        encoding="utf-8",
    )

    result = identify_midi_file(midi_file)
    # JSON should take priority
    assert result.composer == "JSON Composer"
    assert result.title == "JSON Title"
    assert result.confidence == 1.0


def test_catalog_number_extraction() -> None:
    """Test extraction of catalog numbers (BWV, Op., K., etc.)."""
    # BWV
    result = identify_from_filename("bach-invention-bwv-772.mid")
    assert result.catalog_number == "BWV 772"

    # Opus (may extract as "Op. 28" or "Op. 28 No. 7" depending on parsing)
    result = identify_from_filename("chopin-prelude-op28-no7.mid")
    assert result.opus is not None
    assert "28" in result.opus
    # May or may not include "No. 7" depending on parsing

    # Köchel
    result = identify_from_filename("mozart-sonata-k545.mid")
    assert result.catalog_number == "K. 545"


def test_modern_metadata_extraction() -> None:
    """Test extraction of modern work metadata."""
    result = identify_from_filename("Hans Zimmer - Interstellar (Main Theme).mid")
    assert result.composer == "Hans Zimmer"
    assert result.title is not None
    # Album/source might be in parentheses
    assert result.is_classical is False
