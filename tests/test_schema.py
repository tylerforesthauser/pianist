from __future__ import annotations

import pytest

from pianist.schema import validate_composition_dict


def test_schema_requires_track() -> None:
    with pytest.raises(ValueError):
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [],
            }
        )


def test_schema_coerces_pitch_string_to_midi() -> None:
    comp = validate_composition_dict(
        {
            "title": "x",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "tracks": [
                {
                    "events": [
                        {
                            "type": "note",
                            "start": 0,
                            "duration": 1,
                            "pitches": ["C4", "E4", "G4"],
                            "velocity": 80,
                        }
                    ]
                }
            ],
        }
    )
    ev = comp.tracks[0].events[0]
    assert ev.pitches == [60, 64, 67]

