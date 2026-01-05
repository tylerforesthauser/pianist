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
    assert "One of 'pitch', 'pitches', 'notes', or 'groups' must be provided" in str(
        exc.value
    )


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


def test_schema_errors_on_empty_pitches_list() -> None:
    with pytest.raises(ValueError) as exc:
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {"events": [{"type": "note", "start": 0, "duration": 1, "pitches": []}]}
                ],
            }
        )
    assert "pitches must not be empty" in str(exc.value)

    with pytest.raises(ValueError):
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [{"events": [{"type": "pedal", "start": 0, "duration": 0}]}],
            }
        )


def test_schema_accepts_labeled_notes_and_coerces_pitches() -> None:
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
                            "notes": [
                                {"pitch": "C4", "hand": "rh", "voice": 1},
                                {"pitch": "C3", "hand": "lh", "voice": 2},
                            ],
                        }
                    ]
                }
            ],
        }
    )
    ev = comp.tracks[0].events[0]
    assert ev.pitches == [60, 48]
    assert ev.notes is not None
    assert [n.pitch for n in ev.notes] == [60, 48]


def test_schema_accepts_groups_and_flattens_pitches() -> None:
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
                            "groups": [
                                {"hand": "rh", "voice": 1, "pitches": ["C4", "E4", "G4"]},
                                {"hand": "lh", "voice": 2, "pitches": ["C3"]},
                            ],
                        }
                    ]
                }
            ],
        }
    )
    ev = comp.tracks[0].events[0]
    assert ev.pitches == [60, 64, 67, 48]
    assert ev.groups is not None
    assert ev.groups[0].pitches == [60, 64, 67]
    assert ev.groups[1].pitches == [48]


def test_schema_rejects_event_level_hand_when_using_groups() -> None:
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
                                "hand": "rh",
                                "groups": [{"hand": "rh", "pitches": ["C4"]}],
                            }
                        ]
                    }
                ],
            }
        )
    assert "omit event-level 'hand'" in str(exc.value)

