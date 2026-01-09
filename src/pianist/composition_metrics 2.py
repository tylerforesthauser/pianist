"""
Advanced composition metrics analysis for extracting patterns from professional MIDI files.

This module analyzes MIDI files to extract statistical patterns that inform prompt engineering:
- Motif frequency and repetition patterns
- Section transition lengths
- Rhythmic and melodic variation patterns
- Gap analysis between sections
- Phrase structure patterns
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import mido
from pydantic import BaseModel, Field


@dataclass
class _NoteEvent:
    """Simplified note event for pattern analysis."""

    start_beats: float
    duration_beats: float
    pitch: int
    velocity: int


@dataclass
class _Section:
    """Detected section in a composition."""

    start_beats: float
    end_beats: float
    label: str | None = None


class MotifPattern(BaseModel):
    """A detected melodic/rhythmic motif."""

    pitches: list[int]  # Relative intervals or absolute pitches
    rhythm: list[float]  # Durations in beats
    occurrences: list[float]  # Beat positions where motif appears
    variations: list[str]  # Types of variations (transposition, inversion, etc.)


class GapAnalysis(BaseModel):
    """Analysis of gaps between musical events."""

    max_gap_beats: float
    mean_gap_beats: float
    median_gap_beats: float
    gaps_between_sections: list[float]  # Gaps at section boundaries
    total_silence_ratio: float  # Ratio of silence to total duration


class VariationMetrics(BaseModel):
    """Metrics for rhythmic and melodic variation."""

    rhythmic_entropy: float  # Measure of rhythmic diversity
    melodic_entropy: float  # Measure of melodic diversity
    phrase_length_variance: float  # Variance in phrase lengths
    rhythmic_density_variance: float  # Variance in notes per beat
    melodic_contour_variance: float  # Variance in melodic direction


class CompositionMetrics(BaseModel):
    """Comprehensive metrics for a composition."""

    source_path: str
    duration_beats: float

    # Motif analysis
    primary_motifs: list[MotifPattern] = Field(default_factory=list)
    motif_frequency_per_64_beats: float | None = None
    motif_repetition_interval_beats: Distribution | None = None

    # Gap and continuity
    gap_analysis: GapAnalysis | None = None

    # Section transitions
    section_transitions: list[float] = Field(default_factory=list)  # Transition lengths in beats
    mean_transition_length: float | None = None
    median_transition_length: float | None = None

    # Variation
    variation_metrics: VariationMetrics | None = None

    # Phrase structure
    phrase_lengths: list[float] = Field(default_factory=list)
    phrase_length_distribution: Distribution | None = None

    # Section coherence
    sections: list[_Section] = Field(default_factory=list)
    section_count: int = 0


class Distribution(BaseModel):
    """Statistical distribution."""

    min: float | None = None
    p25: float | None = None
    median: float | None = None
    mean: float | None = None
    p75: float | None = None
    max: float | None = None


def _calculate_distribution(values: list[float]) -> Distribution:
    """Calculate distribution statistics."""
    if not values:
        return Distribution()

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return Distribution(
        min=float(sorted_vals[0]),
        p25=float(sorted_vals[n // 4]) if n >= 4 else None,
        median=float(sorted_vals[n // 2]) if n >= 2 else None,
        mean=float(sum(values) / n),
        p75=float(sorted_vals[3 * n // 4]) if n >= 4 else None,
        max=float(sorted_vals[-1]),
    )


def _detect_phrases(
    notes: list[_NoteEvent], beats_per_bar: float = 4.0
) -> list[tuple[float, float]]:
    """
    Detect phrase boundaries based on note density and rhythmic patterns.

    Returns list of (start_beats, end_beats) for each phrase.
    """
    if not notes:
        return []

    # Group notes by measure (rough approximation)
    notes_by_measure: defaultdict[int, list[_NoteEvent]] = defaultdict(list)
    for note in notes:
        measure = int(note.start_beats / beats_per_bar)
        notes_by_measure[measure].append(note)

    # Detect phrase boundaries: look for cadence-like patterns (longer notes, lower density)
    phrases: list[tuple[float, float]] = []
    current_phrase_start = notes[0].start_beats

    for i in range(len(notes) - 1):
        current = notes[i]
        next_note = notes[i + 1]

        gap = next_note.start_beats - (current.start_beats + current.duration_beats)

        # Potential phrase boundary indicators:
        # 1. Longer gap (but not too long - that's a section break)
        # 2. Note density drop
        # 3. Longer note duration (cadential)

        if gap > 1.0 and gap < 4.0:  # Between phrases, not sections
            # Check if this looks like a phrase ending
            if current.duration_beats >= 1.0:  # Longer note suggests cadence
                phrases.append((current_phrase_start, current.start_beats + current.duration_beats))
                current_phrase_start = next_note.start_beats

    # Add final phrase
    if notes:
        phrases.append((current_phrase_start, notes[-1].start_beats + notes[-1].duration_beats))

    return (
        phrases
        if phrases
        else [(notes[0].start_beats, notes[-1].start_beats + notes[-1].duration_beats)]
    )


def _detect_motifs(
    notes: list[_NoteEvent], min_length: int = 3, max_length: int = 8
) -> list[MotifPattern]:
    """
    Detect recurring melodic/rhythmic patterns (motifs).

    Uses a simple sliding window approach to find repeated patterns.
    """
    if len(notes) < min_length * 2:
        return []

    # Extract melodic intervals and rhythms, tracking note indices
    patterns: list[tuple[list[int], list[float], int]] = []  # (intervals, rhythms, note_start_idx)

    for window_size in range(min_length, min(max_length + 1, len(notes) // 2)):
        for i in range(len(notes) - window_size + 1):
            window = notes[i : i + window_size]

            # Extract pattern: intervals and rhythms
            intervals = [window[j + 1].pitch - window[j].pitch for j in range(len(window) - 1)]
            rhythms = [n.duration_beats for n in window]

            patterns.append((intervals, rhythms, i))

    # Find repeated patterns
    pattern_counts: Counter[tuple[tuple[int, ...], tuple[float, ...]]] = Counter()
    pattern_positions: defaultdict[tuple[tuple[int, ...], tuple[float, ...]], list[float]] = (
        defaultdict(list)
    )
    pattern_note_indices: defaultdict[tuple[tuple[int, ...], tuple[float, ...]], list[int]] = (
        defaultdict(list)
    )

    for intervals, rhythms, note_idx in patterns:
        # Normalize rhythms to relative durations (to catch similar patterns at different tempos)
        if rhythms:
            min_rhythm = min(rhythms)
            normalized_rhythms = tuple(round(r / min_rhythm, 2) for r in rhythms)
        else:
            normalized_rhythms = ()

        pattern_key = (tuple(intervals), normalized_rhythms)
        pattern_counts[pattern_key] += 1
        pattern_positions[pattern_key].append(notes[note_idx].start_beats)
        pattern_note_indices[pattern_key].append(note_idx)

    # Extract motifs that appear at least 3 times
    motifs: list[MotifPattern] = []
    for (intervals, normalized_rhythms), count in pattern_counts.items():
        if count >= 3:
            # Get the first occurrence's note index
            first_note_idx = pattern_note_indices[(intervals, normalized_rhythms)][0]

            # Find the original pattern with matching intervals and the correct note index
            # We need to find which window_size was used for this pattern
            original_rhythms = None
            window_size = 0

            for pat_intervals, pat_rhythms, pat_idx in patterns:
                if pat_idx == first_note_idx:
                    # Check if this pattern matches (intervals should match)
                    if tuple(pat_intervals) == intervals:
                        original_rhythms = pat_rhythms
                        window_size = len(pat_rhythms)
                        break

            if original_rhythms is None or window_size == 0:
                continue  # Skip if we can't find the original pattern

            # Extract pitches for the first occurrence, ensuring we don't go out of bounds
            if first_note_idx + window_size <= len(notes):
                first_pitches = [notes[first_note_idx + i].pitch for i in range(window_size)]
            else:
                # Fallback: use available notes
                available = len(notes) - first_note_idx
                first_pitches = [notes[first_note_idx + i].pitch for i in range(available)]
                # Pad with last pitch if needed (shouldn't happen, but safety check)
                while len(first_pitches) < window_size and len(first_pitches) > 0:
                    first_pitches.append(first_pitches[-1])

            if len(first_pitches) == window_size:
                motifs.append(
                    MotifPattern(
                        pitches=first_pitches,
                        rhythm=original_rhythms,
                        occurrences=pattern_positions[(intervals, normalized_rhythms)],
                        variations=[],  # TODO: Detect variation types
                    )
                )

    # Sort by frequency
    motifs.sort(key=lambda m: len(m.occurrences), reverse=True)

    return motifs[:5]  # Return top 5 motifs


def _analyze_gaps(notes: list[_NoteEvent], sections: list[_Section]) -> GapAnalysis:
    """Analyze gaps between notes and sections."""
    if not notes:
        return GapAnalysis(
            max_gap_beats=0.0,
            mean_gap_beats=0.0,
            median_gap_beats=0.0,
            gaps_between_sections=[],
            total_silence_ratio=0.0,
        )

    # Calculate gaps between consecutive notes
    gaps: list[float] = []
    total_silence = 0.0

    for i in range(len(notes) - 1):
        current_end = notes[i].start_beats + notes[i].duration_beats
        next_start = notes[i + 1].start_beats
        gap = max(0.0, next_start - current_end)
        gaps.append(gap)
        total_silence += gap

    # Calculate gaps at section boundaries
    section_gaps: list[float] = []
    for i in range(len(sections) - 1):
        current_section = sections[i]
        next_section = sections[i + 1]

        # Find last note in current section and first note in next section
        last_note_in_section = None
        first_note_in_next = None

        for note in notes:
            if current_section.start_beats <= note.start_beats < current_section.end_beats:
                if (
                    last_note_in_section is None
                    or note.start_beats > last_note_in_section.start_beats
                ):
                    last_note_in_section = note

        for note in notes:
            if next_section.start_beats <= note.start_beats < next_section.end_beats:
                first_note_in_next = note
                break

        if last_note_in_section and first_note_in_next:
            gap = max(
                0.0,
                first_note_in_next.start_beats
                - (last_note_in_section.start_beats + last_note_in_section.duration_beats),
            )
            section_gaps.append(gap)

    total_duration = notes[-1].start_beats + notes[-1].duration_beats - notes[0].start_beats
    silence_ratio = total_silence / total_duration if total_duration > 0 else 0.0

    gap_dist = _calculate_distribution(gaps) if gaps else Distribution()

    return GapAnalysis(
        max_gap_beats=gap_dist.max or 0.0,
        mean_gap_beats=gap_dist.mean or 0.0,
        median_gap_beats=gap_dist.median or 0.0,
        gaps_between_sections=section_gaps,
        total_silence_ratio=silence_ratio,
    )


def _calculate_entropy(values: list[float], bins: int = 10) -> float:
    """Calculate Shannon entropy as a measure of diversity."""
    if not values or len(values) < 2:
        return 0.0

    # Normalize values to [0, 1]
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return 0.0

    normalized = [(v - min_val) / (max_val - min_val) for v in values]

    # Bin the values
    histogram = [0] * bins
    for v in normalized:
        bin_idx = min(int(v * bins), bins - 1)
        histogram[bin_idx] += 1

    # Calculate entropy
    total = sum(histogram)
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in histogram:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


def _analyze_variation(
    notes: list[_NoteEvent], phrases: list[tuple[float, float]]
) -> VariationMetrics:
    """Analyze rhythmic and melodic variation."""
    if not notes:
        return VariationMetrics(
            rhythmic_entropy=0.0,
            melodic_entropy=0.0,
            phrase_length_variance=0.0,
            rhythmic_density_variance=0.0,
            melodic_contour_variance=0.0,
        )

    # Rhythmic entropy: diversity of note durations
    durations = [n.duration_beats for n in notes]
    rhythmic_entropy = _calculate_entropy(durations)

    # Melodic entropy: diversity of pitch intervals
    intervals = []
    for i in range(len(notes) - 1):
        intervals.append(abs(notes[i + 1].pitch - notes[i].pitch))
    melodic_entropy = _calculate_entropy(intervals) if intervals else 0.0

    # Phrase length variance
    phrase_lengths = [end - start for start, end in phrases]
    phrase_variance = (
        float(
            sum((x - sum(phrase_lengths) / len(phrase_lengths)) ** 2 for x in phrase_lengths)
            / len(phrase_lengths)
        )
        if phrase_lengths
        else 0.0
    )

    # Rhythmic density variance (notes per beat)
    beats_covered = notes[-1].start_beats + notes[-1].duration_beats - notes[0].start_beats
    notes_per_beat = len(notes) / beats_covered if beats_covered > 0 else 0.0

    # Melodic contour variance (direction changes)
    directions = []
    for i in range(len(notes) - 1):
        if notes[i + 1].pitch > notes[i].pitch:
            directions.append(1)  # Up
        elif notes[i + 1].pitch < notes[i].pitch:
            directions.append(-1)  # Down
        else:
            directions.append(0)  # Same

    direction_changes = sum(
        1 for i in range(len(directions) - 1) if directions[i] != directions[i + 1]
    )
    contour_variance = direction_changes / len(directions) if directions else 0.0

    return VariationMetrics(
        rhythmic_entropy=rhythmic_entropy,
        melodic_entropy=melodic_entropy,
        phrase_length_variance=phrase_variance,
        rhythmic_density_variance=notes_per_beat,  # Simplified
        melodic_contour_variance=contour_variance,
    )


def analyze_composition_metrics(midi_path: str | Path) -> CompositionMetrics:
    """
    Analyze a MIDI file to extract composition metrics for prompt engineering.

    This function extracts statistical patterns that can inform:
    - How often motifs should appear
    - How long transitions should be
    - How much variation is typical
    - What phrase structures are common
    """
    path = Path(midi_path)
    mid = mido.MidiFile(path)
    ppq = int(mid.ticks_per_beat or 480)

    # Extract notes
    notes: list[_NoteEvent] = []
    tempo_map: dict[int, float] = {0: 120.0}  # tick -> bpm

    for track in mid.tracks:
        abs_tick = 0
        active_notes: dict[
            int, tuple[int, int, int]
        ] = {}  # pitch -> (start_tick, velocity, channel)

        for msg in track:
            abs_tick += int(msg.time)

            if isinstance(msg, mido.MetaMessage):
                if msg.type == "set_tempo":
                    tempo_map[abs_tick] = float(mido.tempo2bpm(msg.tempo))
                continue

            if not isinstance(msg, mido.Message):
                continue

            if msg.type == "note_on" and int(msg.velocity) > 0:
                pitch = int(msg.note)
                active_notes[pitch] = (abs_tick, int(msg.velocity), int(getattr(msg, "channel", 0)))

            elif msg.type == "note_off" or (msg.type == "note_on" and int(msg.velocity) == 0):
                pitch = int(msg.note)
                if pitch in active_notes:
                    start_tick, velocity, _channel = active_notes.pop(pitch)
                    duration_ticks = abs_tick - start_tick

                    if duration_ticks > 0:
                        # Convert to beats
                        start_beats = start_tick / ppq
                        duration_beats = duration_ticks / ppq

                        notes.append(
                            _NoteEvent(
                                start_beats=start_beats,
                                duration_beats=duration_beats,
                                pitch=pitch,
                                velocity=velocity,
                            )
                        )

    if not notes:
        return CompositionMetrics(
            source_path=str(path),
            duration_beats=0.0,
        )

    # Sort notes by start time
    notes.sort(key=lambda n: n.start_beats)

    # Calculate duration
    duration_beats = notes[-1].start_beats + notes[-1].duration_beats - notes[0].start_beats

    # Detect sections (simplified: look for tempo/key changes or long gaps)
    sections: list[_Section] = []
    current_section_start = notes[0].start_beats

    for i in range(len(notes) - 1):
        gap = notes[i + 1].start_beats - (notes[i].start_beats + notes[i].duration_beats)

        # Section break: gap > 4 beats
        if gap > 4.0:
            sections.append(
                _Section(
                    start_beats=current_section_start,
                    end_beats=notes[i].start_beats + notes[i].duration_beats,
                )
            )
            current_section_start = notes[i + 1].start_beats

    # Add final section
    sections.append(
        _Section(
            start_beats=current_section_start,
            end_beats=notes[-1].start_beats + notes[-1].duration_beats,
        )
    )

    # Detect phrases
    beats_per_bar = 4.0  # Default, could be extracted from time signature
    phrases = _detect_phrases(notes, beats_per_bar)
    phrase_lengths = [end - start for start, end in phrases]

    # Detect motifs
    motifs = _detect_motifs(notes)

    # Calculate motif frequency (per 64 beats)
    motif_frequency = None
    if motifs:
        total_occurrences = sum(len(m.occurrences) for m in motifs)
        motif_frequency = (total_occurrences / duration_beats) * 64.0 if duration_beats > 0 else 0.0

    # Calculate motif repetition intervals
    motif_intervals: list[float] = []
    for motif in motifs:
        for i in range(len(motif.occurrences) - 1):
            interval = motif.occurrences[i + 1] - motif.occurrences[i]
            motif_intervals.append(interval)

    motif_interval_dist = _calculate_distribution(motif_intervals) if motif_intervals else None

    # Analyze gaps
    gap_analysis = _analyze_gaps(notes, sections)

    # Analyze section transitions
    transition_lengths: list[float] = []
    for i in range(len(sections) - 1):
        # Find notes near section boundary
        section_end = sections[i].end_beats
        next_section_start = sections[i + 1].start_beats

        # Find last note of current section and first note of next section
        last_note = None
        first_note_next = None

        for note in notes:
            if note.start_beats <= section_end and (
                last_note is None or note.start_beats > last_note.start_beats
            ):
                last_note = note

        for note in notes:
            if note.start_beats >= next_section_start:
                first_note_next = note
                break

        if last_note and first_note_next:
            # Transition length is the gap between sections
            transition_length = max(
                0.0,
                first_note_next.start_beats - (last_note.start_beats + last_note.duration_beats),
            )
            transition_lengths.append(transition_length)

    mean_transition = (
        float(sum(transition_lengths) / len(transition_lengths)) if transition_lengths else None
    )
    median_transition = (
        float(sorted(transition_lengths)[len(transition_lengths) // 2])
        if transition_lengths
        else None
    )

    # Analyze variation
    variation_metrics = _analyze_variation(notes, phrases)

    return CompositionMetrics(
        source_path=str(path),
        duration_beats=duration_beats,
        primary_motifs=motifs,
        motif_frequency_per_64_beats=motif_frequency,
        motif_repetition_interval_beats=motif_interval_dist,
        gap_analysis=gap_analysis,
        section_transitions=transition_lengths,
        mean_transition_length=mean_transition,
        median_transition_length=median_transition,
        variation_metrics=variation_metrics,
        phrase_lengths=phrase_lengths,
        phrase_length_distribution=_calculate_distribution(phrase_lengths)
        if phrase_lengths
        else None,
        sections=sections,
        section_count=len(sections),
    )
