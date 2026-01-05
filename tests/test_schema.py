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


def test_schema_normalizes_pitch_field_to_pitches() -> None:
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
                            "pitch": "C4",
                            "velocity": 80,
                        }
                    ]
                }
            ],
        }
    )
    ev = comp.tracks[0].events[0]
    assert ev.pitches == [60]


def test_schema_errors_when_missing_pitch_fields() -> None:
    with pytest.raises(ValueError) as exc:
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [{"events": [{"type": "note", "start": 0, "duration": 1}]}],
            }
        )
    assert "Either 'pitch' or 'pitches' must be provided" in str(exc.value)


def test_schema_errors_when_both_pitch_and_pitches_provided() -> None:
    with pytest.raises(ValueError) as exc:
        validate_composition_dict(
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
                                "pitch": "C4",
                                "pitches": ["E4"],
                            }
                        ]
                    }
                ],
            }
        )
    assert "Provide either 'pitch' or 'pitches', not both" in str(exc.value)


def test_pedal_event_validation() -> None:
    # Value bounds and positive duration enforced by Pydantic validators.
    with pytest.raises(ValueError):
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 1, "value": 200}
                        ]
                    }
                ],
            }
        )

    with pytest.raises(ValueError):
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [{"events": [{"type": "pedal", "start": 0, "duration": 0}]}],
            }
        )

