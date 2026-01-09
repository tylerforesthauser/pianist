"""Render command: Parse model output and render a MIDI file."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from ...parser import parse_composition_from_text
from ...renderers.mido_renderer import render_midi_mido
from ..util import (
    derive_base_name_from_path,
    get_output_base_dir,
    read_text,
    resolve_output_path,
)


def handle_render(args) -> int:
    """Handle the render command."""
    try:
        text = read_text(args.in_path)
        comp = parse_composition_from_text(text)

        # Determine output directory and path
        base_name = derive_base_name_from_path(args.in_path, "render-output")
        output_dir = get_output_base_dir(base_name, "render")
        out_path = resolve_output_path(args.out_path, output_dir, "output.mid", "render")

        out = render_midi_mido(comp, out_path)
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    sys.stdout.write(str(out) + "\n")
    return 0


def setup_parser(parser):
    """Set up the render command parser."""
    parser.add_argument(
        "-i",
        "--input",
        dest="in_path",
        type=Path,
        default=None,
        help="Input text file containing model output. If omitted, reads stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="out_path",
        type=Path,
        required=True,
        help="Output MIDI path (e.g. out.mid).",
    )
