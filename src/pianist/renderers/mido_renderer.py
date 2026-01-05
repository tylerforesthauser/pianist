from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mido

from ..schema import Composition, NoteEvent, PedalEvent


@dataclass(frozen=True)
class _AbsMsg:
    tick: int
    msg: mido.Message | mido.MetaMessage


def _beats_to_ticks(beats: float, ppq: int) -> int:
    # 1 beat == quarter note beat by convention in schema
    return int(round(beats * ppq))


def render_midi_mido(composition: Composition, out_path: str | Path) -> Path:
    """
    Render a validated Composition into a standard MIDI file using mido.
    """
    out_path = Path(out_path)
    mid = mido.MidiFile(ticks_per_beat=composition.ppq)

    # Global / conductor track
    conductor = mido.MidiTrack()
    mid.tracks.append(conductor)
    conductor.append(mido.MetaMessage("track_name", name="Conductor", time=0))
    conductor.append(
        mido.MetaMessage(
            "time_signature",
            numerator=composition.time_signature.numerator,
            denominator=composition.time_signature.denominator,
            time=0,
        )
    )
    conductor.append(
        mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(composition.bpm), time=0)
    )

    if composition.key_signature:
        # Mido accepts values like "C", "Gm", "F#", "Bb", etc.
        conductor.append(
            mido.MetaMessage("key_signature", key=composition.key_signature, time=0)
        )

    # Note tracks
    for track in composition.tracks:
        tr = mido.MidiTrack()
        mid.tracks.append(tr)

        tr.append(mido.MetaMessage("track_name", name=track.name, time=0))
        tr.append(
            mido.Message(
                "program_change", program=track.program, channel=track.channel, time=0
            )
        )

        abs_msgs: list[_AbsMsg] = []

        for ev in track.events:
            start_tick = _beats_to_ticks(ev.start, composition.ppq)
            # Enforce minimum 1 tick to avoid zero-duration events due to rounding.
            dur_ticks = max(1, _beats_to_ticks(ev.duration, composition.ppq))
            end_tick = start_tick + dur_ticks

            if isinstance(ev, NoteEvent):
                for pitch in ev.pitches:
                    abs_msgs.append(
                        _AbsMsg(
                            start_tick,
                            mido.Message(
                                "note_on",
                                note=pitch,
                                velocity=ev.velocity,
                                channel=track.channel,
                                time=0,
                            ),
                        )
                    )
                    abs_msgs.append(
                        _AbsMsg(
                            end_tick,
                            mido.Message(
                                "note_off",
                                note=pitch,
                                velocity=0,
                                channel=track.channel,
                                time=0,
                            ),
                        )
                    )
            elif isinstance(ev, PedalEvent):
                abs_msgs.append(
                    _AbsMsg(
                        start_tick,
                        mido.Message(
                            "control_change",
                            control=64,
                            value=ev.value,
                            channel=track.channel,
                            time=0,
                        ),
                    )
                )
                abs_msgs.append(
                    _AbsMsg(
                        end_tick,
                        mido.Message(
                            "control_change",
                            control=64,
                            value=0,
                            channel=track.channel,
                            time=0,
                        ),
                    )
                )
            else:
                raise TypeError(f"Unsupported event type: {type(ev)}")

        # Stable ordering at the same tick:
        # - note_off first (avoid stuck notes)
        # - note_on next
        # - pedal-off after note_on (so same-tick note_on isn't preceded by a pedal release)
        # - other control/meta messages last
        def _sort_key(x: _AbsMsg) -> tuple[int, int]:
            msg = x.msg
            if isinstance(msg, mido.Message) and msg.type == "note_off":
                return (x.tick, 0)
            elif isinstance(msg, mido.Message) and msg.type == "note_on":
                return (x.tick, 1)
            elif (
                isinstance(msg, mido.Message)
                and msg.type == "control_change"
                and msg.control == 64
                and msg.value == 0
            ):
                return (x.tick, 2)
            else:
                return (x.tick, 3)

        abs_msgs.sort(key=_sort_key)

        last_tick = 0
        for item in abs_msgs:
            delta = item.tick - last_tick
            last_tick = item.tick
            msg = item.msg.copy(time=delta)
            tr.append(msg)

        tr.append(mido.MetaMessage("end_of_track", time=0))

    mid.save(out_path)
    return out_path

