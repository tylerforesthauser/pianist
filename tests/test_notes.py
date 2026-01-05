from __future__ import annotations

import pytest

from aimusicgen.notes import note_name_to_midi


def test_note_name_to_midi_basic() -> None:
    assert note_name_to_midi("C4") == 60
    assert note_name_to_midi("A4") == 69
    assert note_name_to_midi("G9") == 127
    assert note_name_to_midi("C-1") == 0


def test_note_name_to_midi_accidentals() -> None:
    assert note_name_to_midi("B#3") == 60  # enharmonic to C4
    assert note_name_to_midi("Cb4") == 59  # enharmonic to B3
    assert note_name_to_midi("F##4") == 67  # enharmonic to G4
    assert note_name_to_midi("Gbb4") == 65  # enharmonic to F4


def test_note_name_to_midi_out_of_range() -> None:
    with pytest.raises(ValueError):
        note_name_to_midi("C-2")
    with pytest.raises(ValueError):
        note_name_to_midi("G#9")


def test_note_name_to_midi_rejects_invalid_format() -> None:
    with pytest.raises(ValueError):
        note_name_to_midi("H4")
    with pytest.raises(ValueError):
        note_name_to_midi("C#")
