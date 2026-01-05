from __future__ import annotations

import pytest

from aimusicgen.schema import Composition, NoteEvent


def test_noteevent_normalizes_pitch_to_pitches() -> None:
    ev = NoteEvent.model_validate(
        {"type": "note", "start": 0, "duration": 1, "pitch": "C4"}
    )
    assert ev.pitches == [60]


def test_noteevent_rejects_pitch_and_pitches_together() -> None:
    with pytest.raises(ValueError):
        NoteEvent.model_validate(
            {
                "type": "note",
                "start": 0,
                "duration": 1,
                "pitch": "C4",
                "pitches": ["C4", "E4"],
            }
        )


def test_noteevent_velocity_bounds_enforced() -> None:
    with pytest.raises(ValueError):
        NoteEvent.model_validate(
            {"type": "note", "start": 0, "duration": 1, "pitch": "C4", "velocity": 0}
        )
    with pytest.raises(ValueError):
        NoteEvent.model_validate(
            {
                "type": "note",
                "start": 0,
                "duration": 1,
                "pitch": "C4",
                "velocity": 128,
            }
        )


def test_composition_requires_at_least_one_track() -> None:
    with pytest.raises(ValueError):
        Composition.model_validate(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "ppq": 480,
                "tracks": [],
            }
        )

