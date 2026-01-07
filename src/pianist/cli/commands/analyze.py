"""Analyze command: Analyze MIDI or JSON files."""
from __future__ import annotations

import json
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
from ...analyze import analyze_midi, analysis_prompt_template
from ...iterate import composition_to_canonical_json
from ...musical_analysis import MUSIC21_AVAILABLE, analyze_composition as analyze_composition_musical
from ...output_util import write_output_with_sidecar
from ...parser import parse_composition_from_text
from ...renderers.mido_renderer import render_midi_mido


def handle_analyze(args) -> int:
    """Handle the analyze command."""
    try:
        suffix = args.in_path.suffix.lower()
        
        # Handle JSON input (composition analysis)
        if suffix == ".json":
            if not MUSIC21_AVAILABLE:
                sys.stderr.write(
                    "warning: music21 is not installed. Musical analysis requires music21. "
                    "Install with: pip install music21\n"
                )
                return 1
            
            # Load composition from JSON
            text = read_text(args.in_path)
            comp = parse_composition_from_text(text)
            
            # Perform musical analysis
            musical_analysis = analyze_composition_musical(comp)
            
            # Format analysis results as JSON
            analysis_result = {
                "source": str(args.in_path),
                "composition": {
                    "title": comp.title,
                    "bpm": comp.bpm,
                    "key_signature": comp.key_signature,
                    "time_signature": f"{comp.time_signature.numerator}/{comp.time_signature.denominator}",
                },
                "analysis": {
                    "motifs": [
                        {
                            "start": m.start,
                            "duration": m.duration,
                            "pitches": m.pitches,
                            "description": m.description,
                        }
                        for m in musical_analysis.motifs
                    ],
                    "phrases": [
                        {
                            "start": p.start,
                            "duration": p.duration,
                            "description": p.description,
                        }
                        for p in musical_analysis.phrases
                    ],
                    "harmony": {
                        "chords": [
                            {
                                "start": c.start,
                                "pitches": c.pitches,
                                "name": c.name,
                                "roman_numeral": c.roman_numeral,
                                "function": c.function,
                                "inversion": c.inversion,
                                "is_cadence": c.is_cadence,
                                "cadence_type": c.cadence_type,
                            }
                            for c in musical_analysis.harmonic_progression.chords
                        ] if musical_analysis.harmonic_progression else [],
                        "key": musical_analysis.harmonic_progression.key if musical_analysis.harmonic_progression else None,
                        "roman_numerals": musical_analysis.harmonic_progression.roman_numerals if musical_analysis.harmonic_progression else None,
                        "progression": musical_analysis.harmonic_progression.progression if musical_analysis.harmonic_progression else None,
                        "cadences": musical_analysis.harmonic_progression.cadences if musical_analysis.harmonic_progression else None,
                    } if musical_analysis.harmonic_progression else None,
                    "form": musical_analysis.form,
                    "key_ideas": musical_analysis.key_ideas,
                    "expansion_suggestions": musical_analysis.expansion_suggestions,
                },
            }
            
            # Determine output directory and paths
            base_name = derive_base_name_from_path(args.in_path, "analyze-output")
            output_dir = get_output_base_dir(base_name, "analyze")
            
            if args.out_path is not None:
                out_json_path = resolve_output_path(
                    args.out_path, output_dir, "analysis.json", "analyze"
                )
            else:
                out_json_path = None
            
            # Output analysis
            analysis_json = json.dumps(analysis_result, indent=2)
            if args.out_path is None:
                sys.stdout.write(analysis_json)
            else:
                write_text(out_json_path, analysis_json)
                sys.stdout.write(str(out_json_path) + "\n")
            
            return 0
        
        # Handle MIDI input (existing behavior)
        if suffix not in (".mid", ".midi"):
            raise ValueError("Input must be a .mid, .midi, or .json file.")

        analysis = analyze_midi(args.in_path)

        # Determine output directory and paths
        base_name = derive_base_name_from_path(args.in_path, "analyze-output")
        output_dir = get_output_base_dir(base_name, "analyze")
        
        # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
        if args.out_path is not None:
            out_json_path = resolve_output_path(
                args.out_path, output_dir, "analysis.json", "analyze"
            )
        else:
            out_json_path = None
        
        # For MIDI, auto-generate path if --render is used without explicit path
        if args.render and args.provider:
            if args.out_midi_path is None:
                # Auto-generate MIDI path from input/output name
                if args.out_path is not None:
                    midi_name = args.out_path.stem + ".mid"
                else:
                    midi_name = args.in_path.stem + ".mid"
                out_midi_path = resolve_output_path(
                    Path(midi_name), output_dir, "composition.mid", "analyze"
                )
            else:
                out_midi_path = resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "analyze"
                )
        else:
            out_midi_path = resolve_output_path(
                args.out_midi_path, output_dir, "composition.mid", "analyze"
            ) if args.out_midi_path is not None else None
        prompt_out_path = resolve_output_path(
            args.prompt_out_path, output_dir, "prompt.txt", "analyze"
        ) if args.prompt_out_path is not None else None

        if args.provider:
            instructions = (args.instructions or "").strip()
            # Instructions are optional but recommended
            template = analysis_prompt_template(analysis, instructions=instructions)
            prompt = prompt_from_template(template)

            if prompt_out_path is not None:
                write_text(prompt_out_path, template)

            # Determine raw output path (for both reading cached and saving new)
            raw_out_path: Path | None = args.raw_out_path
            if raw_out_path is None and out_json_path is not None:
                # Default: next to JSON output (only if --out was provided)
                raw_out_path = derive_raw_path(out_json_path, args.provider)
            elif raw_out_path is not None and not raw_out_path.is_absolute():
                # Relative path: resolve relative to output directory
                raw_out_path = output_dir / raw_out_path.name
            
            # Check if we have a cached response
            raw_text: str | None = None
            cached_raw_path: Path | None = None
            if raw_out_path is not None and raw_out_path.exists():
                if args.verbose:
                    sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                raw_text = read_text(raw_out_path)
                cached_raw_path = raw_out_path
            
            # If no cached response, call AI provider
            if raw_text is None:
                # Set default model if not provided
                model = args.model
                if model is None:
                    model = "gemini-flash-latest" if args.provider == "gemini" else "gpt-oss:20b"
                
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

            comp = parse_composition_from_text(raw_text)
            out_json = composition_to_canonical_json(comp)

            if args.out_path is None:
                sys.stdout.write(out_json)
                # Save raw response if we have it and no JSON output path
                if raw_text is not None and raw_out_path is not None:
                    write_text(raw_out_path, raw_text, version_if_exists=not args.overwrite)
                elif raw_text is not None:
                    # No path to save raw response - show warning
                    sys.stderr.write(
                        "warning: AI raw output was not saved. Provide --raw (-r) "
                        "or also provide --output (-o) to enable an automatic default.\n"
                    )
            else:
                # Use unified output utility for coordinated versioning
                # Always write sidecar if we have raw_text (even if cached)
                result = write_output_with_sidecar(
                    out_json_path,
                    out_json,
                    sidecar_content=raw_text,
                    provider=args.provider,
                    overwrite=args.overwrite,
                )
                sys.stdout.write(str(result.primary_path) + "\n")

            if args.render:
                render_midi_mido(comp, out_midi_path)
            return 0

        if args.render:
            raise ValueError("--render is only supported with --provider for 'analyze'.")

        if args.format in ("json", "both"):
            out_json = analysis.to_pretty_json()
            if args.out_path is None:
                sys.stdout.write(out_json)
            else:
                write_text(out_json_path, out_json)
                sys.stdout.write(str(out_json_path) + "\n")

        if args.format in ("prompt", "both"):
            prompt = analysis_prompt_template(analysis, instructions=args.instructions)
            if prompt_out_path is not None:
                write_text(prompt_out_path, prompt)
                # Only print the path if we didn't already print JSON path.
                if args.format == "prompt":
                    sys.stdout.write(str(prompt_out_path) + "\n")
            else:
                # If --out was provided and we're in prompt-only mode, treat it as prompt output.
                if args.format == "prompt" and args.out_path is not None:
                    write_text(out_json_path, prompt)
                    sys.stdout.write(str(out_json_path) + "\n")
                else:
                    sys.stdout.write(prompt)
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the analyze command parser."""
    parser.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input file: MIDI (.mid/.midi) or JSON composition (.json).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["prompt", "json", "both"],
        default="prompt",
        help="Output format: 'prompt' (default), 'json', or 'both'.",
    )
    parser.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output path for JSON (or prompt if --format prompt and --prompt not provided). If omitted, prints to stdout.",
    )
    parser.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write the prompt text to this path.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "ollama"],
        default=None,
        help="AI provider to use for generating a new composition: 'gemini' (cloud) or 'ollama' (local). If omitted, only generates analysis/prompt.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use with the provider. Default: gemini-flash-latest (Gemini) or gpt-oss:20b (Ollama). Only used with --provider.",
    )
    parser.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Also render the AI-generated composition to MIDI (only valid with --provider).",
    )
    parser.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    parser.add_argument(
        "--instructions",
        type=str,
        default="",
        help="Instructions for composing a new piece (optional, but recommended when using --provider).",
    )
