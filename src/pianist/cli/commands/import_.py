"""Import command handler."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from ...iterate import composition_from_midi, composition_to_canonical_json
from ..util import (
    add_common_flags,
    derive_base_name_from_path,
    get_output_base_dir,
    resolve_output_path,
    write_text,
)


def setup_parser(subparsers) -> None:
    """Setup the import command parser."""
    import_cmd = subparsers.add_parser(
        "import",
        help="Import a MIDI file and convert it to Pianist JSON format.",
    )
    import_cmd.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input MIDI file (.mid/.midi).",
    )
    import_cmd.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    add_common_flags(import_cmd)


def handle(args: argparse.Namespace) -> int:
    """Handle the import command."""
    try:
        suffix = args.in_path.suffix.lower()
        if suffix not in (".mid", ".midi"):
            raise ValueError("Input must be a .mid or .midi file for import.")
        
        comp = composition_from_midi(args.in_path)
        
        # Determine output directory and paths
        base_name = derive_base_name_from_path(args.in_path, "import-output")
        output_dir = get_output_base_dir(base_name, "import")
        
        if args.out_path is not None:
            out_json_path = resolve_output_path(
                args.out_path, output_dir, "composition.json"
            )
        else:
            out_json_path = None
        
        out_json = composition_to_canonical_json(comp)
        
        if args.out_path is None:
            sys.stdout.write(out_json)
        else:
            write_text(out_json_path, out_json)
            sys.stdout.write(str(out_json_path) + "\n")
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0
