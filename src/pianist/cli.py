from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

from .parser import parse_composition_from_text
from .analyze import analyze_midi, analysis_prompt_template
from .iterate import (
    composition_from_midi,
    composition_to_canonical_json,
    iteration_prompt_template,
    transpose_composition,
)
from .pedal_fix import fix_pedal_patterns
from .schema import PedalEvent
from .renderers.mido_renderer import render_midi_mido
from .gemini import GeminiError, generate_text


# Default output directory for all generated files
_DEFAULT_OUTPUT_DIR = Path("output")


def _get_output_base_dir(base_name: str, command: str) -> Path:
    """
    Get the base output directory for a command run.
    
    Structure: output/<base_name>/<command>/
    
    This groups all operations on the same source material together (by base_name),
    while keeping outputs from different commands separated to avoid filename clashes.
    
    For example:
    - analyze --in song.mid → output/song/analyze/
    - iterate --in song.mid → output/song/iterate/
    - Both are grouped under "song" but separated by command to avoid conflicts.
    
    Args:
        base_name: Base name derived from input file (without extension)
        command: Command name (e.g., "iterate", "analyze", "render", "fix-pedal")
    
    Returns:
        Path to the output directory
    """
    return _DEFAULT_OUTPUT_DIR / base_name / command


def _resolve_output_path(
    provided_path: Path | None,
    default_dir: Path,
    default_filename: str,
    command: str,
) -> Path:
    """
    Resolve an output path, defaulting to the output directory structure if not provided or relative.
    
    If the path is provided and is absolute, use it as-is.
    If the path is provided and is relative, resolve it relative to the default directory.
    If the path is not provided, use default_dir / default_filename.
    
    Args:
        provided_path: The path provided by the user (or None)
        default_dir: The default output directory for this command run
        default_filename: Default filename to use if path is not provided
        command: Command name (for creating default_dir if needed)
    
    Returns:
        Resolved output path
    """
    if provided_path is None:
        return default_dir / default_filename
    
    # If absolute path provided, use as-is
    if provided_path.is_absolute():
        return provided_path
    
    # If relative path provided, resolve relative to default directory
    # But if it already contains directory components, respect them
    if len(provided_path.parts) > 1:
        # User wants a specific subdirectory structure
        return default_dir / provided_path
    else:
        # Just a filename, put it in the default directory
        return default_dir / provided_path.name


def _derive_base_name_from_path(path: Path | None, fallback: str = "output") -> str:
    """
    Derive a base name from an input or output path.
    
    Uses the stem (filename without extension) of the path.
    If path is None, returns the fallback.
    
    For paths within the output directory, extracts the original base name
    to maintain grouping even when using outputs as inputs.
    
    Examples:
    - input/song.mid → "song"
    - output/song/analyze/analysis.json → "song" (extracted from path structure)
    - output/song/iterate/composition.json → "song" (extracted from path structure)
    """
    if path is None:
        return fallback
    
    path = Path(path)
    
    # If the path is already in the output directory, try to extract the original base name
    # This handles cases like: iterate --in output/song/analyze/analysis.json
    # We want to use "song" not "analysis" as the base name
    try:
        # Resolve to absolute path to handle relative paths correctly
        abs_path = path.resolve()
        abs_output_dir = _DEFAULT_OUTPUT_DIR.resolve()
        
        # Check if the path is within the output directory
        try:
            relative_path = abs_path.relative_to(abs_output_dir)
            parts = relative_path.parts
            
            # Our structure is: <base-name>/<command>/<file>
            # So if we have at least 2 parts, the first is the base name
            if len(parts) >= 2:
                # This is output/<base>/<command>/file, extract the base
                return parts[0]
            elif len(parts) == 1:
                # This is output/<base>/file (unusual but possible), use the base
                return parts[0]
        except ValueError:
            # Path is not within output directory, fall through to default
            pass
    except (ValueError, IndexError, OSError):
        # If path resolution fails (e.g., file doesn't exist yet), fall through
        pass
    
    # Default: use the stem of the file
    stem = path.stem
    return stem if stem else fallback


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


