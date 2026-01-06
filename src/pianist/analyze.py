from __future__ import annotations

import json
import math
import os
import statistics
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, DefaultDict, Literal

import mido
from pydantic import BaseModel, Field

from .parser import parse_json_dict_from_text


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
    return ticks / ppq


def _beats_to_seconds(beats: float, bpm: float) -> float:
    return (60.0 * beats) / bpm


def _format_key(root_pc: int, mode: Literal["major", "minor"]) -> str:
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    root = names[root_pc % 12]
    return f"{root} {mode}"


def _estimate_key_from_pitch_classes(pc_counts: list[int]) -> tuple[str, float]:
    """
    Krumhansl-Schmuckler style key estimation using simple pitch-class profiles.

    Returns (estimated_key, confidence) where confidence is a relative score gap.
    """
    # Classic K-S profiles (normalized-ish) for major/minor.
    major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

    def corr(a: list[float], b: list[float]) -> float:
        ma = sum(a) / len(a)
        mb = sum(b) / len(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        da = math.sqrt(sum((x - ma) ** 2 for x in a))
        db = math.sqrt(sum((y - mb) ** 2 for y in b))
        if da == 0 or db == 0:
            return 0.0
        return num / (da * db)

    pcs = [float(x) for x in pc_counts]
    total = sum(pcs)
    if total <= 0:
        return ("unknown", 0.0)

    scores: list[tuple[str, float]] = []
    for root in range(12):
        maj = [major_profile[(i - root) % 12] for i in range(12)]
        minr = [minor_profile[(i - root) % 12] for i in range(12)]
        scores.append((_format_key(root, "major"), corr(pcs, maj)))
        scores.append((_format_key(root, "minor"), corr(pcs, minr)))

    scores.sort(key=lambda x: x[1], reverse=True)
    best_key, best = scores[0]
    second = scores[1][1] if len(scores) > 1 else 0.0
    # Map score gap to a loose confidence [0,1].
    confidence = max(0.0, min(1.0, (best - second) / 0.25))  # 0.25 is an empirical-ish gap scale
    return (best_key, confidence)


def _safe_mean(xs: list[float]) -> float | None:
    return float(statistics.fmean(xs)) if xs else None


def _safe_median(xs: list[float]) -> float | None:
    return float(statistics.median(xs)) if xs else None


def _safe_quantile(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs2 = sorted(xs)
    idx = int(round((len(xs2) - 1) * q))
    return float(xs2[idx])


class TempoPoint(BaseModel):
    tick: int = Field(ge=0)
    bpm: float = Field(ge=20, lt=400)


class TimeSignaturePoint(BaseModel):
    tick: int = Field(ge=0)
    numerator: int = Field(ge=1, le=32)
    denominator: int = Field(ge=1)


class KeySignaturePoint(BaseModel):
    tick: int = Field(ge=0)
    key: str


class ChannelInstrument(BaseModel):
    channel: int = Field(ge=0, le=15)
    program: int = Field(ge=0, le=127)
    name: str | None = None


class Distribution(BaseModel):
    min: float | None = None
    p25: float | None = None
    median: float | None = None
    mean: float | None = None
    p75: float | None = None
    max: float | None = None


class TrackAnalysis(BaseModel):
    channel: int = Field(ge=0, le=15)
    name: str
    program: int = Field(ge=0, le=127)

    note_count: int = Field(ge=0)
    chord_onset_count: int = Field(ge=0)
    chord_size: Distribution

    pitch_min: int | None = Field(default=None, ge=0, le=127)
    pitch_max: int | None = Field(default=None, ge=0, le=127)
    top_pitches: list[int] = Field(default_factory=list)
    pitch_class_histogram: list[int] = Field(default_factory=lambda: [0] * 12)
    estimated_key: str | None = None
    estimated_key_confidence: float | None = Field(default=None, ge=0, le=1)

    velocity: Distribution
    duration_beats: Distribution

    note_density_per_bar: float | None = None
    pedal_coverage_ratio: float | None = Field(default=None, ge=0, le=1)
    melodic_interval_histogram: dict[str, int] = Field(default_factory=dict)


class MidiAnalysis(BaseModel):
    source_path: str
    ppq: int = Field(ge=24, le=32768)

    duration_ticks: int = Field(ge=0)
    duration_beats: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    estimated_bar_count: float = Field(ge=0)

    tempo: list[TempoPoint] = Field(default_factory=list)
    time_signature: list[TimeSignaturePoint] = Field(default_factory=list)
    key_signature: list[KeySignaturePoint] = Field(default_factory=list)

    instruments: list[ChannelInstrument] = Field(default_factory=list)
    tracks: list[TrackAnalysis] = Field(default_factory=list)

    summary: dict[str, str] = Field(default_factory=dict)

    def to_pretty_json(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True)
class _MidiRawParseResult:
    path: Path
    ppq: int
    tempo_by_tick: dict[int, float]
    ts_by_tick: dict[int, tuple[int, int]]
    key_by_tick: dict[int, str]
    channel_program: dict[int, int]
    channel_name: dict[int, str]
    raw_notes: list[_RawNote]
    raw_pedals: list[_RawPedal]
    end_tick_global: int


def _parse_midi_raw(path: str | Path) -> _MidiRawParseResult:
    path = Path(path)
    mid = mido.MidiFile(path)
    ppq = int(mid.ticks_per_beat or 480)

    tempo_by_tick: dict[int, float] = {}
    ts_by_tick: dict[int, tuple[int, int]] = {}
    key_by_tick: dict[int, str] = {}

    channel_program: dict[int, int] = {}
    channel_name: dict[int, str] = {}

    raw_notes: list[_RawNote] = []
    raw_pedals: list[_RawPedal] = []

    end_tick_global = 0

    for tr in mid.tracks:
        abs_tick = 0
        track_name: str | None = None

        active_notes: DefaultDict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        active_pedal: dict[int, tuple[int, int] | None] = {ch: None for ch in range(16)}

        for msg in tr:
            abs_tick += int(msg.time)
            end_tick_global = max(end_tick_global, abs_tick)

            if isinstance(msg, mido.MetaMessage):
                if msg.type == "track_name":
                    track_name = str(msg.name)
                elif msg.type == "set_tempo":
                    tempo_by_tick[abs_tick] = float(mido.tempo2bpm(msg.tempo))
                elif msg.type == "time_signature":
                    ts_by_tick.setdefault(abs_tick, (int(msg.numerator), int(msg.denominator)))
                elif msg.type == "key_signature":
                    key_by_tick.setdefault(abs_tick, str(msg.key))
                continue

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
                    if active_pedal[ch] is None:
                        active_pedal[ch] = (abs_tick, value)
                else:
                    current = active_pedal.get(ch)
                    if current is not None:
                        start_tick, down_value = current
                        end_tick = abs_tick
                        if end_tick > start_tick:
                            raw_pedals.append(
                                _RawPedal(
                                    channel=ch,
                                    start_tick=start_tick,
                                    end_tick=end_tick,
                                    value=int(down_value),
                                )
                            )
                        active_pedal[ch] = None

        # Close out open notes/pedals at end of track.
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
                if end_tick > start_tick:
                    raw_pedals.append(
                        _RawPedal(
                            channel=ch,
                            start_tick=start_tick,
                            end_tick=end_tick,
                            value=int(down_value),
                        )
                    )

    return _MidiRawParseResult(
        path=path,
        ppq=ppq,
        tempo_by_tick=tempo_by_tick,
        ts_by_tick=ts_by_tick,
        key_by_tick=key_by_tick,
        channel_program=channel_program,
        channel_name=channel_name,
        raw_notes=raw_notes,
        raw_pedals=raw_pedals,
        end_tick_global=end_tick_global,
    )


def analyze_midi(path: str | Path) -> MidiAnalysis:
    """
    Analyze a MIDI file and return prompt-friendly statistics.
    """
    path = Path(path)
    mid = mido.MidiFile(path)
    ppq = int(mid.ticks_per_beat or 480)

    tempo_by_tick: dict[int, float] = {}
    ts_by_tick: dict[int, tuple[int, int]] = {}
    key_by_tick: dict[int, str] = {}

    channel_program: dict[int, int] = {}
    channel_name: dict[int, str] = {}

    raw_notes: list[_RawNote] = []
    raw_pedals: list[_RawPedal] = []

    end_tick_global = 0

    for tr in mid.tracks:
        abs_tick = 0
        track_name: str | None = None

        active_notes: DefaultDict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        active_pedal: dict[int, tuple[int, int] | None] = {ch: None for ch in range(16)}

        for msg in tr:
            abs_tick += int(msg.time)
            end_tick_global = max(end_tick_global, abs_tick)

            if isinstance(msg, mido.MetaMessage):
                if msg.type == "track_name":
                    track_name = str(msg.name)
                elif msg.type == "set_tempo":
                    tempo_by_tick[abs_tick] = float(mido.tempo2bpm(msg.tempo))
                elif msg.type == "time_signature":
                    ts_by_tick.setdefault(
                        abs_tick, (int(msg.numerator), int(msg.denominator))
                    )
                elif msg.type == "key_signature":
                    key_by_tick.setdefault(abs_tick, str(msg.key))
                continue

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
                    if active_pedal[ch] is None:
                        active_pedal[ch] = (abs_tick, value)
                else:
                    current = active_pedal.get(ch)
                    if current is not None:
                        start_tick, down_value = current
                        end_tick = abs_tick
                        if end_tick > start_tick:
                            raw_pedals.append(
                                _RawPedal(
                                    channel=ch,
                                    start_tick=start_tick,
                                    end_tick=end_tick,
                                    value=int(down_value),
                                )
                            )
                        active_pedal[ch] = None

        # Close out open notes/pedals at end of track.
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
                if end_tick > start_tick:
                    raw_pedals.append(
                        _RawPedal(
                            channel=ch,
                            start_tick=start_tick,
                            end_tick=end_tick,
                            value=int(down_value),
                        )
                    )

    # Ensure a tempo at tick 0 for time conversion.
    if 0 not in tempo_by_tick:
        tempo_by_tick[0] = 120.0

    tempo_points = [TempoPoint(tick=t, bpm=b) for t, b in sorted(tempo_by_tick.items())]
    ts_points = [
        TimeSignaturePoint(tick=t, numerator=n, denominator=d)
        for t, (n, d) in sorted(ts_by_tick.items())
    ]
    key_points = [KeySignaturePoint(tick=t, key=k) for t, k in sorted(key_by_tick.items())]

    # Use the earliest time signature if present, else default 4/4 for bar estimation.
    if ts_points:
        ts0 = ts_points[0]
        beats_per_bar = float(ts0.numerator) * (4.0 / float(ts0.denominator))
    else:
        beats_per_bar = 4.0
        ts_points = [TimeSignaturePoint(tick=0, numerator=4, denominator=4)]

    duration_beats = _ticks_to_beats(end_tick_global, ppq)

    # Integrate tempo map into total seconds.
    total_seconds = 0.0
    tempo_sorted = sorted(tempo_by_tick.items())
    for i, (tick, bpm) in enumerate(tempo_sorted):
        next_tick = tempo_sorted[i + 1][0] if i + 1 < len(tempo_sorted) else end_tick_global
        if next_tick <= tick:
            continue
        seg_beats = _ticks_to_beats(next_tick - tick, ppq)
        total_seconds += _beats_to_seconds(seg_beats, bpm)

    # Instruments present (channels with either program changes or notes).
    channels_with_notes = {n.channel for n in raw_notes}
    channels = sorted(set(channel_program.keys()) | channels_with_notes)
    instruments = [
        ChannelInstrument(
            channel=ch,
            program=channel_program.get(ch, 0),
            name=channel_name.get(ch),
        )
        for ch in channels
    ]

    # Per-channel analyses.
    notes_by_channel: DefaultDict[int, list[_RawNote]] = defaultdict(list)
    for n in raw_notes:
        notes_by_channel[n.channel].append(n)

    pedals_by_channel: DefaultDict[int, list[_RawPedal]] = defaultdict(list)
    for p in raw_pedals:
        pedals_by_channel[p.channel].append(p)

    track_analyses: list[TrackAnalysis] = []
    for ch in channels:
        channel_notes = notes_by_channel.get(ch, [])
        channel_pedals = pedals_by_channel.get(ch, [])

        # Group by onset tick -> chord sizes.
        onset_to_pitches: DefaultDict[int, list[int]] = defaultdict(list)
        for n in channel_notes:
            onset_to_pitches[n.start_tick].append(n.pitch)
        chord_sizes = [len(set(ps)) for ps in onset_to_pitches.values()]

        all_pitches = [n.pitch for n in channel_notes]
        pc_hist = [0] * 12
        for p in all_pitches:
            pc_hist[int(p) % 12] += 1
        estimated_key, key_conf = _estimate_key_from_pitch_classes(pc_hist)

        velocities = [float(n.velocity) for n in channel_notes]
        durations_beats = [
            float(_ticks_to_beats(n.end_tick - n.start_tick, ppq)) for n in channel_notes
        ]

        # Note density per bar (rough): chord-onsets per bar * mean chord size.
        bar_count = duration_beats / beats_per_bar if beats_per_bar > 0 else 0.0
        note_density = (len(channel_notes) / bar_count) if bar_count > 0 else None

        # Pedal coverage: union of pedal-down windows / total duration (beats).
        pedal_ticks_covered = 0
        if channel_pedals:
            spans = sorted([(p.start_tick, p.end_tick) for p in channel_pedals], key=lambda x: x[0])
            merged: list[tuple[int, int]] = []
            for s, e in spans:
                if not merged or s > merged[-1][1]:
                    merged.append((s, e))
                else:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            pedal_ticks_covered = sum(max(0, e - s) for s, e in merged)
        pedal_ratio = (
            float(pedal_ticks_covered / end_tick_global) if end_tick_global > 0 else None
        )

        # Simple melody proxy: take highest pitch per onset, sorted by onset, then intervals.
        melodic_intervals: Counter[int] = Counter()
        if onset_to_pitches:
            onsets = sorted(onset_to_pitches.items(), key=lambda x: x[0])
            melody = [max(ps) for _, ps in onsets if ps]
            for a, b in zip(melody, melody[1:]):
                melodic_intervals[int(b) - int(a)] += 1
        melodic_interval_hist = {
            str(k): int(v) for k, v in melodic_intervals.most_common(12)
        }

        top_pitches = [p for p, _ in Counter(all_pitches).most_common(12)]
        pitch_min = min(all_pitches) if all_pitches else None
        pitch_max = max(all_pitches) if all_pitches else None

        track_analyses.append(
            TrackAnalysis(
                channel=ch,
                name=channel_name.get(ch, f"Channel {ch}"),
                program=channel_program.get(ch, 0),
                note_count=len(channel_notes),
                chord_onset_count=len(onset_to_pitches),
                chord_size=Distribution(
                    min=float(min(chord_sizes)) if chord_sizes else None,
                    p25=_safe_quantile([float(x) for x in chord_sizes], 0.25) if chord_sizes else None,
                    median=_safe_median([float(x) for x in chord_sizes]) if chord_sizes else None,
                    mean=_safe_mean([float(x) for x in chord_sizes]) if chord_sizes else None,
                    p75=_safe_quantile([float(x) for x in chord_sizes], 0.75) if chord_sizes else None,
                    max=float(max(chord_sizes)) if chord_sizes else None,
                ),
                pitch_min=pitch_min,
                pitch_max=pitch_max,
                top_pitches=top_pitches,
                pitch_class_histogram=pc_hist,
                estimated_key=None if estimated_key == "unknown" else estimated_key,
                estimated_key_confidence=None if estimated_key == "unknown" else float(key_conf),
                velocity=Distribution(
                    min=float(min(velocities)) if velocities else None,
                    p25=_safe_quantile(velocities, 0.25),
                    median=_safe_median(velocities),
                    mean=_safe_mean(velocities),
                    p75=_safe_quantile(velocities, 0.75),
                    max=float(max(velocities)) if velocities else None,
                ),
                duration_beats=Distribution(
                    min=float(min(durations_beats)) if durations_beats else None,
                    p25=_safe_quantile(durations_beats, 0.25),
                    median=_safe_median(durations_beats),
                    mean=_safe_mean(durations_beats),
                    p75=_safe_quantile(durations_beats, 0.75),
                    max=float(max(durations_beats)) if durations_beats else None,
                ),
                note_density_per_bar=float(note_density) if note_density is not None else None,
                pedal_coverage_ratio=pedal_ratio,
                melodic_interval_histogram=melodic_interval_hist,
            )
        )

    # Global summary strings (for prompt-building UIs).
    bpm0 = tempo_points[0].bpm if tempo_points else 120.0
    tempo_note = (
        f"{bpm0:.1f} bpm (with {max(0, len(tempo_points) - 1)} tempo change(s))"
        if tempo_points
        else "unknown"
    )
    ts_note = (
        f"{ts_points[0].numerator}/{ts_points[0].denominator}" if ts_points else "unknown"
    )
    key_note = key_points[0].key if key_points else "unknown"
    est_bars = duration_beats / beats_per_bar if beats_per_bar > 0 else 0.0
    summary = {
        "tempo": tempo_note,
        "time_signature": ts_note,
        "key_signature": key_note,
        "length": f"{duration_beats:.1f} beats (~{est_bars:.1f} bars, ~{total_seconds:.1f}s)",
        "tracks": f"{len(track_analyses)} channel track(s)",
    }

    return MidiAnalysis(
        source_path=str(path),
        ppq=ppq,
        duration_ticks=end_tick_global,
        duration_beats=float(duration_beats),
        duration_seconds=float(total_seconds),
        estimated_bar_count=float(est_bars),
        tempo=tempo_points,
        time_signature=ts_points,
        key_signature=key_points,
        instruments=instruments,
        tracks=track_analyses,
        summary=summary,
    )


def analysis_prompt_template(analysis: MidiAnalysis, instructions: str | None = None) -> str:
    """
    Produce a ready-to-paste prompt to generate a NEW composition inspired by the analysis.
    """
    requested = (instructions or "").strip() or "<describe what you want to compose>"

    ts0 = analysis.time_signature[0] if analysis.time_signature else None
    tempo0 = analysis.tempo[0] if analysis.tempo else None
    key0 = analysis.key_signature[0] if analysis.key_signature else None

    # Provide a conservative “target length” in beats, rounded to whole bars if possible.
    beats_per_bar = 4.0
    if ts0 is not None:
        beats_per_bar = float(ts0.numerator) * (4.0 / float(ts0.denominator))
    bars = analysis.estimated_bar_count
    target_bars = int(max(4, round(bars))) if bars > 0 else 32
    target_beats = float(target_bars) * beats_per_bar

    instrument_lines = []
    for inst in analysis.instruments:
        name = f" ({inst.name})" if inst.name else ""
        instrument_lines.append(f"- ch{inst.channel}: program {inst.program}{name}")
    instruments_block = "\n".join(instrument_lines) if instrument_lines else "- (none detected)"

    # Use the first track as “primary” for texture hints.
    primary = analysis.tracks[0] if analysis.tracks else None
    texture_lines: list[str] = []
    if primary is not None:
        if primary.pitch_min is not None and primary.pitch_max is not None:
            texture_lines.append(f"- register: {primary.pitch_min}..{primary.pitch_max} (MIDI)")
        if primary.chord_size.median is not None:
            texture_lines.append(f"- typical chord size (median): {primary.chord_size.median:.1f} notes")
        if primary.note_density_per_bar is not None:
            texture_lines.append(f"- note density: ~{primary.note_density_per_bar:.1f} notes/bar")
        if primary.pedal_coverage_ratio is not None:
            texture_lines.append(
                f"- sustain pedal coverage: ~{primary.pedal_coverage_ratio*100:.0f}%"
            )
        if primary.estimated_key is not None:
            texture_lines.append(
                f"- pitch-class key estimate: {primary.estimated_key} (conf ~{(primary.estimated_key_confidence or 0.0):.2f})"
            )

    texture_block = "\n".join(texture_lines) if texture_lines else "- (insufficient note data)"

    return (
        "SYSTEM:\n"
        "You are an expert music composition generator. Output MUST be valid JSON only.\n"
        "Hard requirements:\n"
        "- Output ONLY a single JSON object. No markdown. No explanations.\n"
        "- The JSON must validate against the Pianist composition schema (note/pedal/tempo/section events).\n"
        "- Keep timing continuous (avoid long silences). Use musical phrasing and coherent form.\n"
        "\n"
        "USER:\n"
        "Compose a NEW piece inspired by the following reference MIDI analysis.\n"
        "Use it as a style/constraint guide, not something to copy note-for-note.\n"
        "\n"
        "REFERENCE ANALYSIS (high-level):\n"
        f"- tempo: {(tempo0.bpm if tempo0 else 120.0):.1f} bpm\n"
        f"- time signature: {(f'{ts0.numerator}/{ts0.denominator}' if ts0 else '4/4')}\n"
        f"- key signature (if present): {(key0.key if key0 else 'unknown')}\n"
        f"- target length: ~{target_bars} bars (~{target_beats:.1f} beats)\n"
        "\n"
        "INSTRUMENTATION (channels/programs):\n"
        f"{instruments_block}\n"
        "\n"
        "TEXTURE + PERFORMANCE HINTS (from notes/pedal):\n"
        f"{texture_block}\n"
        "\n"
        "REQUESTED COMPOSITION:\n"
        f"{requested}\n"
    )


def _pc_name(pc: int) -> str:
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    return names[int(pc) % 12]


def _key_candidates_from_pitch_classes(
    pc_counts: list[int], *, top_n: int = 5
) -> list[dict[str, Any]]:
    """
    Return top-N K-S style key candidates with raw correlation scores.

    Adds a loose `confidence` field to the best candidate based on score gap.
    """
    # Classic K-S profiles (normalized-ish) for major/minor.
    major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

    def corr(a: list[float], b: list[float]) -> float:
        ma = sum(a) / len(a)
        mb = sum(b) / len(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        da = math.sqrt(sum((x - ma) ** 2 for x in a))
        db = math.sqrt(sum((y - mb) ** 2 for y in b))
        if da == 0 or db == 0:
            return 0.0
        return num / (da * db)

    pcs = [float(x) for x in pc_counts]
    if sum(pcs) <= 0:
        return []

    scored: list[tuple[str, float]] = []
    for root in range(12):
        maj = [major_profile[(i - root) % 12] for i in range(12)]
        minr = [minor_profile[(i - root) % 12] for i in range(12)]
        scored.append((_format_key(root, "major"), corr(pcs, maj)))
        scored.append((_format_key(root, "minor"), corr(pcs, minr)))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[: max(1, int(top_n))]
    best = top[0][1]
    second = top[1][1] if len(top) > 1 else (best - 0.001)
    confidence = max(0.0, min(1.0, (best - second) / 0.25))

    out: list[dict[str, Any]] = [{"key": k, "score": float(s)} for k, s in top]
    out[0]["confidence"] = float(confidence)
    return out


def build_analysis_packet(path: str | Path, *, window_beats: float | None = None) -> dict[str, Any]:
    """
    Build a compact, LLM-friendly analysis packet for a MIDI file.

    Design goals:
    - Deterministic output
    - Evidence-first (windowed features + segmentation candidates)
    - Avoid dumping raw note lists
    """
    raw = _parse_midi_raw(path)
    ppq = raw.ppq
    duration_beats = _ticks_to_beats(raw.end_tick_global, ppq)

    tempo_by_tick = dict(raw.tempo_by_tick)
    if 0 not in tempo_by_tick:
        tempo_by_tick[0] = 120.0
    tempo_points = sorted(tempo_by_tick.items(), key=lambda x: x[0])
    ts_points = sorted(raw.ts_by_tick.items(), key=lambda x: x[0])

    if ts_points:
        n0, d0 = ts_points[0][1]
        beats_per_bar = float(n0) * (4.0 / float(d0))
    else:
        beats_per_bar = 4.0

    win = float(window_beats) if window_beats is not None else float(beats_per_bar)
    if win <= 0:
        win = float(beats_per_bar)

    # Integrate tempo map for seconds.
    total_seconds = 0.0
    for i, (tick, bpm) in enumerate(tempo_points):
        next_tick = tempo_points[i + 1][0] if i + 1 < len(tempo_points) else raw.end_tick_global
        if next_tick <= tick:
            continue
        seg_beats = _ticks_to_beats(next_tick - tick, ppq)
        total_seconds += _beats_to_seconds(seg_beats, bpm)

    # Track summary by channel.
    notes_by_channel: DefaultDict[int, list[_RawNote]] = defaultdict(list)
    for n in raw.raw_notes:
        notes_by_channel[n.channel].append(n)

    channels = sorted(set(notes_by_channel.keys()) | set(raw.channel_program.keys()))
    track_summary: list[dict[str, Any]] = []
    for idx, ch in enumerate(channels):
        notes = notes_by_channel.get(ch, [])
        pitches = [n.pitch for n in notes]
        track_summary.append(
            {
                "track_index": idx,
                "name": raw.channel_name.get(ch, f"Channel {ch}"),
                "channels": [ch],
                "programs": [raw.channel_program.get(ch, 0)],
                "note_count": len(notes),
                "pitch_range": {
                    "min_midi": int(min(pitches)) if pitches else None,
                    "max_midi": int(max(pitches)) if pitches else None,
                },
            }
        )

    # Global pitch-class histogram (all channels).
    global_pc_hist = [0] * 12
    for n in raw.raw_notes:
        global_pc_hist[int(n.pitch) % 12] += 1
    total_pc = sum(global_pc_hist)
    pc_hist_weighted = (
        [{"pc": _pc_name(i), "weight": float(c / total_pc)} for i, c in enumerate(global_pc_hist)]
        if total_pc > 0
        else []
    )

    key_candidates = _key_candidates_from_pitch_classes(global_pc_hist, top_n=5)

    # Texture summaries.
    mean_notes_per_beat = (len(raw.raw_notes) / duration_beats) if duration_beats > 0 else 0.0
    pitches_all = [n.pitch for n in raw.raw_notes]

    onset_to_pitches: DefaultDict[int, set[int]] = defaultdict(set)
    for n in raw.raw_notes:
        onset_to_pitches[n.start_tick].add(int(n.pitch))
    chord_onsets = list(onset_to_pitches.values())
    polyphony_ratio = (
        (sum(1 for s in chord_onsets if len(s) > 1) / len(chord_onsets)) if chord_onsets else 0.0
    )

    bpm_values = [b for _, b in tempo_points]
    tempo_summary = {
        "bpm_min": float(min(bpm_values)) if bpm_values else None,
        "bpm_max": float(max(bpm_values)) if bpm_values else None,
        "has_rubato": bool(len(tempo_points) > 1),
    }

    # Windows.
    def tick_to_beat(t: int) -> float:
        return _ticks_to_beats(int(t), ppq)

    notes_sorted = sorted(raw.raw_notes, key=lambda n: (n.start_tick, n.pitch))
    features_windows: list[dict[str, Any]] = []

    window_count = int(math.ceil(duration_beats / win)) if win > 0 else 0
    for w in range(max(1, window_count)):
        start_beat = float(w * win)
        end_beat = float(min(duration_beats, start_beat + win))
        window_notes = [n for n in notes_sorted if start_beat <= tick_to_beat(n.start_tick) < end_beat]

        pc_hist = [0] * 12
        for n in window_notes:
            pc_hist[int(n.pitch) % 12] += 1
        total_w = sum(pc_hist)
        pc_weighted = (
            [{"pc": _pc_name(i), "weight": float(c / total_w)} for i, c in enumerate(pc_hist)]
            if total_w > 0
            else []
        )

        key_cands = _key_candidates_from_pitch_classes(pc_hist, top_n=3)
        window_pitches = [n.pitch for n in window_notes]

        onset_map: DefaultDict[int, set[int]] = defaultdict(set)
        for n in window_notes:
            onset_map[n.start_tick].add(int(n.pitch))
        onset_sets = list(onset_map.values())
        window_poly_ratio = (
            (sum(1 for s in onset_sets if len(s) > 1) / len(onset_sets)) if onset_sets else 0.0
        )

        notes_per_beat = (len(window_notes) / (end_beat - start_beat)) if end_beat > start_beat else 0.0

        features_windows.append(
            {
                "start_beat": start_beat,
                "end_beat": end_beat,
                "pitch_class_histogram": pc_weighted,
                "key_candidates": key_cands,
                "density": {"notes_per_beat": float(notes_per_beat), "polyphony_ratio": float(window_poly_ratio)},
                "register": {
                    "low_midi_p10": int(_safe_quantile([float(p) for p in window_pitches], 0.10)) if window_pitches else None,
                    "high_midi_p90": int(_safe_quantile([float(p) for p in window_pitches], 0.90)) if window_pitches else None,
                },
            }
        )

    # Segmentation candidates (simple novelty based on pitch-class distribution + density delta).
    segmentation_candidates: list[dict[str, Any]] = []
    if len(features_windows) >= 2:
        pc_names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

        def vec(win_entry: dict[str, Any]) -> list[float]:
            v = [0.0] * 12
            for item in win_entry.get("pitch_class_histogram", []) or []:
                pc = item.get("pc")
                if pc in pc_names:
                    v[pc_names.index(pc)] = float(item.get("weight") or 0.0)
            return v

        def l2(a: list[float], b: list[float]) -> float:
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        dist_values: list[float] = []
        density_deltas: list[float] = []
        for prev, cur in zip(features_windows, features_windows[1:]):
            dist_values.append(l2(vec(prev), vec(cur)))
            d0 = float(prev["density"]["notes_per_beat"])
            d1 = float(cur["density"]["notes_per_beat"])
            density_deltas.append(abs(d1 - d0))

        dist_max = max(dist_values) if dist_values else 1.0
        dens_max = max(density_deltas) if density_deltas else 1.0

        for i in range(1, len(features_windows)):
            beat = float(features_windows[i]["start_beat"])
            dist = dist_values[i - 1] if (i - 1) < len(dist_values) else 0.0
            dens = density_deltas[i - 1] if (i - 1) < len(density_deltas) else 0.0
            strength = 0.6 * (dist / dist_max if dist_max > 0 else 0.0) + 0.4 * (dens / dens_max if dens_max > 0 else 0.0)

            reasons: list[str] = []
            if dist_max > 0 and (dist / dist_max) > 0.6:
                reasons.append("tonal_centroid_shift")
            if dens_max > 0 and (dens / dens_max) > 0.6:
                reasons.append("density_change")

            bar_aligned = (
                abs((beat / beats_per_bar) - round(beat / beats_per_bar)) < 0.05 if beats_per_bar > 0 else False
            )

            segmentation_candidates.append(
                {
                    "beat": beat,
                    "strength": float(max(0.0, min(1.0, strength))),
                    "reasons": reasons or ["window_change"],
                    "bar_aligned": bool(bar_aligned),
                }
            )

        segmentation_candidates.sort(key=lambda x: x["strength"], reverse=True)
        segmentation_candidates = segmentation_candidates[:12]

    # Excerpt: first 8 beats.
    excerpt_end = float(min(duration_beats, 8.0))
    excerpt_notes = [n for n in raw.raw_notes if tick_to_beat(n.start_tick) < excerpt_end]
    top_pitches = [p for p, _ in Counter([n.pitch for n in excerpt_notes]).most_common(8)]

    onset_map2: DefaultDict[int, list[int]] = defaultdict(list)
    for n in excerpt_notes:
        onset_map2[n.start_tick].append(int(n.pitch))
    melody = [max(ps) for _, ps in sorted(onset_map2.items(), key=lambda x: x[0]) if ps]
    interval_counts: Counter[int] = Counter()
    for a, b in zip(melody, melody[1:]):
        interval_counts[int(b) - int(a)] += 1
    motif_intervals = [int(k) for k, _ in interval_counts.most_common(6)]

    payload: dict[str, Any] = {
        "schema_version": "analysis-packet/v1",
        "source": {
            "filename": raw.path.name,
            "format": "midi",
            "ppq": int(ppq),
            "duration_seconds": float(total_seconds),
            "total_beats_estimate": float(duration_beats),
        },
        "timeline": {
            "time_signature_events": [
                {"beat": float(_ticks_to_beats(t, ppq)), "numerator": int(n), "denominator": int(d)}
                for t, (n, d) in ts_points
            ]
            or [{"beat": 0.0, "numerator": 4, "denominator": 4}],
            "tempo_events": [{"beat": float(_ticks_to_beats(t, ppq)), "bpm": float(b)} for t, b in tempo_points],
            "beat_grid_hint": {"preferred_window_beats": float(win), "bar_beats": float(beats_per_bar)},
        },
        "track_summary": track_summary,
        "features_global": {
            "pitch_class_histogram": pc_hist_weighted,
            "key_candidates": key_candidates,
            "tempo_summary": tempo_summary,
            "texture_summary": {
                "mean_notes_per_beat": float(mean_notes_per_beat),
                "polyphony_ratio": float(polyphony_ratio),
                "register_center_midi": float(_safe_mean([float(p) for p in pitches_all]) or 0.0),
                "lh_rh_separation_confidence": 0.0,
            },
        },
        "features_windows": features_windows,
        "harmony_windows": [],
        "segmentation_candidates": segmentation_candidates,
        "cadence_candidates": [],
        "excerpts": [
            {
                "start_beat": 0.0,
                "end_beat": excerpt_end,
                "summary": {
                    "top_pitches_midi": [int(x) for x in top_pitches],
                    "motif_hint_intervals": motif_intervals,
                },
            }
        ],
    }
    return payload


def analysis_packet_to_pretty_json(packet: dict[str, Any]) -> str:
    return json.dumps(packet, indent=2, sort_keys=True) + "\n"


def _mock_metadata_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    total_beats = float(packet.get("source", {}).get("total_beats_estimate") or 0.0)
    tempo_events = packet.get("timeline", {}).get("tempo_events") or []
    ts_events = packet.get("timeline", {}).get("time_signature_events") or []

    bpm0 = float((tempo_events[0].get("bpm") if tempo_events else 120.0) or 120.0)
    ts0 = ts_events[0] if ts_events else {"numerator": 4, "denominator": 4}

    key_cands = packet.get("features_global", {}).get("key_candidates") or []
    primary_key = (key_cands[0].get("key") if key_cands else "unknown") or "unknown"
    key_conf = float((key_cands[0].get("confidence") if key_cands else 0.0) or 0.0)

    mood_tags: list[dict[str, Any]] = []
    if isinstance(primary_key, str) and "minor" in primary_key.lower():
        mood_tags.append({"tag": "melancholic", "confidence": 0.55})
    mood_tags.append({"tag": "lyrical", "confidence": 0.45})

    segs = packet.get("segmentation_candidates") or []
    boundaries = sorted(
        {
            float(s["beat"])
            for s in segs
            if float(s.get("strength") or 0.0) >= 0.75 and float(s.get("beat") or 0.0) > 0.0
        }
    )
    boundaries = boundaries[:4]

    cuts = [0.0] + boundaries + ([total_beats] if total_beats > 0 else [])
    cuts = sorted(set(cuts))
    if len(cuts) < 2:
        cuts = [0.0, total_beats]

    sections: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    for i in range(len(cuts) - 1):
        s = float(cuts[i])
        e = float(cuts[i + 1])
        sid = chr(ord("A") + i) if i < 26 else f"S{i+1}"
        label = f"{sid}: section"
        sections.append(
            {
                "id": sid,
                "start_beat": s,
                "end_beat": e,
                "label": label,
                "function": "A" if i == 0 else "B",
                "key_center": {"key": primary_key, "confidence": float(max(0.2, key_conf))},
                "energy": {"value_0_to_1": float(min(1.0, 0.35 + 0.12 * i)), "confidence": 0.4},
                "texture_tags": [],
                "motifs": [],
                "evidence": {"used_segmentation_candidates": boundaries, "notes": "mock metadata (deterministic)"},
                "confidence": 0.4,
            }
        )
        markers.append({"type": "section", "start": s, "label": label})

    warnings: list[dict[str, Any]] = []
    if key_conf < 0.35:
        warnings.append(
            {
                "type": "ambiguity",
                "field": "global.key",
                "message": "Low confidence key estimate; treat as ambiguous.",
            }
        )

    return {
        "schema_version": "metadata-suggestion/v1",
        "global": {
            "title_suggestion": packet.get("source", {}).get("filename") or "Untitled",
            "primary_instrument": "piano",
            "tempo": {
                "type": "steady" if len(tempo_events) <= 1 else "variable",
                "bpm_representative": bpm0,
                "notes": "",
            },
            "time_signature": {
                "numerator": int(ts0.get("numerator") or 4),
                "denominator": int(ts0.get("denominator") or 4),
            },
            "key": {"primary": primary_key, "secondary": [], "confidence": key_conf, "notes": ""},
            "tags": {"mood": mood_tags, "genre_style": []},
        },
        "sections": sections,
        "seed_annotations": {
            "section_markers": markers,
            "note_event_sectioning": {
                "mode": "by_range",
                "ranges": [{"start_beat": cuts[0], "end_beat": cuts[-1], "section": "A"}],
            },
        },
        "prompt_hints": {
            "one_sentence_summary": f"Piece in {primary_key} at ~{bpm0:.0f} BPM with {len(sections)} section(s).",
            "iteration_suggestions": [],
        },
        "warnings": warnings,
    }


def _openai_chat_completions(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.0,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": float(temperature)}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"OpenAI-compatible API error: HTTP {e.code}: {err}") from e
    data = json.loads(raw_text)
    try:
        return str(data["choices"][0]["message"]["content"])
    except Exception as e:
        raise RuntimeError("Unexpected OpenAI-compatible response shape.") from e


def suggest_metadata_from_analysis_packet(
    packet: dict[str, Any],
    *,
    llm: Literal["mock", "openai"],
    model: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """
    Turn an analysis packet into a metadata suggestion JSON object.

    `llm="mock"` is deterministic and requires no external credentials.
    `llm="openai"` uses an OpenAI-compatible Chat Completions API.
    """
    if llm == "mock":
        return _mock_metadata_from_packet(packet)

    if llm == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for --llm openai.")
        model2 = (model or os.environ.get("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"
        base = (base_url or os.environ.get("OPENAI_BASE_URL") or "").strip() or "https://api.openai.com/v1"

        schema_hint = (
            "Return ONLY a single JSON object that matches this schema (metadata-suggestion/v1):\n"
            "- schema_version: \"metadata-suggestion/v1\"\n"
            "- global: { title_suggestion, primary_instrument, tempo{type,bpm_representative,notes}, "
            "time_signature{numerator,denominator}, key{primary,secondary[],confidence,notes}, "
            "tags{mood[{tag,confidence}], genre_style[{tag,confidence}] } }\n"
            "- sections: [ { id, start_beat, end_beat, label, function, key_center{key,confidence}, "
            "energy{value_0_to_1,confidence}, texture_tags[], motifs[{id,description,confidence}], "
            "evidence{used_segmentation_candidates[],notes}, confidence } ]\n"
            "- seed_annotations: { section_markers: [ {type:\"section\", start, label} ], "
            "note_event_sectioning: { mode:\"by_range\", ranges:[{start_beat,end_beat,section}] } }\n"
            "- prompt_hints: { one_sentence_summary, iteration_suggestions[] }\n"
            "- warnings: [ {type, field, message} ]\n"
            "Rules:\n"
            "- Do not invent beats outside packet.source.total_beats_estimate.\n"
            "- Prefer packet.segmentation_candidates for section boundaries.\n"
            "- If uncertain, say so in warnings and lower confidence.\n"
        )

        messages = [
            {
                "role": "system",
                "content": "You label MIDI analysis into metadata JSON. Output JSON only.",
            },
            {
                "role": "user",
                "content": schema_hint
                + "\n\nANALYSIS PACKET JSON:\n"
                + json.dumps(packet, ensure_ascii=False),
            },
        ]
        text = _openai_chat_completions(
            base_url=base, api_key=api_key, model=model2, messages=messages, temperature=0.0
        )
        meta = parse_json_dict_from_text(text)
        if meta.get("schema_version") != "metadata-suggestion/v1":
            raise ValueError("LLM output did not set schema_version to metadata-suggestion/v1.")
        return meta

    raise ValueError(f"Unsupported llm provider: {llm}")

