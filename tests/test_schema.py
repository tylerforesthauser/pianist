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


def test_schema_rejects_event_level_hand_when_using_notes() -> None:
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
                                "notes": [{"hand": "rh", "pitch": "C4"}],
                            }
                        ]
                    }
                ],
            }
        )
    assert "omit event-level 'hand'" in str(exc.value)


def test_schema_rejects_empty_notes_and_empty_groups() -> None:
    with pytest.raises(ValueError) as exc_notes:
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {"events": [{"type": "note", "start": 0, "duration": 1, "notes": []}]}
                ],
            }
        )
    assert "'notes' must not be empty" in str(exc_notes.value)

    with pytest.raises(ValueError) as exc_groups:
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {"events": [{"type": "note", "start": 0, "duration": 1, "groups": []}]}
                ],
            }
        )
    assert "'groups' must not be empty" in str(exc_groups.value)


def test_schema_rejects_notes_not_list() -> None:
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
                                "notes": {"hand": "rh", "pitch": "C4"},
                            }
                        ]
                    }
                ],
            }
        )
    assert "Field 'notes' must be a list" in str(exc.value)


def test_schema_rejects_mixed_pitch_representations() -> None:
    with pytest.raises(ValueError) as exc_legacy_notes:
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
                                "pitches": ["C4"],
                                "notes": [{"hand": "rh", "pitch": "E4"}],
                            }
                        ]
                    }
                ],
            }
        )
    assert "Provide only one of legacy 'pitch'/'pitches', 'notes', or 'groups'" in str(
        exc_legacy_notes.value
    )

    with pytest.raises(ValueError) as exc_notes_groups:
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
                                "notes": [{"hand": "rh", "pitch": "C4"}],
                                "groups": [{"hand": "rh", "pitches": ["E4"]}],
                            }
                        ]
                    }
                ],
            }
        )
    assert "Provide only one of legacy 'pitch'/'pitches', 'notes', or 'groups'" in str(
        exc_notes_groups.value
    )


def test_schema_rejects_invalid_hand_and_voice_values_in_notes() -> None:
    with pytest.raises(ValueError) as exc_hand:
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
                                "notes": [{"hand": "middle", "pitch": "C4"}],
                            }
                        ]
                    }
                ],
            }
        )
    # Keep this assertion loose across Pydantic versions.
    msg_hand = str(exc_hand.value)
    assert "hand" in msg_hand and "lh" in msg_hand and "rh" in msg_hand

    with pytest.raises(ValueError) as exc_voice:
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
                                "notes": [{"hand": "rh", "pitch": "C4", "voice": 0}],
                            }
                        ]
                    }
                ],
            }
        )
    msg_voice = str(exc_voice.value)
    assert "voice" in msg_voice and "greater than or equal to 1" in msg_voice


def test_schema_rejects_invalid_voice_value_in_groups() -> None:
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
                                "groups": [{"hand": "rh", "pitches": ["C4"], "voice": 5}],
                            }
                        ]
                    }
                ],
            }
        )
    msg = str(exc.value)
    assert "voice" in msg and "less than or equal to 4" in msg


def test_schema_rejects_note_missing_pitch_in_notes_list() -> None:
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
                                "notes": [{"hand": "rh"}],
                            }
                        ]
                    }
                ],
            }
        )
    assert "Note at index 0 is missing required 'pitch'" in str(exc.value)


def test_schema_rejects_group_missing_pitches_in_groups_list() -> None:
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
                                "groups": [{"hand": "rh"}],
                            }
                        ]
                    }
                ],
            }
        )
    assert "Group at index 0 is missing required 'pitches'" in str(exc.value)


def test_schema_errors_when_note_missing_hand_in_notes_list() -> None:
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
                                "notes": [{"pitch": "C4"}],
                            }
                        ]
                    }
                ],
            }
        )
    # Pydantic wording can vary; assert the key signal.
    msg = str(exc.value)
    assert "hand" in msg and ("Field required" in msg or "field required" in msg)


