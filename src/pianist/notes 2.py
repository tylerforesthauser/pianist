from __future__ import annotations

import re

_NOTE_BASE: dict[str, int] = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


_NOTE_RE = re.compile(r"^\s*([A-Ga-g])([#b]{0,2})\s*(-?\d+)\s*$")


def note_name_to_midi(note: str) -> int:
    """
    Convert scientific pitch notation (e.g. C4, F#3, Bb2) to MIDI note number.

    Convention:
    - C4 == 60 (middle C)
    - octave numbers follow scientific pitch notation
    """
    m = _NOTE_RE.match(note)
    if not m:
        raise ValueError(f"Invalid note name {note!r}. Expected e.g. 'C4', 'F#3', 'Bb2'.")

    letter = m.group(1).upper()
    accidentals = m.group(2)
    octave = int(m.group(3))

    semitone = _NOTE_BASE[letter]
    # Accidentals can cross octave boundaries (e.g. B#3 == C4),
    # so do not modulo the semitone.
    for acc in accidentals:
        if acc == "#":
            semitone += 1
        elif acc == "b":
            semitone -= 1

    midi = (octave + 1) * 12 + semitone
    if not 0 <= midi <= 127:
        raise ValueError(f"Note {note!r} converts to out-of-range MIDI note {midi}.")
    return midi
