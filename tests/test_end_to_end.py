from __future__ import annotations

from pathlib import Path

import mido

from pianist.parser import parse_composition_from_text
from pianist.renderers.mido_renderer import render_midi_mido


def _assert_valid_midi(path: Path) -> None:
    assert path.exists()
    mid = mido.MidiFile(path)
    # At least conductor-ish + 1 note track
    assert len(mid.tracks) >= 1
    note_msgs = [
        msg
        for tr in mid.tracks
        for msg in tr
        if isinstance(msg, mido.Message) and msg.type in ("note_on", "note_off")
    ]
    assert note_msgs


def test_parse_and_render(tmp_path: Path) -> None:
    text = (Path(__file__).parent.parent / "examples" / "model_output.txt").read_text(
        encoding="utf-8"
    )
    comp = parse_composition_from_text(text)
    out = render_midi_mido(comp, tmp_path / "out.mid")
    _assert_valid_midi(out)

