from __future__ import annotations

import json
from pathlib import Path

import mido

from pianist.analyze import analyze_midi, analysis_prompt_template
from pianist.cli import main


def _write_test_midi(path: Path) -> None:
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)

    tr.append(mido.MetaMessage("track_name", name="Piano", time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.MetaMessage("key_signature", key="C", time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))

    # Pedal down + C major chord for 1 beat.
    tr.append(mido.Message("control_change", control=64, value=127, channel=0, time=0))
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_on", note=64, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_on", note=67, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=0))
    tr.append(mido.Message("note_off", note=67, velocity=0, channel=0, time=0))

    # Pedal up at 2 beats total.
    tr.append(mido.Message("control_change", control=64, value=0, channel=0, time=480))

    # Tempo change at beat 4 (still within file end).
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(100), time=960))
    tr.append(mido.MetaMessage("end_of_track", time=0))

    mid.save(path)


def test_analyze_midi_basic_fields(tmp_path: Path) -> None:
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    analysis = analyze_midi(midi_path)
    assert analysis.ppq == 480
    assert analysis.duration_ticks > 0
    assert analysis.duration_beats == analysis.duration_ticks / 480
    assert analysis.duration_seconds > 0
    assert analysis.time_signature[0].numerator == 4
    assert analysis.time_signature[0].denominator == 4
    assert analysis.key_signature[0].key == "C"

    # Tempo points should include tick 0 and the later change.
    assert analysis.tempo[0].tick == 0
    assert analysis.tempo[0].bpm == 120
    assert any(tp.bpm == 100 for tp in analysis.tempo)

    assert analysis.instruments
    assert analysis.instruments[0].channel == 0
    assert analysis.instruments[0].program == 0

    assert analysis.tracks
    tr = analysis.tracks[0]
    assert tr.channel == 0
    assert tr.note_count == 3
    assert tr.chord_onset_count == 1
    assert tr.chord_size.median == 3
    assert tr.pitch_min == 60
    assert tr.pitch_max == 67
    assert tr.velocity.median == 64
    assert tr.duration_beats.median == 1
    assert tr.pedal_coverage_ratio is not None


def test_analysis_prompt_template_contains_key_fields(tmp_path: Path) -> None:
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)
    analysis = analyze_midi(midi_path)

    prompt = analysis_prompt_template(analysis, instructions="Write a calm 32-bar nocturne.")
    assert "Output MUST be valid JSON only" in prompt
    assert "REFERENCE ANALYSIS" in prompt
    assert "Write a calm 32-bar nocturne." in prompt


def test_cli_analyze_json_and_prompt_outputs(tmp_path: Path) -> None:
    midi_path = tmp_path / "in.mid"
    _write_test_midi(midi_path)

    out_json = tmp_path / "analysis.json"
    prompt_path = tmp_path / "prompt.txt"
    rc = main(
        [
            "analyze",
            "--in",
            str(midi_path),
            "--format",
            "both",
            "--out",
            str(out_json),
            "--prompt-out",
            str(prompt_path),
            "--instructions",
            "Compose something lyrical.",
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert prompt_path.exists()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["ppq"] == 480
    assert "tracks" in data and data["tracks"]

    prompt = prompt_path.read_text(encoding="utf-8")
    assert "Compose something lyrical." in prompt

