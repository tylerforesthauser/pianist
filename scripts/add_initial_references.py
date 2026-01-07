#!/usr/bin/env python3
"""
Script to add initial example references to the reference database.

This script creates a few basic examples demonstrating different styles,
forms, and techniques that can be used as references for AI expansion.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.reference_db import ReferenceDatabase, MusicalReference, get_default_database
from pianist.parser import parse_composition_from_text


def create_example_references() -> list[MusicalReference]:
    """Create a list of example references."""
    references = []
    
    # Example 1: Simple Classical motif with sequence
    comp1_json = {
        "title": "Classical Motif Sequence",
        "bpm": 120,
        "key_signature": "C major",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                # Motif: C-E-G
                {"type": "note", "start": 0, "duration": 0.5, "pitches": [60], "velocity": 80},
                {"type": "note", "start": 0.5, "duration": 0.5, "pitches": [64], "velocity": 80},
                {"type": "note", "start": 1, "duration": 0.5, "pitches": [67], "velocity": 80},
                # Sequence up a step: D-F-A
                {"type": "note", "start": 2, "duration": 0.5, "pitches": [62], "velocity": 80},
                {"type": "note", "start": 2.5, "duration": 0.5, "pitches": [65], "velocity": 80},
                {"type": "note", "start": 3, "duration": 0.5, "pitches": [69], "velocity": 80},
            ]
        }]
    }
    comp1 = parse_composition_from_text(json.dumps(comp1_json))
    ref1 = MusicalReference(
        id="classical_sequence_example",
        title="Classical Motif Sequence",
        description="Demonstrates sequential development of a simple ascending motif (C-E-G) transposed up a step (D-F-A).",
        composition=comp1,
        style="Classical",
        form="binary",
        techniques=["sequence", "motif_development"],
    )
    references.append(ref1)
    
    # Example 2: Phrase extension example
    comp2_json = {
        "title": "Phrase Extension Example",
        "bpm": 100,
        "key_signature": "G major",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                # Original phrase (4 beats)
                {"type": "note", "start": 0, "duration": 1, "pitches": [67], "velocity": 80},
                {"type": "note", "start": 1, "duration": 1, "pitches": [69], "velocity": 80},
                {"type": "note", "start": 2, "duration": 1, "pitches": [71], "velocity": 80},
                {"type": "note", "start": 3, "duration": 1, "pitches": [72], "velocity": 80},
                # Extended phrase (8 beats total)
                {"type": "note", "start": 4, "duration": 1, "pitches": [74], "velocity": 80},
                {"type": "note", "start": 5, "duration": 1, "pitches": [76], "velocity": 80},
                {"type": "note", "start": 6, "duration": 1, "pitches": [77], "velocity": 80},
                {"type": "note", "start": 7, "duration": 1, "pitches": [79], "velocity": 80},
            ]
        }]
    }
    comp2 = parse_composition_from_text(json.dumps(comp2_json))
    ref2 = MusicalReference(
        id="phrase_extension_example",
        title="Phrase Extension Example",
        description="Shows how to extend a 4-beat phrase to 8 beats by continuing the melodic line.",
        composition=comp2,
        style="Classical",
        techniques=["phrase_extension", "melodic_continuation"],
    )
    references.append(ref2)
    
    # Example 3: Transition example
    comp3_json = {
        "title": "Section Transition Example",
        "bpm": 120,
        "key_signature": "F major",
        "time_signature": {"numerator": 4, "denominator": 4},
        "ppq": 480,
        "tracks": [{
            "events": [
                # Section A ending
                {"type": "note", "start": 0, "duration": 2, "pitches": [60, 64, 67], "velocity": 80},
                {"type": "note", "start": 2, "duration": 2, "pitches": [62, 65, 69], "velocity": 80},
                # Transition material
                {"type": "note", "start": 4, "duration": 1, "pitches": [64, 67, 71], "velocity": 75},
                {"type": "note", "start": 5, "duration": 1, "pitches": [65, 69, 72], "velocity": 75},
                {"type": "note", "start": 6, "duration": 1, "pitches": [67, 71, 74], "velocity": 75},
                {"type": "note", "start": 7, "duration": 1, "pitches": [69, 72, 76], "velocity": 75},
                # Section B beginning
                {"type": "note", "start": 8, "duration": 2, "pitches": [65, 69, 72], "velocity": 80},
            ]
        }]
    }
    comp3 = parse_composition_from_text(json.dumps(comp3_json))
    ref3 = MusicalReference(
        id="transition_example",
        title="Section Transition Example",
        description="Demonstrates a smooth transition between sections using stepwise voice leading and dynamic variation.",
        composition=comp3,
        style="Classical",
        form="ternary",
        techniques=["transition", "voice_leading", "dynamic_variation"],
    )
    references.append(ref3)
    
    return references


def main() -> int:
    """Add initial references to the database."""
    db = get_default_database()
    
    print("Adding initial example references to the database...")
    print(f"Database location: {db.db_path}")
    
    references = create_example_references()
    
    for ref in references:
        db.add_reference(ref)
        print(f"  ✓ Added: {ref.id} - {ref.title}")
    
    total = db.count_references()
    print(f"\nTotal references in database: {total}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

