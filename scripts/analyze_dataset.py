#!/usr/bin/env python3
"""
Comprehensive batch analysis tool for extracting composition metrics from a dataset.

This script uses the full pianist package to analyze MIDI files and extract
comprehensive metrics including motifs, phrases, harmony, form, and composition
structure. Results are aggregated across the dataset.

For quick basic statistics without full package installation, use `quick_analysis.py`.

Usage:
    python3 scripts/analyze_dataset.py <midi_directory> [--output output.json] [--verbose]

This script analyzes all MIDI files in a directory and aggregates statistics to inform
prompt engineering decisions and composition analysis.
"""

import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Add src to path for standalone execution
project_root = Path(__file__).parent
src_path = project_root / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from pianist.composition_metrics import (
        CompositionMetrics,
        analyze_composition_metrics,
    )
except ImportError:
    # Fallback if import fails
    print("Error: Could not import composition_metrics module.")
    print("Please ensure dependencies are installed: pip install pydantic mido")
    sys.exit(1)


def aggregate_metrics(metrics_list: list[CompositionMetrics]) -> dict[str, Any]:
    """Aggregate metrics across multiple compositions."""
    if not metrics_list:
        return {}

    # Filter out compositions that are too short or have no data
    valid_metrics = [m for m in metrics_list if m.duration_beats >= 16.0]

    if not valid_metrics:
        return {"error": "No valid compositions found"}

    aggregated: dict[str, Any] = {
        "total_compositions": len(valid_metrics),
        "total_duration_beats": sum(m.duration_beats for m in valid_metrics),
    }

    # Motif frequency analysis
    motif_frequencies = [
        m.motif_frequency_per_64_beats
        for m in valid_metrics
        if m.motif_frequency_per_64_beats is not None
    ]
    if motif_frequencies:
        aggregated["motif_frequency"] = {
            "mean": float(statistics.mean(motif_frequencies)),
            "median": float(statistics.median(motif_frequencies)),
            "min": float(min(motif_frequencies)),
            "max": float(max(motif_frequencies)),
            "p25": float(statistics.quantiles(motif_frequencies, n=4)[0])
            if len(motif_frequencies) >= 4
            else None,
            "p75": float(statistics.quantiles(motif_frequencies, n=4)[2])
            if len(motif_frequencies) >= 4
            else None,
        }

    # Motif repetition intervals
    all_intervals: list[float] = []
    for m in valid_metrics:
        if m.motif_repetition_interval_beats:
            dist = m.motif_repetition_interval_beats
            if dist.median:
                all_intervals.append(dist.median)

    if all_intervals:
        aggregated["motif_repetition_interval"] = {
            "mean": float(statistics.mean(all_intervals)),
            "median": float(statistics.median(all_intervals)),
            "min": float(min(all_intervals)),
            "max": float(max(all_intervals)),
        }

    # Gap analysis
    max_gaps = [m.gap_analysis.max_gap_beats for m in valid_metrics if m.gap_analysis]
    mean_gaps = [m.gap_analysis.mean_gap_beats for m in valid_metrics if m.gap_analysis]
    section_gaps = []
    for m in valid_metrics:
        if m.gap_analysis:
            section_gaps.extend(m.gap_analysis.gaps_between_sections)

    if max_gaps:
        aggregated["gaps"] = {
            "max_gap_mean": float(statistics.mean(max_gaps)),
            "max_gap_median": float(statistics.median(max_gaps)),
            "mean_gap_mean": float(statistics.mean(mean_gaps)),
            "mean_gap_median": float(statistics.median(mean_gaps)),
        }

    if section_gaps:
        aggregated["section_gaps"] = {
            "mean": float(statistics.mean(section_gaps)),
            "median": float(statistics.median(section_gaps)),
            "min": float(min(section_gaps)),
            "max": float(max(section_gaps)),
            "p95": float(statistics.quantiles(section_gaps, n=20)[18])
            if len(section_gaps) >= 20
            else None,
        }

    # Transition lengths
    all_transitions: list[float] = []
    for m in valid_metrics:
        all_transitions.extend(m.section_transitions)

    if all_transitions:
        aggregated["transition_lengths"] = {
            "mean": float(statistics.mean(all_transitions)),
            "median": float(statistics.median(all_transitions)),
            "min": float(min(all_transitions)),
            "max": float(max(all_transitions)),
            "p25": float(statistics.quantiles(all_transitions, n=4)[0])
            if len(all_transitions) >= 4
            else None,
            "p75": float(statistics.quantiles(all_transitions, n=4)[2])
            if len(all_transitions) >= 4
            else None,
        }

    # Variation metrics
    rhythmic_entropies = [
        m.variation_metrics.rhythmic_entropy for m in valid_metrics if m.variation_metrics
    ]
    melodic_entropies = [
        m.variation_metrics.melodic_entropy for m in valid_metrics if m.variation_metrics
    ]
    phrase_variances = [
        m.variation_metrics.phrase_length_variance for m in valid_metrics if m.variation_metrics
    ]

    if rhythmic_entropies:
        aggregated["variation"] = {
            "rhythmic_entropy": {
                "mean": float(statistics.mean(rhythmic_entropies)),
                "median": float(statistics.median(rhythmic_entropies)),
            },
            "melodic_entropy": {
                "mean": float(statistics.mean(melodic_entropies)),
                "median": float(statistics.median(melodic_entropies)),
            }
            if melodic_entropies
            else None,
            "phrase_length_variance": {
                "mean": float(statistics.mean(phrase_variances)),
                "median": float(statistics.median(phrase_variances)),
            }
            if phrase_variances
            else None,
        }

    # Phrase lengths
    all_phrase_lengths: list[float] = []
    for m in valid_metrics:
        all_phrase_lengths.extend(m.phrase_lengths)

    if all_phrase_lengths:
        aggregated["phrase_lengths"] = {
            "mean": float(statistics.mean(all_phrase_lengths)),
            "median": float(statistics.median(all_phrase_lengths)),
            "min": float(min(all_phrase_lengths)),
            "max": float(max(all_phrase_lengths)),
            "common_lengths": dict(
                Counter(round(pl, 1) for pl in all_phrase_lengths).most_common(10)
            ),
        }

    # Section counts
    section_counts = [m.section_count for m in valid_metrics]
    if section_counts:
        aggregated["sections"] = {
            "mean_per_composition": float(statistics.mean(section_counts)),
            "median_per_composition": float(statistics.median(section_counts)),
        }

    # Duration-based analysis
    short_pieces = [m for m in valid_metrics if m.duration_beats < 64]
    medium_pieces = [m for m in valid_metrics if 64 <= m.duration_beats < 200]
    long_pieces = [m for m in valid_metrics if m.duration_beats >= 200]

    if short_pieces:
        short_motif_freqs = [
            m.motif_frequency_per_64_beats for m in short_pieces if m.motif_frequency_per_64_beats
        ]
        if short_motif_freqs:
            aggregated["by_duration"] = {
                "short_<64_beats": {
                    "count": len(short_pieces),
                    "motif_frequency_mean": float(statistics.mean(short_motif_freqs)),
                },
            }

    if medium_pieces:
        medium_motif_freqs = [
            m.motif_frequency_per_64_beats for m in medium_pieces if m.motif_frequency_per_64_beats
        ]
        if medium_motif_freqs:
            if "by_duration" not in aggregated:
                aggregated["by_duration"] = {}
            aggregated["by_duration"]["medium_64-200_beats"] = {
                "count": len(medium_pieces),
                "motif_frequency_mean": float(statistics.mean(medium_motif_freqs)),
            }

    if long_pieces:
        long_motif_freqs = [
            m.motif_frequency_per_64_beats for m in long_pieces if m.motif_frequency_per_64_beats
        ]
        if long_motif_freqs:
            if "by_duration" not in aggregated:
                aggregated["by_duration"] = {}
            aggregated["by_duration"]["long_>=200_beats"] = {
                "count": len(long_pieces),
                "motif_frequency_mean": float(statistics.mean(long_motif_freqs)),
            }

    return aggregated


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze a dataset of MIDI files to extract composition metrics"
    )
    parser.add_argument(
        "midi_directory",
        type=str,
        help="Directory containing MIDI files to analyze",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="composition_metrics.json",
        help="Output JSON file for aggregated metrics",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information",
    )

    args = parser.parse_args()

    midi_dir = Path(args.midi_directory)
    if not midi_dir.exists():
        print(f"Error: Directory {midi_dir} does not exist")
        return 1

    # Find all MIDI files
    midi_files = list(midi_dir.glob("*.mid")) + list(midi_dir.glob("*.midi"))

    if not midi_files:
        print(f"Error: No MIDI files found in {midi_dir}")
        return 1

    print(f"Found {len(midi_files)} MIDI files")

    # Analyze each file
    all_metrics: list[CompositionMetrics] = []
    errors: list[tuple[str, str]] = []

    for i, midi_file in enumerate(midi_files, 1):
        if args.verbose:
            print(f"Analyzing {i}/{len(midi_files)}: {midi_file.name}")

        try:
            metrics = analyze_composition_metrics(midi_file)
            all_metrics.append(metrics)
        except Exception as e:
            errors.append((str(midi_file), str(e)))
            if args.verbose:
                print(f"  Error: {e}")

    if errors:
        print(f"\n{len(errors)} files had errors:")
        for file, error in errors[:10]:  # Show first 10 errors
            print(f"  {file}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    # Aggregate metrics
    print(f"\nAggregating metrics from {len(all_metrics)} successful analyses...")
    aggregated = aggregate_metrics(all_metrics)

    # Save results
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(aggregated, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print("\nSummary:")
    print(f"  Total compositions analyzed: {aggregated.get('total_compositions', 0)}")
    if "motif_frequency" in aggregated:
        print(f"  Mean motif frequency (per 64 beats): {aggregated['motif_frequency']['mean']:.2f}")
    if "transition_lengths" in aggregated:
        print(f"  Mean transition length: {aggregated['transition_lengths']['mean']:.2f} beats")
    if "section_gaps" in aggregated:
        print(f"  Mean gap at section boundaries: {aggregated['section_gaps']['mean']:.2f} beats")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
