from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mido

from ..schema import Composition, NoteEvent, PedalEvent, SectionEvent, TempoEvent


@dataclass(frozen=True)
class _AbsMsg:
    tick: int
    msg: mido.Message | mido.MetaMessage


def _beats_to_ticks(beats: float, ppq: int) -> int:
    # 1 beat == quarter note beat by convention in schema
    return int(round(beats * ppq))


def _expand_gradual_tempo_change(
    start: float,
    start_bpm: float,
    end_bpm: float,
    duration: float,
    ppq: int,
) -> list[tuple[int, float]]:
    """
    Expand a gradual tempo change into discrete tempo change events.

    Returns a list of (tick, bpm) tuples representing tempo changes.
    Uses a step size of 0.5 beats for smooth approximation.
    """
    steps: list[tuple[int, float]] = []
    step_size = 0.5  # beats between tempo changes
    num_steps = max(1, int(round(duration / step_size)))

    for i in range(num_steps + 1):
        progress = i / num_steps if num_steps > 0 else 1.0
        # Linear interpolation
        current_bpm = start_bpm + (end_bpm - start_bpm) * progress
        beat_position = start + (duration * progress)
        tick = _beats_to_ticks(beat_position, ppq)
        steps.append((tick, current_bpm))

    return steps


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

    # Collect tempo events from all tracks first to find initial tempo override
    tempo_changes: list[tuple[int, float]] = []  # (tick, bpm)
    initial_tempo_override: float | None = None

    for track in composition.tracks:
        for ev in track.events:
            if isinstance(ev, TempoEvent):
                if ev.start == 0:
                    # Tempo change at beat 0: override initial tempo
                    if ev.bpm is not None:
                        initial_tempo_override = ev.bpm
                    elif ev.start_bpm is not None:
                        initial_tempo_override = ev.start_bpm
                    # Still process gradual changes starting at 0
                    if ev.start_bpm is not None and ev.end_bpm is not None and ev.duration is not None:
                        steps = _expand_gradual_tempo_change(
                            ev.start,
                            ev.start_bpm,
                            ev.end_bpm,
                            ev.duration,
                            composition.ppq,
                        )
                        # Skip the first step if it's at tick 0 (we'll use initial_tempo_override)
                        for tick, bpm in steps:
                            if tick > 0:
                                tempo_changes.append((tick, bpm))
                    continue

                if ev.bpm is not None:
                    # Instant tempo change
                    tick = _beats_to_ticks(ev.start, composition.ppq)
                    tempo_changes.append((tick, ev.bpm))
                else:
                    # Gradual tempo change
                    assert ev.start_bpm is not None
                    assert ev.end_bpm is not None
                    assert ev.duration is not None
                    steps = _expand_gradual_tempo_change(
                        ev.start,
                        ev.start_bpm,
                        ev.end_bpm,
                        ev.duration,
                        composition.ppq,
                    )
                    tempo_changes.extend(steps)

    # Use initial tempo (from composition.bpm or override from tempo event at beat 0)
    initial_bpm = initial_tempo_override if initial_tempo_override is not None else composition.bpm
    conductor.append(
        mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(initial_bpm), time=0)
    )

    if composition.key_signature:
        # Mido accepts values like "C", "Gm", "F#", "Bb", etc.
        conductor.append(
            mido.MetaMessage("key_signature", key=composition.key_signature, time=0)
        )

    # Sort tempo changes by tick, then insert into conductor track
    tempo_changes.sort(key=lambda x: x[0])

    # Remove duplicates at the same tick (keep the last one)
    if tempo_changes:
        deduplicated: list[tuple[int, float]] = []
        last_tick = -1
        for tick, bpm in tempo_changes:
            if tick == last_tick:
                # Replace the previous entry at this tick
                deduplicated[-1] = (tick, bpm)
            else:
                deduplicated.append((tick, bpm))
                last_tick = tick
        tempo_changes = deduplicated

    # Store tempo changes to insert after we've processed all tracks
    # (we'll insert them into conductor track at the end)

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
            # Tempo events are collected above and handled separately
            if isinstance(ev, TempoEvent):
                continue
            # Section events are metadata markers, skip during rendering
            if isinstance(ev, SectionEvent):
                continue

            start_tick = _beats_to_ticks(ev.start, composition.ppq)
            # For pedal events, allow duration=0 (instant release/press).
            # For note events, enforce minimum 1 tick to avoid zero-duration events due to rounding.
            if isinstance(ev, PedalEvent):
                dur_ticks = _beats_to_ticks(ev.duration, composition.ppq)
            elif isinstance(ev, NoteEvent):
                dur_ticks = max(1, _beats_to_ticks(ev.duration, composition.ppq))
            else:
                raise TypeError(f"Unsupported event type: {type(ev)}")
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
                # For duration=0, only create a single message (instant press or release)
                # For duration>0, create press at start and release at end
                if dur_ticks == 0:
                    # Instant action: only send the value change, no release
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
                else:
                    # Sustained pedal: press at start, release at end
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
            elif isinstance(ev, TempoEvent):
                # Tempo events are collected above and handled separately
                # Skip them here to avoid duplicate processing
                pass
            elif isinstance(ev, SectionEvent):
                # Section events are metadata markers, skip during rendering
                pass
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

    # Insert tempo changes into conductor track
    if tempo_changes:
        # Collect existing conductor track messages with their absolute ticks
        existing_msgs: list[tuple[int, mido.MetaMessage]] = []
        current_tick = 0
        for msg in conductor:
            if msg.type == "set_tempo" and current_tick == 0:
                # Skip the initial tempo message (we'll keep it separately)
                current_tick += msg.time
                continue
            if msg.type != "end_of_track":
                current_tick += msg.time
                existing_msgs.append((current_tick, msg))

        # Combine tempo changes with existing messages
        all_conductor_msgs: list[tuple[int, mido.MetaMessage]] = []
        for tick, bpm in tempo_changes:
            tempo_msg = mido.MetaMessage(
                "set_tempo", tempo=mido.bpm2tempo(bpm), time=0
            )
            all_conductor_msgs.append((tick, tempo_msg))
        all_conductor_msgs.extend(existing_msgs)
        all_conductor_msgs.sort(key=lambda x: x[0])

        # Rebuild conductor track with delta times
        new_conductor = mido.MidiTrack()
        new_conductor.append(mido.MetaMessage("track_name", name="Conductor", time=0))
        new_conductor.append(
            mido.MetaMessage(
                "time_signature",
                numerator=composition.time_signature.numerator,
                denominator=composition.time_signature.denominator,
                time=0,
            )
        )
        new_conductor.append(
            mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(initial_bpm), time=0)
        )
        if composition.key_signature:
            new_conductor.append(
                mido.MetaMessage("key_signature", key=composition.key_signature, time=0)
            )

        last_tick = 0
        for tick, msg in all_conductor_msgs:
            delta = tick - last_tick
            last_tick = tick
            new_conductor.append(msg.copy(time=delta))

        new_conductor.append(mido.MetaMessage("end_of_track", time=0))
        mid.tracks[0] = new_conductor

    mid.save(out_path)
    return out_path

