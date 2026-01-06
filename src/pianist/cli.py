from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from .parser import parse_composition_from_text
from .analyze import analyze_midi, analysis_prompt_template
from .iterate import (
    composition_from_midi,
    composition_to_canonical_json,
    iteration_prompt_template,
    transpose_composition,
)
from .renderers.mido_renderer import render_midi_mido

try:
    from .generate_openapi_schema import generate_openapi_schema
except ImportError:
    # Schema generation may not be available in all environments
    generate_openapi_schema = None


def _read_text(path: Path | None) -> str:
    if path is None:
        text = sys.stdin.read()
        if not text.strip():
            raise ValueError("Input is empty (no content provided).")
        return text
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError(f"Input file is empty: {path}")
        return text
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Input file not found: {path}") from e
    except PermissionError as e:
        raise PermissionError(f"Input file not readable: {path}") from e


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pianist",
        description="Convert AI-generated composition JSON into a MIDI file.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    render = sub.add_parser("render", help="Parse model output and render a MIDI file.")
    render.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=None,
        help="Input text file containing model output. If omitted, reads stdin.",
    )
    render.add_argument(
        "--out",
        dest="out_path",
        type=Path,
        required=True,
        help="Output MIDI path (e.g. out.mid).",
    )
    render.add_argument(
        "--debug",
        action="store_true",
        help="Print a full traceback on errors.",
    )

    iterate = sub.add_parser(
        "iterate",
        help="Import an existing JSON/MIDI and emit a clean, tweakable composition JSON seed.",
    )
    iterate.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition: a Pianist JSON (or raw LLM output text) OR a .mid/.midi file.",
    )
    iterate.add_argument(
        "--out",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    iterate.add_argument(
        "--transpose",
        type=int,
        default=0,
        help="Transpose all notes by this many semitones (can be negative).",
    )
    iterate.add_argument(
        "--prompt-out",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Optional: write a ready-to-paste LLM prompt that includes the seed JSON.",
    )
    iterate.add_argument(
        "--instructions",
        type=str,
        default=None,
        help="Optional: embed requested changes into the generated prompt template.",
    )
    iterate.add_argument(
        "--debug",
        action="store_true",
        help="Print a full traceback on errors.",
    )

    analyze = sub.add_parser(
        "analyze",
        help="Analyze a .mid/.midi file and emit prompt-friendly output.",
    )
    analyze.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        required=True,
        help="Input MIDI file (.mid/.midi).",
    )
    analyze.add_argument(
        "--format",
        choices=["prompt", "json", "both"],
        default="prompt",
        help="Output format: 'prompt' (default), 'json', or 'both'.",
    )
    analyze.add_argument(
        "--out",
        dest="out_path",
        type=Path,
        default=None,
        help="Output path for JSON (or prompt if --format prompt and --prompt-out not provided). If omitted, prints to stdout.",
    )
    analyze.add_argument(
        "--prompt-out",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Optional: write the prompt text to this path (recommended).",
    )
    analyze.add_argument(
        "--instructions",
        type=str,
        default=None,
        help="Optional: embed requested composition instructions into the generated prompt.",
    )
    analyze.add_argument(
        "--debug",
        action="store_true",
        help="Print a full traceback on errors.",
    )

    if generate_openapi_schema is not None:
        schema_cmd = sub.add_parser(
            "generate-schema",
            help="Generate OpenAPI and Gemini-compatible schema files for structured output.",
        )
        schema_cmd.add_argument(
            "--format",
            choices=["both", "openapi", "gemini"],
            default="both",
            help="Which schema format(s) to generate: 'both' (openapi+gemini), 'openapi', or 'gemini' (default: both).",
        )
        schema_cmd.add_argument(
            "--output-dir",
            type=Path,
            default=None,
            help="Directory to write schema files (default: project root).",
        )

    args = parser.parse_args(argv)

    if args.cmd == "render":
        try:
            text = _read_text(args.in_path)
            comp = parse_composition_from_text(text)
            out = render_midi_mido(comp, args.out_path)
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        sys.stdout.write(str(out) + "\n")
        return 0

    if args.cmd == "iterate":
        try:
            suffix = args.in_path.suffix.lower()
            if suffix in (".mid", ".midi"):
                comp = composition_from_midi(args.in_path)
            else:
                # Treat as model output / JSON text file (parse_composition_from_text is lenient).
                text = _read_text(args.in_path)
                comp = parse_composition_from_text(text)

            if args.transpose:
                comp = transpose_composition(comp, args.transpose)

            out_json = composition_to_canonical_json(comp)

            if args.out_path is None:
                sys.stdout.write(out_json)
            else:
                args.out_path.write_text(out_json, encoding="utf-8")
                sys.stdout.write(str(args.out_path) + "\n")

            if args.prompt_out_path is not None:
                prompt = iteration_prompt_template(comp, instructions=args.instructions)
                args.prompt_out_path.write_text(prompt, encoding="utf-8")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "analyze":
        try:
            suffix = args.in_path.suffix.lower()
            if suffix not in (".mid", ".midi"):
                raise ValueError("Input must be a .mid or .midi file.")

            analysis = analyze_midi(args.in_path)

            if args.format in ("json", "both"):
                out_json = analysis.to_pretty_json()
                if args.out_path is None:
                    sys.stdout.write(out_json)
                else:
                    args.out_path.write_text(out_json, encoding="utf-8")
                    sys.stdout.write(str(args.out_path) + "\n")

            if args.format in ("prompt", "both"):
                prompt = analysis_prompt_template(analysis, instructions=args.instructions)
                if args.prompt_out_path is not None:
                    args.prompt_out_path.write_text(prompt, encoding="utf-8")
                    # Only print the path if we didn't already print JSON path.
                    if args.format == "prompt":
                        sys.stdout.write(str(args.prompt_out_path) + "\n")
                else:
                    # If --out was provided and we're in prompt-only mode, treat it as prompt output.
                    if args.format == "prompt" and args.out_path is not None:
                        args.out_path.write_text(prompt, encoding="utf-8")
                        sys.stdout.write(str(args.out_path) + "\n")
                    else:
                        sys.stdout.write(prompt)
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "generate-schema":
        if generate_openapi_schema is None:
            sys.stderr.write("error: Schema generation not available.\n")
            return 1
        try:
            import json
            from pianist.generate_openapi_schema import generate_gemini_schema

            output_dir = args.output_dir or Path(__file__).parent.parent.parent

            if args.format in ("both", "openapi"):
                openapi_schema = generate_openapi_schema()
                openapi_path = output_dir / "schema.openapi.json"
                openapi_path.write_text(json.dumps(openapi_schema, indent=2))
                sys.stdout.write(f"Generated OpenAPI schema: {openapi_path}\n")

            if args.format in ("both", "gemini"):
                gemini_schema = generate_gemini_schema()
                gemini_path = output_dir / "schema.gemini.json"
                gemini_path.write_text(json.dumps(gemini_schema, indent=2))
                sys.stdout.write(f"Generated Gemini-compatible schema: {gemini_path}\n")

        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    raise RuntimeError("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())

