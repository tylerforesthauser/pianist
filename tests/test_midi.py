from __future__ import annotations

from pathlib import Path

import mido

from aimusicgen.schema import Composition
from aimusicgen.midi import render_midi


def _abs_times(track: mido.MidiTrack) -> list[tuple[int, mido.Message | mido.MetaMessage]]:
    out: list[tuple[int, mido.Message | mido.MetaMessage]] = []
    t = 0
    for msg in track:
        t += msg.time
        out.append((t, msg))
    return out


def test_midi_enforces_minimum_1_tick_duration(tmp_path: Path) -> None:
    comp = Composition.model_validate(
        {
            "title": "Tiny note",
            "bpm": 120,
            "time_signature": {"numerator": 4, "denominator": 4},
            "ppq": 480,
            "tracks": [
                {
                    "events": [
                        {"type": "note", "start": 1.0, "duration": 0.0001, "pitch": "C4"}
                    ]
                }
            ],
        }
    )
    out = render_midi(comp, tmp_path / "tiny.mid")
    mid = mido.MidiFile(out)
    # Track 0 is conductor, track 1 is piano
    abs_msgs = _abs_times(mid.tracks[1])

    on_tick = None
    off_tick = None
    for tick, msg in abs_msgs:
        if isinstance(msg, mido.Message) and msg.type == "note_on" and msg.velocity > 0:
            on_tick = tick
        if isinstance(msg, mido.Message) and msg.type == "note_off":
            off_tick = tick
        if on_tick is not None and off_tick is not None:
            break

    assert on_tick is not None
    assert off_tick is not None
    assert off_tick > on_tick

