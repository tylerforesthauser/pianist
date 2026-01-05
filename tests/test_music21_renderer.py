from __future__ import annotations

from pianist.renderers.music21_renderer import to_music21_score
from pianist.schema import validate_composition_dict


def test_to_music21_score_builds_score_with_parts_and_notes() -> None:
    comp = validate_composition_dict(
        {
            "title": "x",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "tracks": [
                {
                    "name": "Piano",
                    "program": 0,
                    "channel": 0,
                    "events": [
                        {
                            "type": "note",
                            "start": 0,
                            "duration": 1,
                            "pitches": ["C4", "E4", "G4"],
                            "velocity": 80,
                        }
                    ],
                }
            ],
        }
    )

    score = to_music21_score(comp)
    parts = list(score.parts)
    assert len(parts) == 1
    p = parts[0]
    # Ensure at least one note/chord element exists
    assert list(p.recurse().getElementsByClass("Chord"))

