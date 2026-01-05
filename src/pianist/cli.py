from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from .parser import parse_composition_from_text
from .renderers.mido_renderer import render_midi_mido


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

    raise RuntimeError("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())

