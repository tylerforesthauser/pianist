from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict

import mido

from .schema import (
    Composition,
    NoteEvent,
    PedalEvent,
    TempoEvent,
    TimeSignature,
    Track,
)


@dataclass(frozen=True)
class _RawNote:
    channel: int
    start_tick: int
    end_tick: int
    pitch: int
    velocity: int


@dataclass(frozen=True)
class _RawPedal:
    channel: int
    start_tick: int
    end_tick: int
    value: int


def _ticks_to_beats(ticks: int, ppq: int) -> float:
    # In Pianist's schema, 1 beat == quarter note.
    return ticks / ppq


def _safe_title_from_path(path: Path) -> str:
    # Path.stem is fine for most filenames; keep it stable and predictable.
    return path.stem or "Untitled"


def composition_to_canonical_json(comp: Composition) -> str:
    """
    Serialize a Composition into a stable, tweak-friendly JSON string.
    """
    payload = comp.model_dump(mode="json", exclude_none=True)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def composition_from_midi(path: Path) -> Composition:
    """
    Best-effort MIDI -> Composition import.

    This is intended to support iteration workflows (tweak, re-render, feed back into an LLM).
    It does not attempt to infer hands/voices; it uses legacy `pitches` for safety.
    """
    mid = mido.MidiFile(path)
    ppq = int(mid.ticks_per_beat or 480)

    # Defaults if the MIDI does not contain metadata.
    ts = TimeSignature(numerator=4, denominator=4)
    key_signature: str | None = None
    initial_bpm = 120.0
    tempo_events_by_tick: dict[int, float] = {}

    raw_notes: list[_RawNote] = []
    raw_pedals: list[_RawPedal] = []

    # Per-channel program + human-friendly name if present.
    channel_program: dict[int, int] = {}
    channel_name: dict[int, str] = {}

    # For global metadata, prefer the earliest tick; if ties, keep the first seen.
    ts_tick: int | None = None

    # Track absolute ticks independently (MIDI uses per-track delta times).
    for tr_idx, tr in enumerate(mid.tracks):
        abs_tick = 0
        track_name: str | None = None

        active_notes: DefaultDict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        active_pedal: dict[int, tuple[int, int] | None] = {ch: None for ch in range(16)}

        for msg in tr:
            abs_tick += int(msg.time)

            if isinstance(msg, mido.MetaMessage):
                if msg.type == "track_name":
                    track_name = str(msg.name)
                elif msg.type == "time_signature":
                    # Prefer the earliest time signature; if multiple occur at the same
                    # tick (common at tick 0 across tracks), keep the first seen.
                    if ts_tick is None or abs_tick < ts_tick:
                        ts = TimeSignature(
                            numerator=int(msg.numerator),
                            denominator=int(msg.denominator),
                        )
                        ts_tick = abs_tick
                elif msg.type == "key_signature":
                    if key_signature is None:
                        key_signature = str(msg.key)
                elif msg.type == "set_tempo":
                    bpm = float(mido.tempo2bpm(msg.tempo))
                    tempo_events_by_tick[abs_tick] = bpm
                continue

            # Channel voice messages
            if not isinstance(msg, mido.Message):
                continue

            ch = int(getattr(msg, "channel", 0))

            if msg.type == "program_change":
                channel_program.setdefault(ch, int(msg.program))
                if track_name and ch not in channel_name:
                    channel_name[ch] = track_name

            elif msg.type == "note_on" and int(msg.velocity) > 0:
                active_notes[(ch, int(msg.note))].append((abs_tick, int(msg.velocity)))
                if track_name and ch not in channel_name:
                    channel_name[ch] = track_name

            elif msg.type == "note_off" or (msg.type == "note_on" and int(msg.velocity) == 0):
                stack = active_notes[(ch, int(msg.note))]
                if stack:
                    start_tick, vel = stack.pop(0)
                    end_tick = abs_tick
                    if end_tick > start_tick:
                        raw_notes.append(
                            _RawNote(
                                channel=ch,
                                start_tick=start_tick,
                                end_tick=end_tick,
                                pitch=int(msg.note),
                                velocity=int(vel),
                            )
                        )

            elif msg.type == "control_change" and int(msg.control) == 64:
                value = int(msg.value)
                if value > 0:
                    # Start a pedal window if not already down.
                    if active_pedal[ch] is None:
                        active_pedal[ch] = (abs_tick, value)
                else:
                    # Release.
                    current = active_pedal.get(ch)
                    if current is not None:
                        start_tick, down_value = current
                        end_tick = abs_tick
                        if end_tick >= start_tick:
                            raw_pedals.append(
                                _RawPedal(
                                    channel=ch,
                                    start_tick=start_tick,
                                    end_tick=end_tick,
                                    value=int(down_value),
                                )
                            )
                        active_pedal[ch] = None

        # Close out any notes/pedals still open at track end (best-effort).
        end_tick = abs_tick
        for (ch, pitch), stack in active_notes.items():
            for start_tick, vel in stack:
                if end_tick > start_tick:
                    raw_notes.append(
                        _RawNote(
                            channel=ch,
                            start_tick=start_tick,
                            end_tick=end_tick,
                            pitch=int(pitch),
                            velocity=int(vel),
                        )
                    )
        for ch, current in active_pedal.items():
            if current is not None:
                start_tick, down_value = current
                if end_tick >= start_tick:
                    raw_pedals.append(
                        _RawPedal(
                            channel=ch,
                            start_tick=start_tick,
                            end_tick=end_tick,
                            value=int(down_value),
                        )
                    )

    # Build tempo events + initial bpm.
    if 0 in tempo_events_by_tick:
        initial_bpm = tempo_events_by_tick[0]
    tempo_events: list[TempoEvent] = []
    for tick, bpm in sorted(tempo_events_by_tick.items()):
        if tick == 0:
            continue
        tempo_events.append(TempoEvent(start=_ticks_to_beats(tick, ppq), bpm=bpm))

    # Group notes into chords when start/end/velocity align.
    by_channel: DefaultDict[int, list[_RawNote]] = defaultdict(list)
    for n in raw_notes:
        by_channel[n.channel].append(n)

    tracks: list[Track] = []
    for ch in sorted(by_channel.keys()):
        channel_notes = by_channel[ch]
        chord_groups: DefaultDict[tuple[int, int, int], list[int]] = defaultdict(list)
        for n in channel_notes:
            key = (n.start_tick, n.end_tick, n.velocity)
            chord_groups[key].append(n.pitch)

        note_events: list[NoteEvent] = []
        for (start_tick, end_tick, vel), pitches in chord_groups.items():
            pitches_sorted = sorted({int(p) for p in pitches})
            start = _ticks_to_beats(start_tick, ppq)
            duration = _ticks_to_beats(end_tick - start_tick, ppq)
            # Guard against zero-duration due to malformed MIDI.
            if duration <= 0:
                continue
            note_events.append(
                NoteEvent(start=start, duration=duration, pitches=pitches_sorted, velocity=vel)
            )

        pedal_events: list[PedalEvent] = []
        for p in raw_pedals:
            if p.channel != ch:
                continue
            start = _ticks_to_beats(p.start_tick, ppq)
            duration = _ticks_to_beats(p.end_tick - p.start_tick, ppq)
            if duration < 0:
                continue
            pedal_events.append(PedalEvent(start=start, duration=duration, value=p.value))

        events = sorted(
            [*note_events, *pedal_events],
            key=lambda e: (float(getattr(e, "start", 0.0)), getattr(e, "type", "")),
        )

        tracks.append(
            Track(
                name=channel_name.get(ch, f"Channel {ch}"),
                channel=ch,
                program=channel_program.get(ch, 0),
                events=events,
            )
        )

    if not tracks:
        tracks = [Track()]

    # Tempo events are global; store them once (renderer collects from all tracks).
    if tempo_events:
        tracks[0].events.extend(tempo_events)
        tracks[0].events.sort(
            key=lambda e: (float(getattr(e, "start", 0.0)), getattr(e, "type", ""))
        )

    return Composition(
        title=_safe_title_from_path(path),
        bpm=initial_bpm,
        time_signature=ts,
        key_signature=key_signature,
        ppq=ppq,
        tracks=tracks,
    )