def test_schema_errors_when_group_missing_hand_in_groups_list() -> None:
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
                                "groups": [{"pitches": ["C4"]}],
                            }
                        ]
                    }
                ],
            }
        )
    msg = str(exc.value)
    assert "hand" in msg and ("Field required" in msg or "field required" in msg)


def test_tempo_event_instant_change() -> None:
    """Test that instant tempo changes are validated correctly."""
    comp = validate_composition_dict(
        {
            "title": "x",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "tracks": [
                {
                    "events": [
                        {
                            "type": "tempo",
                            "start": 60,
                            "bpm": 100,
                        }
                    ]
                }
            ],
        }
    )
    tempo_ev = comp.tracks[0].events[0]
    assert tempo_ev.type == "tempo"
    assert tempo_ev.start == 60
    assert tempo_ev.bpm == 100
    assert tempo_ev.start_bpm is None
    assert tempo_ev.end_bpm is None


def test_tempo_event_gradual_change() -> None:
    """Test that gradual tempo changes are validated correctly."""
    comp = validate_composition_dict(
        {
            "title": "x",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "tracks": [
                {
                    "events": [
                        {
                            "type": "tempo",
                            "start": 120,
                            "start_bpm": 100,
                            "end_bpm": 60,
                            "duration": 16,
                        }
                    ]
                }
            ],
        }
    )
    tempo_ev = comp.tracks[0].events[0]
    assert tempo_ev.type == "tempo"
    assert tempo_ev.start == 120
    assert tempo_ev.bpm is None
    assert tempo_ev.start_bpm == 100
    assert tempo_ev.end_bpm == 60
    assert tempo_ev.duration == 16


def test_tempo_event_requires_either_instant_or_gradual() -> None:
    """Test that tempo events must specify either instant or gradual change."""
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
                                "type": "tempo",
                                "start": 60,
                            }
                        ]
                    }
                ],
            }
        )
    assert "bpm" in str(exc.value) or "start_bpm" in str(exc.value)


def test_tempo_event_cannot_have_both_instant_and_gradual() -> None:
    """Test that tempo events cannot specify both instant and gradual changes."""
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
                                "type": "tempo",
                                "start": 60,
                                "bpm": 100,
                                "start_bpm": 100,
                                "end_bpm": 80,
                                "duration": 8,
                            }
                        ]
                    }
                ],
            }
        )
    assert "instant" in str(exc.value).lower() or "gradual" in str(exc.value).lower()


def test_tempo_event_gradual_requires_all_fields() -> None:
    """Test that gradual tempo changes require start_bpm, end_bpm, and duration."""
    # Missing start_bpm
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
                                "type": "tempo",
                                "start": 60,
                                "end_bpm": 80,
                                "duration": 8,
                            }
                        ]
                    }
                ],
            }
        )
    assert "start_bpm" in str(exc.value)

    # Missing end_bpm
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
                                "type": "tempo",
                                "start": 60,
                                "start_bpm": 100,
                                "duration": 8,
                            }
                        ]
                    }
                ],
            }
        )
    assert "end_bpm" in str(exc.value)

    # Missing duration
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
                                "type": "tempo",
                                "start": 60,
                                "start_bpm": 100,
                                "end_bpm": 80,
                            }
                        ]
                    }
                ],
            }
        )
    assert "duration" in str(exc.value)


def test_tempo_event_bpm_bounds() -> None:
    """Test that tempo values are within valid bounds."""
    # Too low
    with pytest.raises(ValueError):
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {
                                "type": "tempo",
                                "start": 60,
                                "bpm": 10,
                            }
                        ]
                    }
                ],
            }
        )

    # Too high
    with pytest.raises(ValueError):
        validate_composition_dict(
            {
                "title": "x",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {
                                "type": "tempo",
                                "start": 60,
                                "bpm": 500,
                            }
                        ]
                    }
                ],
            }
        )

