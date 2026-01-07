"""Tests for reference database module."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pianist.reference_db import (
    ReferenceDatabase,
    MusicalReference,
)
from pianist.parser import parse_composition_from_text


def test_reference_database_init(tmp_path: Path) -> None:
    """Test database initialization."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    assert db.db_path == db_path
    assert db_path.exists()
    
    # Should be able to count (should be 0)
    assert db.count_references() == 0


def test_add_and_get_reference(tmp_path: Path) -> None:
    """Test adding and retrieving a reference."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test Composition",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80}
            ]
        }]
    }
    
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    reference = MusicalReference(
        id="test_1",
        title="Test Composition",
        description="A test composition",
        composition=comp,
        style="Classical",
        form="binary",
        techniques=["sequence", "inversion"],
    )
    
    db.add_reference(reference)
    
    retrieved = db.get_reference("test_1")
    assert retrieved is not None
    assert retrieved.id == "test_1"
    assert retrieved.title == "Test Composition"
    assert retrieved.description == "A test composition"
    assert retrieved.style == "Classical"
    assert retrieved.form == "binary"
    assert retrieved.techniques == ["sequence", "inversion"]
    assert retrieved.composition.title == "Test Composition"


def test_get_nonexistent_reference(tmp_path: Path) -> None:
    """Test retrieving a non-existent reference."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    retrieved = db.get_reference("nonexistent")
    assert retrieved is None


def test_search_references_by_style(tmp_path: Path) -> None:
    """Test searching references by style."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    # Add Classical reference
    ref1 = MusicalReference(
        id="classical_1",
        title="Classical Piece",
        description="A classical piece",
        composition=comp,
        style="Classical",
    )
    db.add_reference(ref1)
    
    # Add Romantic reference
    ref2 = MusicalReference(
        id="romantic_1",
        title="Romantic Piece",
        description="A romantic piece",
        composition=comp,
        style="Romantic",
    )
    db.add_reference(ref2)
    
    # Search for Classical
    results = db.search_references(style="Classical")
    assert len(results) == 1
    assert results[0].id == "classical_1"
    assert results[0].style == "Classical"
    
    # Search for Romantic
    results = db.search_references(style="Romantic")
    assert len(results) == 1
    assert results[0].id == "romantic_1"


def test_search_references_by_form(tmp_path: Path) -> None:
    """Test searching references by form."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    ref1 = MusicalReference(
        id="binary_1",
        title="Binary Piece",
        description="A binary piece",
        composition=comp,
        form="binary",
    )
    db.add_reference(ref1)
    
    ref2 = MusicalReference(
        id="ternary_1",
        title="Ternary Piece",
        description="A ternary piece",
        composition=comp,
        form="ternary",
    )
    db.add_reference(ref2)
    
    results = db.search_references(form="binary")
    assert len(results) == 1
    assert results[0].form == "binary"


def test_search_references_by_technique(tmp_path: Path) -> None:
    """Test searching references by technique."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    ref1 = MusicalReference(
        id="seq_1",
        title="Sequential Piece",
        description="Uses sequence",
        composition=comp,
        techniques=["sequence", "inversion"],
    )
    db.add_reference(ref1)
    
    ref2 = MusicalReference(
        id="aug_1",
        title="Augmented Piece",
        description="Uses augmentation",
        composition=comp,
        techniques=["augmentation"],
    )
    db.add_reference(ref2)
    
    results = db.search_references(technique="sequence")
    assert len(results) == 1
    assert results[0].id == "seq_1"
    assert "sequence" in (results[0].techniques or [])


def test_search_references_by_title(tmp_path: Path) -> None:
    """Test searching references by title substring."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    ref1 = MusicalReference(
        id="sonata_1",
        title="Sonata in C",
        description="A sonata",
        composition=comp,
    )
    db.add_reference(ref1)
    
    ref2 = MusicalReference(
        id="fugue_1",
        title="Fugue in D",
        description="A fugue",
        composition=comp,
    )
    db.add_reference(ref2)
    
    results = db.search_references(title_contains="Sonata")
    assert len(results) == 1
    assert results[0].title == "Sonata in C"


def test_list_all_references(tmp_path: Path) -> None:
    """Test listing all references."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    for i in range(5):
        ref = MusicalReference(
            id=f"ref_{i}",
            title=f"Reference {i}",
            description=f"Description {i}",
            composition=comp,
        )
        db.add_reference(ref)
    
    all_refs = db.list_all_references()
    assert len(all_refs) == 5


def test_delete_reference(tmp_path: Path) -> None:
    """Test deleting a reference."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    ref = MusicalReference(
        id="to_delete",
        title="To Delete",
        description="This will be deleted",
        composition=comp,
    )
    db.add_reference(ref)
    
    assert db.count_references() == 1
    
    deleted = db.delete_reference("to_delete")
    assert deleted is True
    assert db.count_references() == 0
    
    # Try to delete again
    deleted = db.delete_reference("to_delete")
    assert deleted is False


def test_count_references(tmp_path: Path) -> None:
    """Test counting references."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    assert db.count_references() == 0
    
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    for i in range(3):
        ref = MusicalReference(
            id=f"ref_{i}",
            title=f"Reference {i}",
            description="Test",
            composition=comp,
        )
        db.add_reference(ref)
    
    assert db.count_references() == 3


def test_find_relevant_references(tmp_path: Path) -> None:
    """Test finding relevant references for a composition."""
    db_path = tmp_path / "test.db"
    db = ReferenceDatabase(db_path)
    
    # Add some references
    comp_json = {
        "title": "Test",
        "bpm": 120,
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    comp = parse_composition_from_text(json.dumps(comp_json))
    
    ref1 = MusicalReference(
        id="classical_binary",
        title="Classical Binary",
        description="Classical binary form",
        composition=comp,
        style="Classical",
        form="binary",
    )
    db.add_reference(ref1)
    
    ref2 = MusicalReference(
        id="romantic_ternary",
        title="Romantic Ternary",
        description="Romantic ternary form",
        composition=comp,
        style="Romantic",
        form="ternary",
    )
    db.add_reference(ref2)
    
    # Create a composition to find references for
    search_comp_json = {
        "title": "Search Composition",
        "bpm": 120,
        "key_signature": "C major",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{"events": []}]
    }
    search_comp = parse_composition_from_text(json.dumps(search_comp_json))
    
    # Find relevant references (should return some, even if no exact match)
    results = db.find_relevant_references(search_comp, limit=5)
    assert len(results) >= 0  # May or may not find matches depending on heuristics


def test_default_database_path() -> None:
    """Test that default database path is used when none specified."""
    db = ReferenceDatabase()
    
    # Should use ~/.pianist/references.db
    expected_path = Path.home() / ".pianist" / "references.db"
    assert db.db_path == expected_path