def transpose_composition(comp: Composition, semitones: int) -> Composition:
    """
    Transpose all note pitches by `semitones` (can be negative).

    Notes are clamped to the MIDI pitch range [0, 127].
    """
    if semitones == 0:
        return comp

    out = comp.model_copy(deep=True)

    def _clamp(p: int) -> int:
        return max(0, min(127, p))

    for tr in out.tracks:
        for ev in tr.events:
            if isinstance(ev, NoteEvent):
                ev.pitches = [_clamp(int(p) + semitones) for p in ev.pitches]
                if ev.notes is not None:
                    for n in ev.notes:
                        n.pitch = _clamp(int(n.pitch) + semitones)
                if ev.groups is not None:
                    for g in ev.groups:
                        g.pitches = [_clamp(int(p) + semitones) for p in g.pitches]
    return out


def iteration_prompt_template(comp: Composition, instructions: str | None = None) -> str:
    """
    Build a copy/paste-friendly prompt for iterating with an LLM.

    This does NOT call an LLM. It just packages the prior work + constraints in a
    way that's easy to feed back into your model of choice.
    """
    seed = composition_to_canonical_json(comp).strip()
    requested = (instructions or "").strip() or "<describe the changes you want>"
    return (
        "SYSTEM:\n"
        "You are an expert music composition generator. Output MUST be valid JSON only.\n"
        "Hard requirements:\n"
        "- Output ONLY a single JSON object. No markdown. No explanations.\n"
        "- The JSON must validate against the Pianist composition schema (note/pedal/tempo/section events).\n"
        "- Preserve existing motifs/structure unless asked; keep timing continuous (avoid long silences).\n"
        "\n"
        "USER:\n"
        "Here is the previous composition JSON (the 'seed'). Modify it according to the requested changes.\n"
        "Return a COMPLETE new composition JSON (not a patch/diff).\n"
        "\n"
        "SEED JSON:\n"
        f"{seed}\n"
        "\n"
        "REQUESTED CHANGES:\n"
        f"{requested}\n"
    )

