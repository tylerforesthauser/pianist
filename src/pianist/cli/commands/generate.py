"""Generate command: Generate new compositions from text descriptions."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from ..util import (
    derive_raw_path,
    get_output_base_dir,
    read_text,
    resolve_output_path,
    write_text,
)
from ...ai_providers import GeminiError, OllamaError, generate_text_unified
from ...iterate import composition_to_canonical_json
from ...output_util import write_output_with_sidecar
from ...parser import parse_composition_from_text
from ...renderers.mido_renderer import render_midi_mido
from ...iterate import generation_prompt_for_api, generation_prompt_template


def handle_generate(args) -> int:
    """Handle the generate command."""
    try:
        # Read description from positional arg or stdin
        if args.description is not None:
            description = args.description.strip()
        else:
            description = sys.stdin.read().strip()
        
        if not description:
            raise ValueError("Composition description is required. Provide as argument or pipe text to stdin.")
        
        # Determine output directory and paths
        base_name = "generate-output"
        output_dir = get_output_base_dir(base_name, "generate")
        
        # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
        if args.out_path is not None:
            out_json_path = resolve_output_path(
                args.out_path, output_dir, "composition.json", "generate"
            )
        else:
            out_json_path = None
        
        # Validate --render requires --provider
        if args.render and args.provider is None:
            raise ValueError("--render is only supported with --provider for 'generate'.")
        
        # For MIDI, auto-generate path if --render is used without explicit path
        if args.render:
            if args.out_midi_path is None:
                # Auto-generate MIDI path from output name
                if args.out_path is not None:
                    midi_name = args.out_path.stem + ".mid"
                else:
                    midi_name = "composition.mid"
                out_midi_path = resolve_output_path(
                    Path(midi_name), output_dir, "composition.mid", "generate"
                )
            else:
                out_midi_path = resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "generate"
                )
        else:
            out_midi_path = resolve_output_path(
                args.out_midi_path, output_dir, "composition.mid", "generate"
            ) if args.out_midi_path is not None else None
        prompt_out_path = resolve_output_path(
            args.prompt_out_path, output_dir, "prompt.txt", "generate"
        ) if args.prompt_out_path is not None else None
        
        # Generate prompt template
        template = generation_prompt_template(description)
        
        if prompt_out_path is not None:
            write_text(prompt_out_path, template)
        
        # If no provider specified, just output the prompt
        if args.provider is None:
            if args.out_path is None:
                sys.stdout.write(template)
            else:
                write_text(out_json_path, template)
                sys.stdout.write(str(out_json_path) + "\n")
            return 0
        
        # Generate composition using AI provider
        # Use the full prompt for API calls (better quality)
        prompt = generation_prompt_for_api(description)
        
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
                model = "gemini-flash-latest" if args.provider == "gemini" else "llama3.2"
            
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
            sys.stdout.write(f"Rendered to: {out_midi_path}\n")
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the generate command parser."""
    parser.add_argument(
        "description",
        nargs="?",
        type=str,
        default=None,
        help="Text description of the composition to generate. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "ollama"],
        default=None,
        help="AI provider to use for generation: 'gemini' (cloud) or 'ollama' (local). If omitted, only generates a prompt template (use --prompt to save it).",
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
        help="Also render the generated composition to MIDI (only valid with --provider).",
    )
    parser.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from output name if --render is used without this flag.",
    )
    parser.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write a ready-to-paste LLM prompt to this path.",
    )
