from __future__ import annotations

from pathlib import Path

import mido

from aimusicgen.parser import parse_composition_from_text
from aimusicgen.midi import render_midi


def test_parse_and_render(tmp_path: Path) -> None:
    text = (Path(__file__).parent.parent / "examples" / "model_output.txt").read_text(
        encoding="utf-8"
    )
    comp = parse_composition_from_text(text)
    out = render_midi(comp, tmp_path / "out.mid")

    assert out.exists()
    mid = mido.MidiFile(out)
    # At least conductor + 1 note track
    assert len(mid.tracks) >= 2
    # Ensure we actually wrote some note events
    note_msgs = [
        msg
        for tr in mid.tracks
        for msg in tr
        if isinstance(msg, mido.Message) and msg.type in ("note_on", "note_off")
    ]
    assert note_msgs
