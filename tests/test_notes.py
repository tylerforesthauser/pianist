from __future__ import annotations

import pytest

from pianist.notes import note_name_to_midi


def test_note_name_to_midi_basic() -> None:
    assert note_name_to_midi("C4") == 60
    assert note_name_to_midi("A4") == 69
    assert note_name_to_midi("F#3") == 54
    assert note_name_to_midi("Bb2") == 46


def test_note_name_to_midi_octave_boundary() -> None:
    # B#3 == C4
    assert note_name_to_midi("B#3") == 60


def test_note_name_to_midi_negative_octave() -> None:
    # Lowest possible C in MIDI space
    assert note_name_to_midi("C-1") == 0


def test_note_name_to_midi_invalid() -> None:
    with pytest.raises(ValueError):
        note_name_to_midi("H2")

    # Out-of-range MIDI note
    with pytest.raises(ValueError):
        note_name_to_midi("C10")

