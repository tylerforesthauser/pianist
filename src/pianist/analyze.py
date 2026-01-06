from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict, Literal

import mido
from pydantic import BaseModel, Field


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
    ppq: int = Field(ge=24, le=9600)

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
                if end_tick >= start_tick:
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

