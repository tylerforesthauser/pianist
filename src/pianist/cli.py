from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from .parser import parse_composition_from_text
from .renderers.mido_renderer import render_midi_mido

try:
    from .generate_openapi_schema import generate_openapi_schema
except ImportError:
    # Schema generation may not be available in all environments
    generate_openapi_schema = None


def _read_text(path: Path | None) -> str:
    if path is None:
        return sys.stdin.read()
    try:
        return path.read_text(encoding="utf-8")
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

