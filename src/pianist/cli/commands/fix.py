"""Fix command handler."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from ...iterate import composition_to_canonical_json
from ...parser import parse_composition_from_text
from ...pedal_fix import fix_pedal_patterns
from ...renderers.mido_renderer import render_midi_mido
from ...schema import PedalEvent
from ..util import (
    add_common_flags,
    derive_base_name_from_path,
    get_output_base_dir,
    read_text,
    resolve_output_path,
    write_text,
)


def setup_parser(subparsers) -> None:
    """Setup the fix command parser."""
    fix = subparsers.add_parser(
        "fix",
        help="Fix composition issues (pedal patterns, etc.).",
    )
    fix.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input JSON file containing composition.",
    )
    fix.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, overwrites input file.",
    )
    fix.add_argument(
        "--pedal",
        action="store_true",
        help="Fix incorrect sustain pedal patterns.",
    )
    fix.add_argument(
        "--all",
        action="store_true",
        help="Fix all available issues.",
    )
    fix.add_argument(
        "--render",
        action="store_true",
        help="Also render the fixed composition to MIDI.",
    )
    fix.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    add_common_flags(fix)


def handle(args: argparse.Namespace) -> int:
    """Handle the fix command."""
    try:
        # Determine which fixes to apply
        fix_pedal_flag = args.pedal or args.all
        
        if not fix_pedal_flag:
            raise ValueError("No fix specified. Use --pedal, --all, or other fix flags.")
        
        text = read_text(args.in_path)
        comp = parse_composition_from_text(text)
        
        issues_before = 0
        if fix_pedal_flag:
            issues_before = sum(
                1 for track in comp.tracks
                for ev in track.events
                if isinstance(ev, PedalEvent) and ev.duration == 0 and ev.value == 127
            )
        
        # Apply fixes
        fixed = comp
        if fix_pedal_flag:
            fixed = fix_pedal_patterns(fixed)
        
        # Count after fix
        issues_after = 0
        if fix_pedal_flag:
            issues_after = sum(
                1 for track in fixed.tracks
                for ev in track.events
                if isinstance(ev, PedalEvent) and ev.duration == 0 and ev.value == 127
            )
        
        # Determine output directory and paths
        base_name = derive_base_name_from_path(args.in_path, "fix-output")
        output_dir = get_output_base_dir(base_name, "fix")
        
        # If no output path specified, overwrite input file (original behavior)
        if args.out_path is None:
            out_path = args.in_path
        else:
            out_path = resolve_output_path(args.out_path, output_dir, args.in_path.name)
        
        fixed_json = composition_to_canonical_json(fixed)
        write_text(out_path, fixed_json)
        
        sys.stdout.write(f"Fixed {args.in_path.name}:\n")
        if fix_pedal_flag:
            sys.stdout.write(f"  Pedal issues before: {issues_before}\n")
            sys.stdout.write(f"  Pedal issues after: {issues_after}\n")
        sys.stdout.write(f"  Saved to: {out_path}\n")
        
        # Optionally render to MIDI
        if args.render:
            if args.out_midi_path is None:
                # Auto-generate MIDI path from input/output name
                if args.out_path is not None:
                    midi_name = args.out_path.stem + ".mid"
                else:
                    midi_name = args.in_path.stem + "_fixed.mid"
                out_midi_path = resolve_output_path(
                    Path(midi_name), output_dir, "composition.mid"
                )
            else:
                out_midi_path = resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid"
                )
            render_midi_mido(fixed, out_midi_path)
            sys.stdout.write(f"  Rendered to: {out_midi_path}\n")
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0
