from __future__ import annotations

import json
from pathlib import Path

import mido

from pianist.cli import main
from pianist.iterate import composition_from_midi, transpose_composition
from pianist.schema import NoteEvent, PedalEvent, TempoEvent, validate_composition_dict


def _write_test_midi(path: Path) -> None:
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)

    tr.append(mido.MetaMessage("track_name", name="Piano", time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))

    # Pedal down + a simple chord (C4+E4) for 1 beat.
    tr.append(mido.Message("control_change", control=64, value=127, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_on", note=64, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=0))

    # Pedal up at 2 beats total.
    tr.append(mido.Message("control_change", control=64, value=0, channel=0, time=480))

    # Tempo change at beat 4.
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(100), time=960))
    tr.append(mido.MetaMessage("end_of_track", time=0))

    mid.save(path)


def test_midi_import_to_composition(tmp_path: Path) -> None:
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    comp = composition_from_midi(midi_path)
    assert comp.ppq == 480
    assert comp.bpm == 120
    assert comp.tracks
    tr = comp.tracks[0]
    assert tr.channel == 0

    notes = [e for e in tr.events if isinstance(e, NoteEvent)]
    pedals = [e for e in tr.events if isinstance(e, PedalEvent)]
    tempos = [e for e in tr.events if isinstance(e, TempoEvent)]

    assert len(notes) == 1
    assert notes[0].start == 0
    assert notes[0].duration == 1
    assert notes[0].velocity == 64
    assert notes[0].pitches == [60, 64]

    assert len(pedals) == 1
    assert pedals[0].start == 0
    assert pedals[0].duration == 2
    assert pedals[0].value == 127

    assert len(tempos) == 1
    assert tempos[0].start == 4
    assert tempos[0].bpm == 100

    # Transpose helper should move the chord.
    comp2 = transpose_composition(comp, 2)
    assert notes[0].pitches == [60, 64]  # original is unchanged
    tr2 = comp2.tracks[0]
    notes2 = [e for e in tr2.events if isinstance(e, NoteEvent)]
    assert notes2[0].pitches == [62, 66]


def test_cli_iterate_from_midi_emits_valid_json(tmp_path: Path) -> None:
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "seed.json"
    rc = main(["iterate", "--in", str(midi_path), "--out", str(out_json)])
    assert rc == 0
    assert out_json.exists()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    validate_composition_dict(data)

