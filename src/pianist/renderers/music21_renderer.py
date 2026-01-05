from __future__ import annotations

import copy
from pathlib import Path

from music21 import chord, instrument, meter, metadata, note, stream, tempo

from ..schema import Composition, NoteEvent, PedalEvent


def _beats_to_quarter_length(beats: float) -> float:
    # Schema defines "beat" as quarter-note beat for simplicity.
    return float(beats)


def to_music21_score(composition: Composition) -> stream.Score:
    """
    Convert a validated Composition into a music21 Score.
    """
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = composition.title

    for t in composition.tracks:
        part = stream.Part()
        part.partName = t.name

        # Instrument: keep it simple for now; set MIDI program.
        inst = instrument.Instrument()
        inst.midiProgram = int(t.program)
        part.insert(0, inst)
        part.insert(
            0,
            meter.TimeSignature(
                f"{composition.time_signature.numerator}/{composition.time_signature.denominator}"
            ),
        )
        part.insert(0, tempo.MetronomeMark(number=float(composition.bpm)))

        # We currently ignore key_signature for rendering, since music21's
        # key signature parsing is nuanced (major/minor vs mode strings).
        # It can be added once we standardize accepted formats.

        for ev in t.events:
            start = _beats_to_quarter_length(ev.start)
            dur = _beats_to_quarter_length(ev.duration)

            if isinstance(ev, NoteEvent):
                if len(ev.pitches) == 1:
                    n = note.Note(midi=int(ev.pitches[0]))
                    n.volume.velocity = int(ev.velocity)
                    n.duration.quarterLength = dur
                    part.insert(start, n)
                else:
                    c = chord.Chord([note.Note(midi=int(p)) for p in ev.pitches])
                    for cn in c.notes:
                        cn.volume.velocity = int(ev.velocity)
                    c.duration.quarterLength = dur
                    part.insert(start, c)
            elif isinstance(ev, PedalEvent):
                # music21 control-change insertion is fiddly; for v1 we simply
                # ignore pedal events in the music21 backend.
                #
                # (Pedal is fully supported via the deterministic mido backend.)
                continue
            else:
                raise TypeError(f"Unsupported event type: {type(ev)}")

        # Avoid containment issues if callers later reuse elements/score.
        score.append(copy.deepcopy(part))

    return score


def render_midi_music21(composition: Composition, out_path: str | Path) -> Path:
    """
    Render a validated Composition to a MIDI file via music21.
    """
    out_path = Path(out_path)
    score = to_music21_score(composition)
    score.write("midi", fp=str(out_path))
    return out_path

