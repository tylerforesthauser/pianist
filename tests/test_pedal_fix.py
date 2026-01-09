"""Tests for pedal pattern fixing functionality."""

from __future__ import annotations

import warnings

from pianist.pedal_fix import fix_pedal_patterns
from pianist.schema import PedalEvent, validate_composition_dict


def test_fix_pedal_press_release_pair() -> None:
    """Test that press-release pairs are merged into single duration>0 event."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                            {"type": "pedal", "start": 4, "duration": 0, "value": 0},
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 1
    assert pedals[0].start == 0
    assert pedals[0].duration == 4
    assert pedals[0].value == 127


def test_fix_orphaned_press() -> None:
    """Test that orphaned presses are extended to reasonable default."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "note", "start": 0, "duration": 8, "pitches": [60]},
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 1
    assert pedals[0].start == 0
    assert pedals[0].duration > 0
    assert pedals[0].value == 127


def test_fix_preserves_correct_patterns() -> None:
    """Test that already correct patterns (duration>0) are preserved."""
    comp = validate_composition_dict(
        {
            "title": "Test",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "tracks": [
                {
                    "events": [
                        {"type": "pedal", "start": 0, "duration": 4, "value": 127},
                        {"type": "pedal", "start": 8, "duration": 2, "value": 127},
                    ]
                }
            ],
        }
    )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 2
    assert pedals[0].duration == 4
    assert pedals[1].duration == 2


def test_fix_preserves_annotations() -> None:
    """Test that section/phrase annotations are preserved when merging."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {
                                "type": "pedal",
                                "start": 0,
                                "duration": 0,
                                "value": 127,
                                "section": "A",
                            },
                            {
                                "type": "pedal",
                                "start": 4,
                                "duration": 0,
                                "value": 0,
                            },
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 1
    assert pedals[0].section == "A"


def test_fix_handles_multiple_tracks() -> None:
    """Test that fix works correctly with multiple tracks."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                            {"type": "pedal", "start": 4, "duration": 0, "value": 0},
                        ]
                    },
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                            {"type": "pedal", "start": 2, "duration": 0, "value": 0},
                        ]
                    },
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    assert len(fixed.tracks) == 2
    pedals_0 = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    pedals_1 = [e for e in fixed.tracks[1].events if isinstance(e, PedalEvent)]
    assert len(pedals_0) == 1
    assert len(pedals_1) == 1
    assert pedals_0[0].duration == 4
    assert pedals_1[0].duration == 2


def test_fix_extends_to_next_pedal() -> None:
    """Test that orphaned presses extend to next pedal event."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                            {"type": "pedal", "start": 8, "duration": 4, "value": 127},
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 2
    # First pedal should extend to just before the second
    assert pedals[0].duration > 0
    assert pedals[0].duration < 8
    assert pedals[1].duration == 4  # Second pedal unchanged


def test_fix_handles_same_start_time() -> None:
    """Test that press and release with same start time are skipped."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                            {"type": "pedal", "start": 0, "duration": 0, "value": 0},
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    # Both events should be skipped (invalid pattern)
    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 0


def test_fix_handles_empty_events() -> None:
    """Test that fix handles tracks with no events with duration attribute."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Suppress validator warnings
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {"type": "pedal", "start": 0, "duration": 0, "value": 127},
                        ]
                    }
                ],
            }
        )

    # Should not raise ValueError even with no events with duration
    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 1
    assert pedals[0].duration > 0  # Should use fallback default


def test_fix_handles_half_pedaling_duration_zero() -> None:
    """Test that half-pedaling events with duration=0 are preserved as-is."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {
                                "type": "pedal",
                                "start": 0,
                                "duration": 0,
                                "value": 64,
                            },  # Half-pedaling
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 1
    assert pedals[0].duration == 0  # Preserved as-is
    assert pedals[0].value == 64  # Preserved as-is


def test_fix_preserves_half_pedaling_duration_positive() -> None:
    """Test that half-pedaling events with duration>0 are preserved."""
    comp = validate_composition_dict(
        {
            "title": "Test",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "tracks": [
                {
                    "events": [
                        {"type": "pedal", "start": 0, "duration": 4, "value": 64},  # Half-pedaling
                    ]
                }
            ],
        }
    )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    assert len(pedals) == 1
    assert pedals[0].duration == 4  # Preserved
    assert pedals[0].value == 64  # Preserved


def test_fix_handles_two_presses_one_release() -> None:
    """Test that two consecutive presses followed by one release only pairs first press with release."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        comp = validate_composition_dict(
            {
                "title": "Test",
                "bpm": 120,
                "time_signature": {"numerator": 4, "denominator": 4},
                "tracks": [
                    {
                        "events": [
                            {
                                "type": "pedal",
                                "start": 0,
                                "duration": 0,
                                "value": 127,
                            },  # First press
                            {
                                "type": "pedal",
                                "start": 2,
                                "duration": 0,
                                "value": 127,
                            },  # Second press
                            {
                                "type": "pedal",
                                "start": 4,
                                "duration": 0,
                                "value": 0,
                            },  # Single release
                        ]
                    }
                ],
            }
        )

    fixed = fix_pedal_patterns(comp)

    pedals = [e for e in fixed.tracks[0].events if isinstance(e, PedalEvent)]
    # Should have: first press paired with release (duration=4), second press extended
    assert len(pedals) == 2
    # First pedal should be paired with release
    first_pedal = next(p for p in pedals if p.start == 0)
    assert first_pedal.duration == 4  # Paired with release at 4
    # Second pedal should be extended (no release available)
    second_pedal = next(p for p in pedals if p.start == 2)
    assert second_pedal.duration > 0  # Extended to default
