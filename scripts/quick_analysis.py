#!/usr/bin/env python3
"""
Quick standalone analysis script for basic MIDI file statistics.

This is a lightweight script that works without full package installation.
It provides basic metrics (duration, note count, gaps, pitch range) using
only mido and pydantic.

For comprehensive analysis with musical features (motifs, phrases, harmony),
use the main CLI `analyze` command or `analyze_dataset.py` script.

Requires: pip install mido pydantic

Usage:
    python3 scripts/quick_analysis.py <midi_directory> [--output output.json]
"""

import json
import statistics
import sys
from pathlib import Path
from typing import Any

try:
    import mido
    from pydantic import BaseModel
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install: pip install mido pydantic")
    sys.exit(1)


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


def analyze_single_midi(midi_path: Path) -> dict[str, Any]:
    """Quick analysis of a single MIDI file."""
    try:
        mid = mido.MidiFile(midi_path)
        ppq = int(mid.ticks_per_beat or 480)

        # Extract notes
        notes: list[tuple[float, float, int]] = []  # (start_beats, duration_beats, pitch)
        tempo_map: dict[int, float] = {0: 120.0}

        for track in mid.tracks:
            abs_tick = 0
            active_notes: dict[int, tuple[int, int]] = {}  # pitch -> (start_tick, velocity)

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
                    active_notes[pitch] = (abs_tick, int(msg.velocity))

                elif msg.type == "note_off" or (msg.type == "note_on" and int(msg.velocity) == 0):
                    pitch = int(msg.note)
                    if pitch in active_notes:
                        start_tick, _velocity = active_notes.pop(pitch)
                        duration_ticks = abs_tick - start_tick

                        if duration_ticks > 0:
                            start_beats = start_tick / ppq
                            duration_beats = duration_ticks / ppq
                            notes.append((start_beats, duration_beats, pitch))

        if not notes:
            return {"error": "No notes found", "file": str(midi_path)}

        # Sort by start time
        notes.sort(key=lambda n: n[0])

        # Calculate basic metrics
        duration_beats = notes[-1][0] + notes[-1][1] - notes[0][0]

        # Calculate gaps
        gaps: list[float] = []
        for i in range(len(notes) - 1):
            current_end = notes[i][0] + notes[i][1]
            next_start = notes[i + 1][0]
            gap = max(0.0, next_start - current_end)
            gaps.append(gap)

        gap_dist = _calculate_distribution(gaps) if gaps else Distribution()

        # Note density
        note_density = len(notes) / duration_beats if duration_beats > 0 else 0

        # Duration distribution
        durations = [n[1] for n in notes]
        duration_dist = _calculate_distribution(durations)

        # Pitch range
        pitches = [n[2] for n in notes]
        pitch_min = min(pitches) if pitches else None
        pitch_max = max(pitches) if pitches else None

        return {
            "file": midi_path.name,
            "duration_beats": round(duration_beats, 2),
            "note_count": len(notes),
            "note_density_per_beat": round(note_density, 2),
            "gaps": {
                "max": round(gap_dist.max or 0, 2),
                "mean": round(gap_dist.mean or 0, 2),
                "median": round(gap_dist.median or 0, 2),
            },
            "duration": {
                "min": round(duration_dist.min or 0, 2),
                "mean": round(duration_dist.mean or 0, 2),
                "median": round(duration_dist.median or 0, 2),
                "max": round(duration_dist.max or 0, 2),
            },
            "pitch_range": {
                "min": pitch_min,
                "max": pitch_max,
            },
        }
    except Exception as e:
        return {"error": str(e), "file": str(midi_path)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_analysis.py <midi_directory> [--output output.json]")
        sys.exit(1)

    midi_dir = Path(sys.argv[1])
    if not midi_dir.exists():
        print(f"Error: Directory {midi_dir} does not exist")
        sys.exit(1)

    output_file = "quick_analysis.json"
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    # Find MIDI files
    midi_files = list(midi_dir.glob("*.mid")) + list(midi_dir.glob("*.midi"))

    if not midi_files:
        print(f"Error: No MIDI files found in {midi_dir}")
        sys.exit(1)

    print(f"Found {len(midi_files)} MIDI files")
    print("Analyzing...")

    results = []
    errors = []

    for i, midi_file in enumerate(midi_files, 1):
        print(f"  [{i}/{len(midi_files)}] {midi_file.name}")
        result = analyze_single_midi(midi_file)
        if "error" in result:
            errors.append(result)
        else:
            results.append(result)

    # Aggregate statistics
    if results:
        durations = [r["duration_beats"] for r in results]
        max_gaps = [r["gaps"]["max"] for r in results]
        mean_gaps = [r["gaps"]["mean"] for r in results]
        note_counts = [r["note_count"] for r in results]

        summary = {
            "total_files": len(results),
            "errors": len(errors),
            "duration": {
                "mean": round(statistics.mean(durations), 2),
                "median": round(statistics.median(durations), 2),
                "min": round(min(durations), 2),
                "max": round(max(durations), 2),
            },
            "gaps": {
                "max_gap_mean": round(statistics.mean(max_gaps), 2),
                "max_gap_median": round(statistics.median(max_gaps), 2),
                "mean_gap_mean": round(statistics.mean(mean_gaps), 2),
                "mean_gap_median": round(statistics.median(mean_gaps), 2),
            },
            "notes": {
                "mean": round(statistics.mean(note_counts), 2),
                "median": round(statistics.median(note_counts), 2),
            },
        }

        # Group by length
        short = [r for r in results if r["duration_beats"] < 64]
        medium = [r for r in results if 64 <= r["duration_beats"] < 200]
        long_pieces = [r for r in results if r["duration_beats"] >= 200]

        summary["by_length"] = {
            "short_<64_beats": len(short),
            "medium_64-200_beats": len(medium),
            "long_>=200_beats": len(long_pieces),
        }

        output = {
            "summary": summary,
            "files": results,
            "errors": errors,
        }
    else:
        output = {"error": "No valid files analyzed", "errors": errors}

    # Save results
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_file}")
    print("\nSummary:")
    print(f"  Successfully analyzed: {len(results)} files")
    print(f"  Errors: {len(errors)}")
    if results:
        print(f"  Average duration: {summary['duration']['mean']:.1f} beats")
        print(f"  Average max gap: {summary['gaps']['max_gap_mean']:.2f} beats")
        print(f"  Average mean gap: {summary['gaps']['mean_gap_mean']:.2f} beats")


if __name__ == "__main__":
    main()
