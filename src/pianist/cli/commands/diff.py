"""Diff command: Show changes between compositions."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from ..util import (
    derive_base_name_from_path,
    get_output_base_dir,
    read_text,
    resolve_output_path,
    write_text,
)
from ...diff import diff_compositions, format_diff_json, format_diff_markdown, format_diff_text
from ...parser import parse_composition_from_text


def handle_diff(args) -> int:
    """Handle the diff command."""
    try:
        # Load both compositions
        text1 = read_text(args.input1)
        comp1 = parse_composition_from_text(text1)
        
        text2 = read_text(args.input2)
        comp2 = parse_composition_from_text(text2)
        
        # Compute diff
        diff = diff_compositions(comp1, comp2)
        
        # Format output based on format flag
        if args.format == "json":
            output = format_diff_json(diff)
        elif args.format == "markdown":
            output = format_diff_markdown(diff)
        else:  # text
            # TODO: Implement --musical flag for musical-aware diff
            # For now, --musical is a no-op (musical diff not yet implemented)
            if args.musical:
                sys.stderr.write(
                    "warning: --musical flag is not yet fully implemented. "
                    "Showing standard diff.\n"
                )
            output = format_diff_text(diff, show_preserved=args.show_preserved)
        
        # Write output
        if args.out_path is not None:
            # Determine output directory
            base_name = derive_base_name_from_path(args.input1, "diff-output")
            output_dir = get_output_base_dir(base_name, "diff")
            out_path = resolve_output_path(args.out_path, output_dir, "diff.txt", "diff")
            write_text(out_path, output)
            sys.stdout.write(str(out_path) + "\n")
        else:
            sys.stdout.write(output)
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the diff command parser."""
    parser.add_argument(
        "input1",
        type=Path,
        help="First composition JSON.",
    )
    parser.add_argument(
        "input2",
        type=Path,
        help="Second composition JSON.",
    )
    parser.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output diff file. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--musical",
        action="store_true",
        help="Show musical diff (not just text).",
    )
    parser.add_argument(
        "--show-preserved",
        action="store_true",
        help="Highlight what was preserved.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
