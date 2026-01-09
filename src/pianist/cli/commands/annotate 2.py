"""Annotate command: Mark musical intent."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

from ...annotations import (
    add_expansion_point,
    add_key_idea,
    add_to_preserve_list,
    set_development_direction,
)
from ...iterate import composition_to_canonical_json
from ...musical_analysis import MUSIC21_AVAILABLE, _composition_to_music21_stream
from ...musical_analysis import analyze_composition as analyze_composition_musical
from ...parser import parse_composition_from_text
from ...schema import KeyIdea, MusicalIntent
from ..util import (
    derive_base_name_from_path,
    get_output_base_dir,
    read_text,
    resolve_output_path,
    write_text,
)


def handle_annotate(args) -> int:
    """Handle the annotate command."""
    try:
        # Load composition
        text = read_text(args.in_path)
        comp = parse_composition_from_text(text)

        # Determine output directory and paths
        base_name = derive_base_name_from_path(args.in_path, "annotate-output")
        output_dir = get_output_base_dir(base_name, "annotate")

        # If --show, just display current annotations and exit
        if args.show:
            if comp.musical_intent is not None:
                intent_dict = comp.musical_intent.model_dump()
                intent_json = json.dumps(intent_dict, indent=2)
                sys.stdout.write("Current annotations:\n")
                sys.stdout.write(intent_json + "\n")
            else:
                sys.stdout.write("No annotations found in composition.\n")
            return 0

        annotated_comp = comp

        # For --auto-detect, use analysis module
        if args.auto_detect:
            if not MUSIC21_AVAILABLE:
                sys.stderr.write(
                    "error: Auto-detection requires music21. Install with: pip install music21\n"
                )
                return 1

            try:
                # Perform musical analysis with pre-converted stream to avoid redundant conversion
                music21_stream = _composition_to_music21_stream(annotated_comp)
                musical_analysis = analyze_composition_musical(
                    annotated_comp, music21_stream=music21_stream
                )

                # Initialize musical_intent if it doesn't exist
                if annotated_comp.musical_intent is None:
                    annotated_comp.musical_intent = MusicalIntent()

                # Auto-detect and add motifs as key ideas
                for i, motif in enumerate(musical_analysis.motifs):
                    motif_id = f"auto_motif_{i + 1}"
                    # Check if this motif already exists
                    existing_ids = {idea.id for idea in annotated_comp.musical_intent.key_ideas}
                    if motif_id not in existing_ids:
                        key_idea = KeyIdea(
                            id=motif_id,
                            type="motif",
                            start=motif.start,
                            duration=motif.duration,
                            description=motif.description or f"Auto-detected motif {i + 1}",
                            importance="medium",
                        )
                        annotated_comp.musical_intent.key_ideas.append(key_idea)

                # Auto-detect and add phrases as key ideas
                for i, phrase in enumerate(musical_analysis.phrases):
                    phrase_id = f"auto_phrase_{i + 1}"
                    # Check if this phrase already exists
                    existing_ids = {idea.id for idea in annotated_comp.musical_intent.key_ideas}
                    if phrase_id not in existing_ids:
                        key_idea = KeyIdea(
                            id=phrase_id,
                            type="phrase",
                            start=phrase.start,
                            duration=phrase.duration,
                            description=phrase.description or f"Auto-detected phrase {i + 1}",
                            importance="medium",
                        )
                        annotated_comp.musical_intent.key_ideas.append(key_idea)

                if args.verbose:
                    motifs_added = len(list(musical_analysis.motifs))
                    phrases_added = len(list(musical_analysis.phrases))
                    sys.stderr.write(
                        f"Auto-detected {motifs_added} motif(s) and {phrases_added} phrase(s)\n"
                    )

            except Exception as e:
                if args.debug:
                    traceback.print_exc(file=sys.stderr)
                sys.stderr.write(f"error: Auto-detection failed: {e}\n")
                return 1
        else:
            # Process manual annotation flags
            annotations_added = False

            # Parse START-DURATION format (e.g., "0-4" means start=0, duration=4)
            def parse_time_range(time_str: str) -> tuple[float, float]:
                try:
                    parts = time_str.split("-")
                    if len(parts) != 2:
                        raise ValueError(
                            f"Invalid time range format: {time_str}. Expected 'START-DURATION'"
                        )
                    start = float(parts[0])
                    duration = float(parts[1])
                    if duration <= 0:
                        raise ValueError(f"Duration must be positive: {duration}")
                    return start, duration
                except ValueError as e:
                    raise ValueError(f"Invalid time range '{time_str}': {e}") from e

            # Generate idea ID if not provided
            idea_counter = 1

            def generate_idea_id(idea_type: str) -> str:
                nonlocal idea_counter
                existing_ids = set()
                if annotated_comp.musical_intent:
                    existing_ids = {idea.id for idea in annotated_comp.musical_intent.key_ideas}
                while True:
                    candidate = f"{idea_type}_{idea_counter}"
                    if candidate not in existing_ids:
                        idea_counter += 1
                        return candidate
                    idea_counter += 1

            # Mark motif
            if args.mark_motif:
                start, duration = parse_time_range(args.mark_motif[0])
                description = args.mark_motif[1]
                idea_id = args.idea_id or generate_idea_id("motif")
                annotated_comp = add_key_idea(
                    annotated_comp,
                    idea_id=idea_id,
                    idea_type="motif",
                    start=start,
                    duration=duration,
                    description=description,
                    importance=args.importance,
                    development_direction=args.development_direction,
                )
                annotations_added = True
                sys.stdout.write(f"Marked motif '{idea_id}' at {start}-{start + duration} beats\n")

            # Mark phrase
            if args.mark_phrase:
                start, duration = parse_time_range(args.mark_phrase[0])
                description = args.mark_phrase[1]
                idea_id = args.idea_id or generate_idea_id("phrase")
                annotated_comp = add_key_idea(
                    annotated_comp,
                    idea_id=idea_id,
                    idea_type="phrase",
                    start=start,
                    duration=duration,
                    description=description,
                    importance=args.importance,
                    development_direction=args.development_direction,
                )
                annotations_added = True
                sys.stdout.write(f"Marked phrase '{idea_id}' at {start}-{start + duration} beats\n")

            # Mark harmonic progression
            if args.mark_harmonic_progression:
                start, duration = parse_time_range(args.mark_harmonic_progression[0])
                description = args.mark_harmonic_progression[1]
                idea_id = args.idea_id or generate_idea_id("harmonic_progression")
                annotated_comp = add_key_idea(
                    annotated_comp,
                    idea_id=idea_id,
                    idea_type="harmonic_progression",
                    start=start,
                    duration=duration,
                    description=description,
                    importance=args.importance,
                    development_direction=args.development_direction,
                )
                annotations_added = True
                sys.stdout.write(
                    f"Marked harmonic progression '{idea_id}' at {start}-{start + duration} beats\n"
                )

            # Mark rhythmic pattern
            if args.mark_rhythmic_pattern:
                start, duration = parse_time_range(args.mark_rhythmic_pattern[0])
                description = args.mark_rhythmic_pattern[1]
                idea_id = args.idea_id or generate_idea_id("rhythmic_pattern")
                annotated_comp = add_key_idea(
                    annotated_comp,
                    idea_id=idea_id,
                    idea_type="rhythmic_pattern",
                    start=start,
                    duration=duration,
                    description=description,
                    importance=args.importance,
                    development_direction=args.development_direction,
                )
                annotations_added = True
                sys.stdout.write(
                    f"Marked rhythmic pattern '{idea_id}' at {start}-{start + duration} beats\n"
                )

            # Mark expansion point
            if args.mark_expansion:
                if args.target_length is None:
                    raise ValueError("--target-length is required with --mark-expansion")
                if args.development_strategy is None:
                    raise ValueError("--development-strategy is required with --mark-expansion")

                # Calculate current length
                current_length = 0.0
                for track in annotated_comp.tracks:
                    for event in track.events:
                        event_end = event.start + (getattr(event, "duration", 0.0))
                        current_length = max(current_length, event_end)

                preserve_list = None
                if args.preserve:
                    preserve_list = [id.strip() for id in args.preserve.split(",")]

                annotated_comp = add_expansion_point(
                    annotated_comp,
                    section=args.mark_expansion,
                    current_length=current_length,
                    suggested_length=args.target_length,
                    development_strategy=args.development_strategy,
                    preserve=preserve_list,
                )
                annotations_added = True
                sys.stdout.write(
                    f"Marked expansion point for section '{args.mark_expansion}': "
                    f"{current_length:.2f} → {args.target_length:.2f} beats\n"
                )

            # Set overall development direction
            if args.overall_direction:
                annotated_comp = set_development_direction(annotated_comp, args.overall_direction)
                annotations_added = True
                sys.stdout.write("Set overall development direction\n")

            # Add to preserve list
            if args.preserve and not args.mark_expansion:  # Only if not used for expansion point
                preserve_items = [item.strip() for item in args.preserve.split(",")]
                annotated_comp = add_to_preserve_list(annotated_comp, preserve_items)
                annotations_added = True
                sys.stdout.write(f"Added to preserve list: {', '.join(preserve_items)}\n")

            if not annotations_added and not args.auto_detect:
                sys.stderr.write(
                    "warning: No annotations specified. Use --mark-motif, --mark-expansion, "
                    "--auto-detect, or other annotation flags.\n"
                )

        # Determine output path
        if args.out_path is None:
            # Default: overwrite input file
            out_path = args.in_path
        else:
            out_path = resolve_output_path(args.out_path, output_dir, args.in_path.name, "annotate")

        # Save annotated composition
        annotated_json = composition_to_canonical_json(annotated_comp)
        write_text(out_path, annotated_json)
        sys.stdout.write(f"Saved to: {out_path}\n")
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the annotate command parser."""
    parser.add_argument(
        "-i",
        "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output annotated JSON path. If omitted, overwrites input file.",
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Automatically detect and annotate key ideas.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current annotations without modifying.",
    )
    parser.add_argument(
        "--mark-motif",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a motif. Format: --mark-motif '0-4' 'Opening motif'",
    )
    parser.add_argument(
        "--mark-phrase",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a phrase. Format: --mark-phrase '0-16' 'Opening phrase'",
    )
    parser.add_argument(
        "--mark-harmonic-progression",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a harmonic progression. Format: --mark-harmonic-progression '0-8' 'I-V-vi-IV'",
    )
    parser.add_argument(
        "--mark-rhythmic-pattern",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a rhythmic pattern. Format: --mark-rhythmic-pattern '0-2' 'Syncopated rhythm'",
    )
    parser.add_argument(
        "--idea-id",
        type=str,
        default=None,
        help="ID for the key idea (auto-generated if not provided).",
    )
    parser.add_argument(
        "--importance",
        choices=["high", "medium", "low"],
        default="medium",
        help="Importance level for the key idea (default: medium).",
    )
    parser.add_argument(
        "--development-direction",
        type=str,
        default=None,
        help="How to develop the key idea (e.g., 'expand and vary', 'preserve exactly').",
    )
    parser.add_argument(
        "--mark-expansion",
        type=str,
        metavar="SECTION",
        help="Mark an expansion point for a section.",
    )
    parser.add_argument(
        "--target-length",
        type=float,
        default=None,
        help="Target length in beats for expansion point (required with --mark-expansion).",
    )
    parser.add_argument(
        "--development-strategy",
        type=str,
        default=None,
        help="Development strategy for expansion (required with --mark-expansion).",
    )
    parser.add_argument(
        "--preserve",
        type=str,
        default=None,
        help="Comma-separated list of idea IDs or characteristics to preserve.",
    )
    parser.add_argument(
        "--overall-direction",
        type=str,
        default=None,
        help="Overall development direction for the composition.",
    )