def _version_path_if_exists(path: Path, use_timestamp: bool = False) -> Path:
    """
    If the path exists, return a versioned path. Otherwise return the original path.
    
    Versioning strategies:
    - If use_timestamp: append timestamp like .2024-01-15T14-30-25
    - Otherwise: append incremental version like .v2, .v3, etc.
    
    Args:
        path: The original path
        use_timestamp: If True, use timestamp-based versioning; otherwise use incremental
    
    Returns:
        A path that doesn't exist (either original or versioned)
    """
    if not path.exists():
        return path
    
    if use_timestamp:
        # Use timestamp: filename.2024-01-15T14-30-25.ext
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        stem = path.stem
        suffix = path.suffix
        return path.parent / f"{stem}.{timestamp}{suffix}"
    else:
        # Use incremental versioning: filename.v2.ext, filename.v3.ext, etc.
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        # Check if stem already ends with .vN pattern
        import re
        version_match = re.match(r"^(.+)\.v(\d+)$", stem)
        if version_match:
            base_stem = version_match.group(1)
            version_num = int(version_match.group(2))
            next_version = version_num + 1
        else:
            base_stem = stem
            next_version = 2
        
        # Find the next available version
        while True:
            versioned_path = parent / f"{base_stem}.v{next_version}{suffix}"
            if not versioned_path.exists():
                return versioned_path
            next_version += 1


def _write_text(path: Path, text: str, version_if_exists: bool = False) -> Path:
    """
    Write text to a file, optionally versioning if the file exists.
    
    Args:
        path: The target path
        text: The text to write
        version_if_exists: If True and file exists, create a versioned path instead
    
    Returns:
        The actual path used (may be versioned if version_if_exists was True)
    """
    path = Path(path)
    
    if version_if_exists and path.exists():
        path = _version_path_if_exists(path, use_timestamp=False)
    
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _derive_gemini_raw_path(out_path: Path) -> Path:
    # Keep it simple and discoverable: next to the JSON output.
    return out_path.with_name(out_path.name + ".gemini.txt")


