"""Modify command: Modify existing compositions."""
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
from ...iterate import composition_to_canonical_json, iteration_prompt_template, transpose_composition
from ...output_util import write_output_with_sidecar
from ...parser import parse_composition_from_text
from ...renderers.mido_renderer import render_midi_mido


def handle_modify(args) -> int:
    """Handle the modify command."""
    try:
        # Treat as model output / JSON text file (parse_composition_from_text is lenient).
        text = read_text(args.in_path)
        comp = parse_composition_from_text(text)

        if args.transpose:
            comp = transpose_composition(comp, args.transpose)

        # Determine output directory and paths
        base_name = derive_base_name_from_path(args.in_path, "modify-output")
        output_dir = get_output_base_dir(base_name, "modify")
        
        # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
        if args.out_path is not None:
            out_json_path = resolve_output_path(
                args.out_path, output_dir, "composition.json", "modify"
            )
        else:
            out_json_path = None
        
        # For MIDI, auto-generate path if --render is used without explicit path
        if args.render:
            if args.out_midi_path is None:
                # Auto-generate MIDI path from input/output name
                if args.out_path is not None:
                    midi_name = args.out_path.stem + ".mid"
                else:
                    midi_name = args.in_path.stem + ".mid"
                out_midi_path = resolve_output_path(
                    Path(midi_name), output_dir, "composition.mid", "modify"
                )
            else:
                out_midi_path = resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "modify"
                )
        else:
            out_midi_path = resolve_output_path(
                args.out_midi_path, output_dir, "composition.mid", "modify"
            ) if args.out_midi_path is not None else None
        prompt_out_path = resolve_output_path(
            args.prompt_out_path, output_dir, "prompt.txt", "modify"
        ) if args.prompt_out_path is not None else None

        if args.provider:
            instructions = (args.instructions or "").strip()
            # Instructions are optional but recommended
            template = iteration_prompt_template(comp, instructions=instructions)
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
            if raw_out_path is not None and raw_out_path.exists():
                if args.verbose:
                    sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                raw_text = read_text(raw_out_path)
            
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

            updated = parse_composition_from_text(raw_text)
            out_json = composition_to_canonical_json(updated)

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
                # Always write sidecar if we have raw_text (even if cached) because:
                # 1. If file is being overwritten, we want to update the sidecar
                # 2. If file is being versioned, we want a matching versioned sidecar
                result = write_output_with_sidecar(
                    out_json_path,
                    out_json,
                    sidecar_content=raw_text,
                    provider=args.provider,
                    overwrite=args.overwrite,
                )
                sys.stdout.write(str(result.primary_path) + "\n")

            if args.render:
                render_midi_mido(updated, out_midi_path)
        else:
            out_json = composition_to_canonical_json(comp)

            if args.out_path is None:
                sys.stdout.write(out_json)
            else:
                write_text(out_json_path, out_json)
                sys.stdout.write(str(out_json_path) + "\n")

            if prompt_out_path is not None:
                template = iteration_prompt_template(comp, instructions=args.instructions)
                write_text(prompt_out_path, template)

            if args.render:
                render_midi_mido(comp, out_midi_path)
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the modify command parser."""
    parser.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON (or raw LLM output text).",
    )
    parser.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--transpose", "-t",
        type=int,
        default=0,
        help="Transpose all notes by this many semitones (can be negative).",
    )
    parser.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write a ready-to-paste LLM prompt that includes the composition JSON.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "ollama"],
        default=None,
        help="AI provider to use for modification: 'gemini' (cloud) or 'ollama' (local). If omitted, only generates a prompt template (use --prompt to save it).",
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
        help="Also render the (possibly AI-modified) composition to MIDI.",
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
        help="Instructions for modifying the composition (optional, but recommended when using --provider).",
    )
