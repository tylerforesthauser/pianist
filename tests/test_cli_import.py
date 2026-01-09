"""Tests for the import command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import mido

from pianist.cli import main
from pianist.schema import validate_composition_dict

if TYPE_CHECKING:
    from pathlib import Path


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


def test_cli_import_from_midi_emits_valid_json(tmp_path: Path) -> None:
    """Test that import command converts MIDI to valid JSON."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "seed.json"
    rc = main(["import", "-i", str(midi_path), "-o", str(out_json)])
    assert rc == 0
    assert out_json.exists()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    validate_composition_dict(data)


def test_cli_import_stdout_output(tmp_path: Path, capsys) -> None:
    """Test that import outputs to stdout when --output is omitted."""
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    rc = main(["import", "-i", str(midi_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "title" in captured.out.lower() or '"title"' in captured.out


def test_cli_import_rejects_non_midi_file(tmp_path: Path) -> None:
    """Test that import errors when input is not a MIDI file."""
    text_file = tmp_path / "not_midi.txt"
    text_file.write_text("not a midi file", encoding="utf-8")

    rc = main(["import", "-i", str(text_file)])
    assert rc == 1