def _gemini_prompt_from_template(template: str) -> str:
    """
    The CLI prompt templates are optimized for copy/paste into chat UIs.
    For Gemini CLI calls, we send a single text prompt that includes both the
    "system" and "user" sections explicitly.
    """
    return template.strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pianist",
        description="Convert AI-generated composition JSON into a MIDI file.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Common flags function
    def add_common_flags(cmd_parser):
        """Add common flags to a command parser."""
        cmd_parser.add_argument(
            "--debug",
            action="store_true",
            help="Print a full traceback on errors.",
        )
        cmd_parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Show progress indicators and timing for Gemini API calls.",
        )
        cmd_parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing output files instead of creating versioned copies.",
        )

    render = sub.add_parser("render", help="Parse model output and render a MIDI file.")
    render.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        default=None,
        help="Input text file containing model output. If omitted, reads stdin.",
    )
    render.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        required=True,
        help="Output MIDI path (e.g. out.mid).",
    )
    add_common_flags(render)

    iterate = sub.add_parser(
        "iterate",
        help="Import an existing JSON/MIDI and emit a clean, tweakable composition JSON seed.",
    )
    iterate.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition: a Pianist JSON (or raw LLM output text) OR a .mid/.midi file.",
    )
    iterate.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    iterate.add_argument(
        "--transpose", "-t",
        type=int,
        default=0,
        help="Transpose all notes by this many semitones (can be negative).",
    )
    iterate.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write a ready-to-paste LLM prompt that includes the seed JSON.",
    )
    iterate.add_argument(
        "--gemini",
        action="store_true",
        help="Call Google Gemini to apply instructions to the seed, producing an updated composition JSON.",
    )
    iterate.add_argument(
        "--gemini-model",
        type=str,
        default="gemini-flash-latest",
        help="Gemini model name to use (default: gemini-flash-latest).",
    )
    iterate.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw Gemini response text to this path. Auto-generated if --output is provided.",
    )
    iterate.add_argument(
        "--render",
        action="store_true",
        help="Also render the (possibly Gemini-updated) composition to MIDI.",
    )
    iterate.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    iterate.add_argument(
        "--instructions",
        type=str,
        default="",
        help="Instructions for Gemini to modify the composition (optional, but recommended).",
    )
    add_common_flags(iterate)

    analyze = sub.add_parser(
        "analyze",
        help="Analyze a .mid/.midi file and emit prompt-friendly output.",
    )
    analyze.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input MIDI file (.mid/.midi).",
    )
    analyze.add_argument(
        "--format", "-f",
        choices=["prompt", "json", "both"],
        default="prompt",
        help="Output format: 'prompt' (default), 'json', or 'both'.",
    )
    analyze.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output path for JSON (or prompt if --format prompt and --prompt not provided). If omitted, prints to stdout.",
    )
    analyze.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write the prompt text to this path.",
    )
    analyze.add_argument(
        "--gemini",
        action="store_true",
        help="Call Google Gemini to generate a new composition inspired by the analysis.",
    )
    analyze.add_argument(
        "--gemini-model",
        type=str,
        default="gemini-flash-latest",
        help="Gemini model name to use (default: gemini-flash-latest).",
    )
    analyze.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw Gemini response text to this path. Auto-generated if --output is provided.",
    )
    analyze.add_argument(
        "--render",
        action="store_true",
        help="Also render the Gemini-generated composition to MIDI (only valid with --gemini).",
    )
    analyze.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    analyze.add_argument(
        "--instructions",
        type=str,
        default="",
        help="Instructions for Gemini to compose a new piece (optional, but recommended).",
    )
    add_common_flags(analyze)

    fix_pedal = sub.add_parser(
        "fix-pedal",
        help="Fix incorrect sustain pedal patterns in a composition JSON file.",
    )
    fix_pedal.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input JSON file containing composition.",
    )
    fix_pedal.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, overwrites input file.",
    )
    fix_pedal.add_argument(
        "--render",
        action="store_true",
        help="Also render the fixed composition to MIDI.",
    )
    fix_pedal.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    add_common_flags(fix_pedal)


    args = parser.parse_args(argv)

    if args.cmd == "render":
        try:
            text = _read_text(args.in_path)
            comp = parse_composition_from_text(text)
            
            # Determine output directory and path
            base_name = _derive_base_name_from_path(args.in_path, "render-output")
            output_dir = _get_output_base_dir(base_name, "render")
            out_path = _resolve_output_path(args.out_path, output_dir, "output.mid", "render")
            
            out = render_midi_mido(comp, out_path)
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        sys.stdout.write(str(out) + "\n")
        return 0

    if args.cmd == "fix-pedal":
        try:
            text = _read_text(args.in_path)
            comp = parse_composition_from_text(text)
            
            # Count issues before fix
            issues_before = sum(
                1 for track in comp.tracks
                for ev in track.events
                if isinstance(ev, PedalEvent) and ev.duration == 0 and ev.value == 127
            )
            
            # Fix pedal patterns
            fixed = fix_pedal_patterns(comp)
            
            # Count after fix
            issues_after = sum(
                1 for track in fixed.tracks
                for ev in track.events
                if isinstance(ev, PedalEvent) and ev.duration == 0 and ev.value == 127
            )
            
            # Determine output directory and paths
            base_name = _derive_base_name_from_path(args.in_path, "fix-pedal-output")
            output_dir = _get_output_base_dir(base_name, "fix-pedal")
            
            # If no output path specified, overwrite input file (original behavior)
            if args.out_path is None:
                out_path = args.in_path
            else:
                out_path = _resolve_output_path(args.out_path, output_dir, args.in_path.name, "fix-pedal")
            
            fixed_json = composition_to_canonical_json(fixed)
            _write_text(out_path, fixed_json)
            
            sys.stdout.write(f"Fixed {args.in_path.name}:\n")
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
                    out_midi_path = _resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "fix-pedal"
                    )
                else:
                    out_midi_path = _resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "fix-pedal"
                    )
                render_midi_mido(fixed, out_midi_path)
                sys.stdout.write(f"  Rendered to: {out_midi_path}\n")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
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

            # Determine output directory and paths
            base_name = _derive_base_name_from_path(args.in_path, "iterate-output")
            output_dir = _get_output_base_dir(base_name, "iterate")
            
            # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
            if args.out_path is not None:
                out_json_path = _resolve_output_path(
                    args.out_path, output_dir, "composition.json", "iterate"
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
                    out_midi_path = _resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "iterate"
                    )
                else:
                    out_midi_path = _resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "iterate"
                    )
            else:
                out_midi_path = _resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "iterate"
                ) if args.out_midi_path is not None else None
            prompt_out_path = _resolve_output_path(
                args.prompt_out_path, output_dir, "prompt.txt", "iterate"
            ) if args.prompt_out_path is not None else None

            if args.gemini:
                instructions = (args.instructions or "").strip()
                # Instructions are optional but recommended
                template = iteration_prompt_template(comp, instructions=instructions)
                prompt = _gemini_prompt_from_template(template)

                if prompt_out_path is not None:
                    _write_text(prompt_out_path, template)

                # Determine raw output path (for both reading cached and saving new)
                raw_out_path: Path | None = args.raw_out_path
                if raw_out_path is None and out_json_path is not None:
                    # Default: next to JSON output (only if --out was provided)
                    raw_out_path = _derive_gemini_raw_path(out_json_path)
                elif raw_out_path is not None and not raw_out_path.is_absolute():
                    # Relative path: resolve relative to output directory
                    raw_out_path = output_dir / raw_out_path.name
                
                # Check if we have a cached response
                raw_text: str | None = None
                cached_raw_path: Path | None = None
                if raw_out_path is not None and raw_out_path.exists():
                    if args.verbose:
                        sys.stderr.write(f"Using cached Gemini response from {raw_out_path}\n")
                    raw_text = _read_text(raw_out_path)
                    cached_raw_path = raw_out_path
                
                # If no cached response, call Gemini
                if raw_text is None:
                    raw_text = generate_text(model=args.gemini_model, prompt=prompt, verbose=args.verbose)

                updated = parse_composition_from_text(raw_text)
                out_json = composition_to_canonical_json(updated)

                if args.out_path is None:
                    sys.stdout.write(out_json)
                    # Save raw response if we have it and no JSON output path
                    if raw_text is not None and raw_out_path is not None:
                        _write_text(raw_out_path, raw_text, version_if_exists=not args.overwrite)
                    elif raw_text is not None:
                        # No path to save raw response - show warning
                        sys.stderr.write(
                            "warning: Gemini raw output was not saved. Provide --raw (-r) "
                            "or also provide --output (-o) to enable an automatic default.\n"
                        )
                else:
                    # Version output if file exists and --overwrite not set
                    version_output = not args.overwrite
                    original_path = out_json_path
                    actual_json_path = _write_text(out_json_path, out_json, version_if_exists=version_output)
                    
                    # Handle raw response: if JSON was versioned, version the raw response too
                    if raw_text is not None and raw_out_path is not None:
                        if version_output and original_path != actual_json_path:
                            # JSON was versioned - save raw response with matching version
                            versioned_raw_path = _derive_gemini_raw_path(actual_json_path)
                            _write_text(versioned_raw_path, raw_text, version_if_exists=False)
                        elif cached_raw_path is None:
                            # New response (not cached) - save to original location
                            _write_text(raw_out_path, raw_text, version_if_exists=False)
                        elif cached_raw_path != raw_out_path:
                            # Cached from different location - copy to expected location
                            _write_text(raw_out_path, raw_text, version_if_exists=False)
                        # If cached and JSON not versioned and paths match, raw response already exists
                    
                    sys.stdout.write(str(actual_json_path) + "\n")

                if args.render:
                    render_midi_mido(updated, out_midi_path)
            else:
                out_json = composition_to_canonical_json(comp)

                if args.out_path is None:
                    sys.stdout.write(out_json)
                else:
                    _write_text(out_json_path, out_json)
                    sys.stdout.write(str(out_json_path) + "\n")

                if prompt_out_path is not None:
                    template = iteration_prompt_template(comp, instructions=args.instructions)
                    _write_text(prompt_out_path, template)

                if args.render:
                    render_midi_mido(comp, out_midi_path)
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

            # Determine output directory and paths
            base_name = _derive_base_name_from_path(args.in_path, "analyze-output")
            output_dir = _get_output_base_dir(base_name, "analyze")
            
            # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
            if args.out_path is not None:
                out_json_path = _resolve_output_path(
                    args.out_path, output_dir, "analysis.json", "analyze"
                )
            else:
                out_json_path = None
            
            # For MIDI, auto-generate path if --render is used without explicit path
            if args.render and args.gemini:
                if args.out_midi_path is None:
                    # Auto-generate MIDI path from input/output name
                    if args.out_path is not None:
                        midi_name = args.out_path.stem + ".mid"
                    else:
                        midi_name = args.in_path.stem + ".mid"
                    out_midi_path = _resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "analyze"
                    )
                else:
                    out_midi_path = _resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "analyze"
                    )
            else:
                out_midi_path = _resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "analyze"
                ) if args.out_midi_path is not None else None
            prompt_out_path = _resolve_output_path(
                args.prompt_out_path, output_dir, "prompt.txt", "analyze"
            ) if args.prompt_out_path is not None else None

            if args.gemini:
                instructions = (args.instructions or "").strip()
                # Instructions are optional but recommended
                template = analysis_prompt_template(analysis, instructions=instructions)
                prompt = _gemini_prompt_from_template(template)

                if prompt_out_path is not None:
                    _write_text(prompt_out_path, template)

                # Determine raw output path (for both reading cached and saving new)
                raw_out_path: Path | None = args.raw_out_path
                if raw_out_path is None and out_json_path is not None:
                    # Default: next to JSON output (only if --out was provided)
                    raw_out_path = _derive_gemini_raw_path(out_json_path)
                elif raw_out_path is not None and not raw_out_path.is_absolute():
                    # Relative path: resolve relative to output directory
                    raw_out_path = output_dir / raw_out_path.name
                
                # Check if we have a cached response
                raw_text: str | None = None
                cached_raw_path: Path | None = None
                if raw_out_path is not None and raw_out_path.exists():
                    if args.verbose:
                        sys.stderr.write(f"Using cached Gemini response from {raw_out_path}\n")
                    raw_text = _read_text(raw_out_path)
                    cached_raw_path = raw_out_path
                
                # If no cached response, call Gemini
                if raw_text is None:
                    raw_text = generate_text(model=args.gemini_model, prompt=prompt, verbose=args.verbose)

                comp = parse_composition_from_text(raw_text)
                out_json = composition_to_canonical_json(comp)

                if args.out_path is None:
                    sys.stdout.write(out_json)
                    # Save raw response if we have it and no JSON output path
                    if raw_text is not None and raw_out_path is not None:
                        _write_text(raw_out_path, raw_text, version_if_exists=not args.overwrite)
                    elif raw_text is not None:
                        # No path to save raw response - show warning
                        sys.stderr.write(
                            "warning: Gemini raw output was not saved. Provide --raw (-r) "
                            "or also provide --output (-o) to enable an automatic default.\n"
                        )
                else:
                    # Version output if file exists and --overwrite not set
                    version_output = not args.overwrite
                    original_path = out_json_path
                    actual_json_path = _write_text(out_json_path, out_json, version_if_exists=version_output)
                    
                    # Handle raw response: if JSON was versioned, version the raw response too
                    if raw_text is not None and raw_out_path is not None:
                        if version_output and original_path != actual_json_path:
                            # JSON was versioned - save raw response with matching version
                            versioned_raw_path = _derive_gemini_raw_path(actual_json_path)
                            _write_text(versioned_raw_path, raw_text, version_if_exists=False)
                        elif cached_raw_path is None:
                            # New response (not cached) - save to original location
                            _write_text(raw_out_path, raw_text, version_if_exists=False)
                        elif cached_raw_path != raw_out_path:
                            # Cached from different location - copy to expected location
                            _write_text(raw_out_path, raw_text, version_if_exists=False)
                        # If cached and JSON not versioned and paths match, raw response already exists
                    
                    sys.stdout.write(str(actual_json_path) + "\n")

                if args.render:
                    render_midi_mido(comp, out_midi_path)
                return 0

            if args.render:
                raise ValueError("--render is only supported with --gemini for 'analyze'.")

            if args.format in ("json", "both"):
                out_json = analysis.to_pretty_json()
                if args.out_path is None:
                    sys.stdout.write(out_json)
                else:
                    _write_text(out_json_path, out_json)
                    sys.stdout.write(str(out_json_path) + "\n")

            if args.format in ("prompt", "both"):
                prompt = analysis_prompt_template(analysis, instructions=args.instructions)
                if prompt_out_path is not None:
                    _write_text(prompt_out_path, prompt)
                    # Only print the path if we didn't already print JSON path.
                    if args.format == "prompt":
                        sys.stdout.write(str(prompt_out_path) + "\n")
                else:
                    # If --out was provided and we're in prompt-only mode, treat it as prompt output.
                    if args.format == "prompt" and args.out_path is not None:
                        _write_text(out_json_path, prompt)
                        sys.stdout.write(str(out_json_path) + "\n")
                    else:
                        sys.stdout.write(prompt)
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    raise RuntimeError("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())

