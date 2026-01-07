"""Expand command: Expand incomplete compositions."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from ..util import (
    derive_base_name_from_path,
    derive_raw_path,
    get_output_base_dir,
    prompt_from_template,
    read_text,
    resolve_output_path,
    write_text,
)
from ...ai_providers import GeminiError, OllamaError, generate_text_unified
from ...expansion_strategy import ExpansionStrategy, generate_expansion_strategy
from ...iterate import composition_to_canonical_json, iteration_prompt_template
from ...musical_analysis import MUSIC21_AVAILABLE, analyze_composition as analyze_composition_musical
from ...output_util import write_output_with_sidecar
from ...parser import parse_composition_from_text
from ...reference_db import get_default_database
from ...renderers.mido_renderer import render_midi_mido
from ...validation import ValidationResult, validate_expansion


def handle_expand(args) -> int:
    """Handle the expand command."""
    try:
        # Load composition
        text = read_text(args.in_path)
        comp = parse_composition_from_text(text)
        
        # Calculate current length
        current_length = 0.0
        for track in comp.tracks:
            for event in track.events:
                event_end = event.start + (getattr(event, "duration", 0.0))
                current_length = max(current_length, event_end)
        
        if args.verbose:
            sys.stderr.write(f"Current length: {current_length:.2f} beats\n")
            sys.stderr.write(f"Target length: {args.target_length:.2f} beats\n")
            sys.stderr.write(f"Expansion needed: {args.target_length - current_length:.2f} beats\n")
        
        # Determine output directory and paths (needed for both provider and no-provider cases)
        base_name = derive_base_name_from_path(args.in_path, "expand-output")
        output_dir = get_output_base_dir(base_name, "expand")
        
        # If no provider, generate and display expansion strategy
        if args.provider is None:
            if MUSIC21_AVAILABLE:
                try:
                    # Perform analysis
                    musical_analysis = analyze_composition_musical(comp)
                    
                    # Generate detailed expansion strategy
                    strategy = generate_expansion_strategy(
                        comp,
                        args.target_length,
                        analysis=musical_analysis
                    )
                    
                    # Display strategy
                    sys.stdout.write("Expansion Strategy:\n")
                    sys.stdout.write("=" * 60 + "\n")
                    sys.stdout.write(f"Current length: {current_length:.2f} beats\n")
                    sys.stdout.write(f"Target length: {args.target_length:.2f} beats\n")
                    expansion_ratio = args.target_length / current_length if current_length > 0 else 1.0
                    sys.stdout.write(f"Expansion ratio: {expansion_ratio:.2f}x\n\n")
                    
                    sys.stdout.write(f"Overall Approach:\n{strategy.overall_approach}\n\n")
                    
                    if strategy.motif_developments:
                        sys.stdout.write("Motif Developments:\n")
                        for dev in strategy.motif_developments:
                            sys.stdout.write(f"  - {dev.description}\n")
                        sys.stdout.write("\n")
                    
                    if strategy.section_expansions:
                        sys.stdout.write("Section Expansions:\n")
                        for exp in strategy.section_expansions:
                            sys.stdout.write(f"  - {exp.description}\n")
                        sys.stdout.write("\n")
                    
                    if strategy.transitions:
                        sys.stdout.write("Transitions:\n")
                        for trans in strategy.transitions:
                            sys.stdout.write(f"  - {trans}\n")
                        sys.stdout.write("\n")
                    
                    if strategy.preserve:
                        sys.stdout.write("Preserve:\n")
                        for item in strategy.preserve:
                            sys.stdout.write(f"  - {item}\n")
                        sys.stdout.write("\n")
                    
                    # For now, just copy the composition (no AI to expand it)
                    expanded_comp = comp
                except Exception as e:
                    if args.debug:
                        traceback.print_exc(file=sys.stderr)
                    sys.stderr.write(f"warning: Could not generate expansion strategy: {e}\n")
                    sys.stderr.write(
                        f"Current: {current_length:.2f} beats, Target: {args.target_length:.2f} beats\n"
                    )
                    expanded_comp = comp
            else:
                sys.stderr.write(
                    "warning: Expansion strategy generation requires music21. "
                    "Install with: pip install music21\n"
                )
                sys.stderr.write(
                    f"Current: {current_length:.2f} beats, Target: {args.target_length:.2f} beats\n"
                )
                expanded_comp = comp
        else:
            # Generate expansion prompt with analysis and strategy
            # Perform musical analysis to inform expansion
            if MUSIC21_AVAILABLE:
                try:
                    musical_analysis = analyze_composition_musical(comp)
                    
                    # Generate detailed expansion strategy
                    strategy = generate_expansion_strategy(
                        comp,
                        args.target_length,
                        analysis=musical_analysis
                    )
                    
                    # Build expansion instructions with analysis and strategy
                    expansion_instructions = (
                        f"Expand this composition from {current_length:.2f} beats to {args.target_length:.2f} beats. "
                        f"Preserve the original musical ideas and develop them naturally. "
                        f"Maintain the same style, tempo ({comp.bpm} bpm), and key signature ({comp.key_signature or 'original'}).\n\n"
                    )
                    
                    # Add overall approach from strategy
                    expansion_instructions += f"Overall Approach: {strategy.overall_approach}\n\n"
                    
                    # Add motif developments from strategy
                    if strategy.motif_developments:
                        expansion_instructions += f"Motif Development ({len(strategy.motif_developments)} motifs):\n"
                        for dev in strategy.motif_developments[:5]:  # Limit to top 5
                            expansion_instructions += f"- {dev.description}\n"
                        expansion_instructions += "\n"
                    
                    # Add section expansions from strategy
                    if strategy.section_expansions:
                        expansion_instructions += f"Section Expansions ({len(strategy.section_expansions)} sections):\n"
                        for exp in strategy.section_expansions[:5]:  # Limit to top 5
                            expansion_instructions += f"- {exp.description}\n"
                        expansion_instructions += "\n"
                    
                    # Add transition suggestions
                    if strategy.transitions:
                        expansion_instructions += "Transitions:\n"
                        for trans in strategy.transitions[:3]:
                            expansion_instructions += f"- {trans}\n"
                        expansion_instructions += "\n"
                    
                    # Add analysis results for context
                    if musical_analysis.harmonic_progression and musical_analysis.harmonic_progression.chords:
                        expansion_instructions += f"Harmonic analysis: {len(musical_analysis.harmonic_progression.chords)} chords detected. "
                        if musical_analysis.harmonic_progression.key:
                            expansion_instructions += f"Key: {musical_analysis.harmonic_progression.key}. "
                        expansion_instructions += "Maintain harmonic coherence while expanding.\n\n"
                    
                    if musical_analysis.form:
                        expansion_instructions += f"Musical form: {musical_analysis.form}. Preserve this form structure while expanding sections.\n\n"
                    
                    # Add preserve list
                    if strategy.preserve:
                        expansion_instructions += "Preserve:\n"
                        for item in strategy.preserve[:5]:
                            expansion_instructions += f"- {item}\n"
                        expansion_instructions += "\n"
                    
                    # Find and include relevant musical references
                    try:
                        ref_db = get_default_database()
                        references = ref_db.find_relevant_references(comp, analysis=musical_analysis, limit=3)
                        if references:
                            expansion_instructions += "Musical References (examples to learn from):\n"
                            for ref in references:
                                expansion_instructions += f"- {ref.title}"
                                if ref.description:
                                    expansion_instructions += f": {ref.description}"
                                if ref.style:
                                    expansion_instructions += f" (Style: {ref.style})"
                                if ref.form:
                                    expansion_instructions += f" (Form: {ref.form})"
                                if ref.techniques:
                                    expansion_instructions += f" (Techniques: {', '.join(ref.techniques)})"
                                expansion_instructions += "\n"
                            
                            # Include reference compositions as examples
                            expansion_instructions += "\nReference Compositions (study these examples):\n"
                            for ref in references[:2]:  # Limit to 2 to avoid prompt bloat
                                ref_json = composition_to_canonical_json(ref.composition)
                                expansion_instructions += f"\n{ref.title}:\n{ref_json}\n"
                            expansion_instructions += "\n"
                    except Exception as e:
                        if args.verbose:
                            sys.stderr.write(f"warning: Could not load musical references: {e}\n")
                    
                except Exception as e:
                    if args.verbose:
                        sys.stderr.write(f"warning: Musical analysis failed: {e}. Using basic expansion instructions.\n")
                    # Fall back to basic instructions
                    expansion_instructions = (
                        f"Expand this composition from {current_length:.2f} beats to {args.target_length:.2f} beats. "
                        f"Preserve the original musical ideas and develop them naturally. "
                        f"Maintain the same style, tempo ({comp.bpm} bpm), and key signature ({comp.key_signature or 'original'})."
                    )
            else:
                # No music21 available, use basic instructions
                expansion_instructions = (
                    f"Expand this composition from {current_length:.2f} beats to {args.target_length:.2f} beats. "
                    f"Preserve the original musical ideas and develop them naturally. "
                    f"Maintain the same style, tempo ({comp.bpm} bpm), and key signature ({comp.key_signature or 'original'})."
                )
            
            if args.preserve_motifs:
                expansion_instructions += " Preserve all marked motifs and develop them throughout."
            
            if args.preserve:
                preserve_ids = [id.strip() for id in args.preserve.split(",")]
                expansion_instructions += f" Preserve these specific ideas: {', '.join(preserve_ids)}."
            
            template = iteration_prompt_template(comp, instructions=expansion_instructions)
            prompt = prompt_from_template(template)
            
            # Determine output directory and paths
            base_name = derive_base_name_from_path(args.in_path, "expand-output")
            output_dir = get_output_base_dir(base_name, "expand")
            
            if args.out_path is not None:
                out_json_path = resolve_output_path(
                    args.out_path, output_dir, "composition.json", "expand"
                )
            else:
                out_json_path = None
            
            # Determine raw output path
            raw_out_path: Path | None = args.raw_out_path
            if raw_out_path is None and out_json_path is not None:
                raw_out_path = derive_raw_path(out_json_path, args.provider)
            elif raw_out_path is not None and not raw_out_path.is_absolute():
                raw_out_path = output_dir / raw_out_path.name
            
            # Check for cached response
            raw_text: str | None = None
            cached_raw_path: Path | None = None
            if raw_out_path is not None and raw_out_path.exists():
                if args.verbose:
                    sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                raw_text = read_text(raw_out_path)
                cached_raw_path = raw_out_path
            
            # Call AI provider if no cached response
            if raw_text is None:
                # Set default model if not provided
                model = args.model
                if model is None:
                    model = "gemini-flash-latest" if args.provider == "gemini" else "gpt-oss:20b"
                
                if args.verbose:
                    sys.stderr.write(f"Calling AI provider ({args.provider}) for expansion...\n")
                
                try:
                    raw_text = generate_text_unified(
                        provider=args.provider,
                        model=model,
                        prompt=prompt,
                        verbose=args.verbose
                    )
                except (GeminiError, OllamaError) as e:
                    sys.stderr.write(f"error: {type(e).__name__}: {e}\n")
                    return 1
            
            # Parse expanded composition
            expanded_comp = parse_composition_from_text(raw_text)
            
            # Calculate expanded length
            expanded_length = 0.0
            for track in expanded_comp.tracks:
                for event in track.events:
                    event_end = event.start + (getattr(event, "duration", 0.0))
                    expanded_length = max(expanded_length, event_end)
            
            if args.verbose:
                sys.stderr.write(f"Expanded length: {expanded_length:.2f} beats\n")
            
            # Validate if requested
            if args.validate:
                if MUSIC21_AVAILABLE:
                    try:
                        validation_result = validate_expansion(
                            comp,
                            expanded_comp,
                            target_length=args.target_length
                        )
                        
                        # Display validation results
                        if args.verbose:
                            sys.stderr.write("\nValidation Results:\n")
                            sys.stderr.write("=" * 60 + "\n")
                            sys.stderr.write(
                                f"Overall Quality: {validation_result.overall_quality:.2%}\n"
                            )
                            sys.stderr.write(
                                f"Motifs Preserved: {validation_result.motifs_preserved_count}/"
                                f"{validation_result.motifs_total_count}\n"
                            )
                            sys.stderr.write(
                                f"Development Quality: {validation_result.development_quality:.2%}\n"
                            )
                            sys.stderr.write(
                                f"Harmonic Coherence: {validation_result.harmonic_coherence:.2%}\n"
                            )
                            sys.stderr.write(
                                f"Form Consistency: {validation_result.form_consistency:.2%}\n"
                            )
                        
                        # Report issues
                        if validation_result.issues:
                            for issue in validation_result.issues:
                                sys.stderr.write(f"⚠️  Issue: {issue}\n")
                        
                        # Report warnings
                        if validation_result.warnings:
                            for warning in validation_result.warnings:
                                sys.stderr.write(f"⚠️  Warning: {warning}\n")
                        
                        # Report pass/fail
                        if validation_result.passed:
                            if args.verbose:
                                sys.stderr.write("✅ Validation passed\n")
                        else:
                            sys.stderr.write(
                                "❌ Validation failed. Review issues above.\n"
                            )
                    except Exception as e:
                        if args.debug:
                            traceback.print_exc(file=sys.stderr)
                        sys.stderr.write(
                            f"warning: Validation failed: {e}. "
                            "Proceeding with basic checks.\n"
                        )
                        # Fall back to basic checks
                        if expanded_length < current_length:
                            sys.stderr.write(
                                "warning: Expanded composition is shorter than original. "
                                "This may indicate an issue.\n"
                            )
                        elif expanded_length < args.target_length * 0.9:
                            sys.stderr.write(
                                f"warning: Expanded composition ({expanded_length:.2f} beats) "
                                f"is significantly shorter than target ({args.target_length:.2f} beats).\n"
                            )
                else:
                    sys.stderr.write(
                        "warning: Validation requires music21. "
                        "Install with: pip install music21\n"
                    )
                    # Basic check: did it expand?
                    if expanded_length < current_length:
                        sys.stderr.write(
                            "warning: Expanded composition is shorter than original. "
                            "This may indicate an issue.\n"
                        )
                    elif expanded_length < args.target_length * 0.9:
                        sys.stderr.write(
                            f"warning: Expanded composition ({expanded_length:.2f} beats) "
                            f"is significantly shorter than target ({args.target_length:.2f} beats).\n"
                        )
            
            # Save expanded composition
            expanded_json = composition_to_canonical_json(expanded_comp)
            
            if args.out_path is None:
                sys.stdout.write(expanded_json)
                # Save raw response if we have it and no JSON output path
                if raw_text is not None and raw_out_path is not None:
                    if cached_raw_path is None:
                        write_text(raw_out_path, raw_text, version_if_exists=not args.overwrite)
            else:
                # Use unified output utility for coordinated versioning
                # Always write sidecar if we have raw_text (even if cached)
                result = write_output_with_sidecar(
                    out_json_path,
                    expanded_json,
                    sidecar_content=raw_text,
                    provider=args.provider,
                    overwrite=args.overwrite,
                )
                sys.stdout.write(str(result.primary_path) + "\n")
            
            # Render if requested
            if args.render:
                if args.out_midi_path is None:
                    if args.out_path is not None:
                        midi_name = args.out_path.stem + ".mid"
                    else:
                        midi_name = args.in_path.stem + "_expanded.mid"
                    out_midi_path = resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "expand"
                    )
                else:
                    out_midi_path = resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "expand"
                    )
                render_midi_mido(expanded_comp, out_midi_path)
                sys.stdout.write(f"Rendered to: {out_midi_path}\n")
                return 0
            
            return 0
        
        # No provider case: save unchanged composition
        expanded_json = composition_to_canonical_json(expanded_comp)
        if args.out_path is None:
            sys.stdout.write(expanded_json)
        else:
            out_path = resolve_output_path(args.out_path, output_dir, args.in_path.name, "expand")
            write_text(out_path, expanded_json)
            sys.stdout.write(str(out_path) + "\n")
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the expand command parser."""
    parser.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON (preferably annotated).",
    )
    parser.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output expanded JSON path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--target-length",
        type=float,
        required=True,
        help="Target length in beats.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "ollama"],
        default=None,
        help="AI provider to use for expansion: 'gemini' (cloud) or 'ollama' (local). If omitted, only generates expansion strategy.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use with the provider. Default: gemini-flash-latest (Gemini) or gpt-oss:20b (Ollama). Only used with --provider.",
    )
    parser.add_argument(
        "--preserve-motifs",
        action="store_true",
        help="Preserve all marked motifs.",
    )
    parser.add_argument(
        "--preserve",
        type=str,
        default=None,
        help="Comma-separated list of idea IDs to preserve.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate expansion quality before returning.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Also render the expanded composition to MIDI.",
    )
    parser.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    parser.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
