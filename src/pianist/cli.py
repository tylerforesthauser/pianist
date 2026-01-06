from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

from .parser import parse_composition_from_text
from .analyze import analyze_midi, analysis_prompt_template
from .musical_analysis import (
    analyze_composition as analyze_composition_musical,
    MUSIC21_AVAILABLE,
)
from .iterate import (
    composition_from_midi,
    composition_to_canonical_json,
    generation_prompt_template,
    iteration_prompt_template,
    transpose_composition,
)
from .pedal_fix import fix_pedal_patterns
from .schema import PedalEvent
from .renderers.mido_renderer import render_midi_mido
from .gemini import GeminiError, generate_text
from .diff import diff_compositions, format_diff_text, format_diff_json, format_diff_markdown
from .annotations import (
    add_key_idea,
    add_expansion_point,
    set_development_direction,
    add_to_preserve_list,
)
from .schema import MusicalIntent, KeyIdea, ExpansionPoint


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
    - import --in song.mid → output/song/import/
    - Both are grouped under "song" but separated by command to avoid conflicts.
    
    Args:
        base_name: Base name derived from input file (without extension)
        command: Command name (e.g., "import", "modify", "analyze", "render", "fix")
    
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
    - output/song/modify/composition.json → "song" (extracted from path structure)
    """
    if path is None:
        return fallback
    
    path = Path(path)
    
    # If the path is already in the output directory, try to extract the original base name
    # This handles cases like: modify -i output/song/analyze/analysis.json
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
        description="Framework for human-AI collaboration in musical composition. Convert between JSON and MIDI, analyze compositions, and expand incomplete works.",
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
            help="Show progress indicators and timing for AI API calls.",
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

    # Import command: Import external formats (MIDI, etc.) to JSON
    import_cmd = sub.add_parser(
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

    # Modify command: Modify existing compositions (transpose, AI modification, etc.)
    modify = sub.add_parser(
        "modify",
        help="Modify an existing composition (transpose, fix, or modify with AI).",
    )
    modify.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON (or raw LLM output text).",
    )
    modify.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    modify.add_argument(
        "--transpose", "-t",
        type=int,
        default=0,
        help="Transpose all notes by this many semitones (can be negative).",
    )
    modify.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write a ready-to-paste LLM prompt that includes the composition JSON.",
    )
    modify.add_argument(
        "--provider",
        type=str,
        choices=["gemini"],
        default=None,
        help="AI provider to use for modification. If omitted, only generates a prompt template (use --prompt to save it).",
    )
    modify.add_argument(
        "--model",
        type=str,
        default="gemini-flash-latest",
        help="Model name to use with the provider (default: gemini-flash-latest). Only used with --provider.",
    )
    modify.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
    modify.add_argument(
        "--render",
        action="store_true",
        help="Also render the (possibly AI-modified) composition to MIDI.",
    )
    modify.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    modify.add_argument(
        "--instructions",
        type=str,
        default="",
        help="Instructions for modifying the composition (optional, but recommended when using --provider).",
    )
    add_common_flags(modify)

    analyze = sub.add_parser(
        "analyze",
        help="Analyze a .mid/.midi file and emit prompt-friendly output.",
    )
    analyze.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input file: MIDI (.mid/.midi) or JSON composition (.json).",
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
        "--provider",
        type=str,
        choices=["gemini"],
        default=None,
        help="AI provider to use for generating a new composition. If omitted, only generates analysis/prompt.",
    )
    analyze.add_argument(
        "--model",
        type=str,
        default="gemini-flash-latest",
        help="Model name to use with the provider (default: gemini-flash-latest). Only used with --provider.",
    )
    analyze.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
    analyze.add_argument(
        "--render",
        action="store_true",
        help="Also render the AI-generated composition to MIDI (only valid with --provider).",
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
        help="Instructions for composing a new piece (optional, but recommended when using --provider).",
    )
    add_common_flags(analyze)

    # Fix command: Fix composition issues
    fix = sub.add_parser(
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

    # Annotate command: Mark musical intent
    annotate = sub.add_parser(
        "annotate",
        help="Mark musical intent (key ideas, expansion points, etc.).",
    )
    annotate.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON.",
    )
    annotate.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output annotated JSON path. If omitted, overwrites input file.",
    )
    annotate.add_argument(
        "--auto-detect",
        action="store_true",
        help="Automatically detect and annotate key ideas.",
    )
    annotate.add_argument(
        "--show",
        action="store_true",
        help="Show current annotations without modifying.",
    )
    annotate.add_argument(
        "--mark-motif",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a motif. Format: --mark-motif '0-4' 'Opening motif'",
    )
    annotate.add_argument(
        "--mark-phrase",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a phrase. Format: --mark-phrase '0-16' 'Opening phrase'",
    )
    annotate.add_argument(
        "--mark-harmonic-progression",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a harmonic progression. Format: --mark-harmonic-progression '0-8' 'I-V-vi-IV'",
    )
    annotate.add_argument(
        "--mark-rhythmic-pattern",
        type=str,
        nargs=2,
        metavar=("START-DURATION", "DESCRIPTION"),
        help="Mark a rhythmic pattern. Format: --mark-rhythmic-pattern '0-2' 'Syncopated rhythm'",
    )
    annotate.add_argument(
        "--idea-id",
        type=str,
        default=None,
        help="ID for the key idea (auto-generated if not provided).",
    )
    annotate.add_argument(
        "--importance",
        choices=["high", "medium", "low"],
        default="medium",
        help="Importance level for the key idea (default: medium).",
    )
    annotate.add_argument(
        "--development-direction",
        type=str,
        default=None,
        help="How to develop the key idea (e.g., 'expand and vary', 'preserve exactly').",
    )
    annotate.add_argument(
        "--mark-expansion",
        type=str,
        metavar="SECTION",
        help="Mark an expansion point for a section.",
    )
    annotate.add_argument(
        "--target-length",
        type=float,
        default=None,
        help="Target length in beats for expansion point (required with --mark-expansion).",
    )
    annotate.add_argument(
        "--development-strategy",
        type=str,
        default=None,
        help="Development strategy for expansion (required with --mark-expansion).",
    )
    annotate.add_argument(
        "--preserve",
        type=str,
        default=None,
        help="Comma-separated list of idea IDs or characteristics to preserve.",
    )
    annotate.add_argument(
        "--overall-direction",
        type=str,
        default=None,
        help="Overall development direction for the composition.",
    )
    add_common_flags(annotate)

    # Expand command: Expand incomplete compositions
    expand = sub.add_parser(
        "expand",
        help="Expand an incomplete composition to a complete work.",
    )
    expand.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON (preferably annotated).",
    )
    expand.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output expanded JSON path. If omitted, prints to stdout.",
    )
    expand.add_argument(
        "--target-length",
        type=float,
        required=True,
        help="Target length in beats.",
    )
    expand.add_argument(
        "--provider",
        type=str,
        choices=["gemini"],
        default=None,
        help="AI provider to use for expansion. If omitted, only generates expansion strategy.",
    )
    expand.add_argument(
        "--model",
        type=str,
        default="gemini-flash-latest",
        help="Model name to use with the provider (default: gemini-flash-latest). Only used with --provider.",
    )
    expand.add_argument(
        "--preserve-motifs",
        action="store_true",
        help="Preserve all marked motifs.",
    )
    expand.add_argument(
        "--preserve",
        type=str,
        default=None,
        help="Comma-separated list of idea IDs to preserve.",
    )
    expand.add_argument(
        "--validate",
        action="store_true",
        help="Validate expansion quality before returning.",
    )
    expand.add_argument(
        "--render",
        action="store_true",
        help="Also render the expanded composition to MIDI.",
    )
    expand.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    expand.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
    add_common_flags(expand)

    # Diff command: Show changes between compositions
    diff = sub.add_parser(
        "diff",
        help="Show what changed between two compositions.",
    )
    diff.add_argument(
        "input1",
        type=Path,
        help="First composition JSON.",
    )
    diff.add_argument(
        "input2",
        type=Path,
        help="Second composition JSON.",
    )
    diff.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output diff file. If omitted, prints to stdout.",
    )
    diff.add_argument(
        "--musical",
        action="store_true",
        help="Show musical diff (not just text).",
    )
    diff.add_argument(
        "--show-preserved",
        action="store_true",
        help="Highlight what was preserved.",
    )
    diff.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    add_common_flags(diff)

    generate = sub.add_parser(
        "generate",
        help="Generate a new composition from a text description.",
    )
    generate.add_argument(
        "description",
        nargs="?",
        type=str,
        default=None,
        help="Text description of the composition to generate. If omitted, reads from stdin.",
    )
    generate.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    generate.add_argument(
        "--provider",
        type=str,
        choices=["gemini"],
        default=None,
        help="AI provider to use for generation. If omitted, only generates a prompt template (use --prompt to save it).",
    )
    generate.add_argument(
        "--model",
        type=str,
        default="gemini-flash-latest",
        help="Model name to use with the provider (default: gemini-flash-latest). Only used with --provider.",
    )
    generate.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
    generate.add_argument(
        "--render",
        action="store_true",
        help="Also render the generated composition to MIDI (only valid with --provider).",
    )
    generate.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from output name if --render is used without this flag.",
    )
    generate.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write a ready-to-paste LLM prompt to this path.",
    )
    add_common_flags(generate)


    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse raises SystemExit on errors, convert to return code
        return e.code if e.code is not None else 1

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

    if args.cmd == "import":
        try:
            suffix = args.in_path.suffix.lower()
            if suffix not in (".mid", ".midi"):
                raise ValueError("Input must be a .mid or .midi file for import.")
            
            comp = composition_from_midi(args.in_path)
            
            # Determine output directory and paths
            base_name = _derive_base_name_from_path(args.in_path, "import-output")
            output_dir = _get_output_base_dir(base_name, "import")
            
            if args.out_path is not None:
                out_json_path = _resolve_output_path(
                    args.out_path, output_dir, "composition.json", "import"
                )
            else:
                out_json_path = None
            
            out_json = composition_to_canonical_json(comp)
            
            if args.out_path is None:
                sys.stdout.write(out_json)
            else:
                _write_text(out_json_path, out_json)
                sys.stdout.write(str(out_json_path) + "\n")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "modify":
        try:
            # Treat as model output / JSON text file (parse_composition_from_text is lenient).
            text = _read_text(args.in_path)
            comp = parse_composition_from_text(text)

            if args.transpose:
                comp = transpose_composition(comp, args.transpose)

            # Determine output directory and paths
            base_name = _derive_base_name_from_path(args.in_path, "modify-output")
            output_dir = _get_output_base_dir(base_name, "modify")
            
            # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
            if args.out_path is not None:
                out_json_path = _resolve_output_path(
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
                    out_midi_path = _resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "modify"
                    )
                else:
                    out_midi_path = _resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "modify"
                    )
            else:
                out_midi_path = _resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "modify"
                ) if args.out_midi_path is not None else None
            prompt_out_path = _resolve_output_path(
                args.prompt_out_path, output_dir, "prompt.txt", "modify"
            ) if args.prompt_out_path is not None else None

            if args.provider:
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
                        sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                    raw_text = _read_text(raw_out_path)
                    cached_raw_path = raw_out_path
                
                # If no cached response, call AI provider
                if raw_text is None:
                    if args.provider == "gemini":
                        raw_text = generate_text(model=args.model, prompt=prompt, verbose=args.verbose)
                    else:
                        raise ValueError(f"Unsupported provider: {args.provider}")

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
                            "warning: AI raw output was not saved. Provide --raw (-r) "
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

    if args.cmd == "fix":
        try:
            # Determine which fixes to apply
            fix_pedal_flag = args.pedal or args.all
            
            if not fix_pedal_flag:
                raise ValueError("No fix specified. Use --pedal, --all, or other fix flags.")
            
            text = _read_text(args.in_path)
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
            base_name = _derive_base_name_from_path(args.in_path, "fix-output")
            output_dir = _get_output_base_dir(base_name, "fix")
            
            # If no output path specified, overwrite input file (original behavior)
            if args.out_path is None:
                out_path = args.in_path
            else:
                out_path = _resolve_output_path(args.out_path, output_dir, args.in_path.name, "fix")
            
            fixed_json = composition_to_canonical_json(fixed)
            _write_text(out_path, fixed_json)
            
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
                    out_midi_path = _resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "fix"
                    )
                else:
                    out_midi_path = _resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "fix"
                    )
                render_midi_mido(fixed, out_midi_path)
                sys.stdout.write(f"  Rendered to: {out_midi_path}\n")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "annotate":
        try:
            # Load composition
            text = _read_text(args.in_path)
            comp = parse_composition_from_text(text)
            
            # Determine output directory and paths
            base_name = _derive_base_name_from_path(args.in_path, "annotate-output")
            output_dir = _get_output_base_dir(base_name, "annotate")
            
            # If --show, just display current annotations and exit
            if args.show:
                if comp.musical_intent is not None:
                    import json
                    intent_dict = comp.musical_intent.model_dump()
                    intent_json = json.dumps(intent_dict, indent=2)
                    sys.stdout.write("Current annotations:\n")
                    sys.stdout.write(intent_json + "\n")
                else:
                    sys.stdout.write("No annotations found in composition.\n")
                return 0
            
            annotated_comp = comp
            
            # For --auto-detect, use analysis module (when implemented)
            if args.auto_detect:
                # TODO: Implement auto-detection using analysis module
                sys.stderr.write(
                    "warning: Auto-detection not yet fully implemented. "
                    "Analysis module is required for automatic detection.\n"
                )
                # For now, just copy the composition
            else:
                # Process manual annotation flags
                annotations_added = False
                
                # Parse START-DURATION format (e.g., "0-4" means start=0, duration=4)
                def parse_time_range(time_str: str) -> tuple[float, float]:
                    try:
                        parts = time_str.split("-")
                        if len(parts) != 2:
                            raise ValueError(f"Invalid time range format: {time_str}. Expected 'START-DURATION'")
                        start = float(parts[0])
                        duration = float(parts[1])
                        if duration <= 0:
                            raise ValueError(f"Duration must be positive: {duration}")
                        return start, duration
                    except ValueError as e:
                        raise ValueError(f"Invalid time range '{time_str}': {e}") from e
                
                # Generate idea ID if not provided
                idea_counter = 1
                def generate_idea_id(idea_type: str) -> str:
                    nonlocal idea_counter
                    existing_ids = set()
                    if annotated_comp.musical_intent:
                        existing_ids = {idea.id for idea in annotated_comp.musical_intent.key_ideas}
                    while True:
                        candidate = f"{idea_type}_{idea_counter}"
                        if candidate not in existing_ids:
                            idea_counter += 1
                            return candidate
                        idea_counter += 1
                
                # Mark motif
                if args.mark_motif:
                    start, duration = parse_time_range(args.mark_motif[0])
                    description = args.mark_motif[1]
                    idea_id = args.idea_id or generate_idea_id("motif")
                    annotated_comp = add_key_idea(
                        annotated_comp,
                        idea_id=idea_id,
                        idea_type="motif",
                        start=start,
                        duration=duration,
                        description=description,
                        importance=args.importance,
                        development_direction=args.development_direction
                    )
                    annotations_added = True
                    sys.stdout.write(f"Marked motif '{idea_id}' at {start}-{start+duration} beats\n")
                
                # Mark phrase
                if args.mark_phrase:
                    start, duration = parse_time_range(args.mark_phrase[0])
                    description = args.mark_phrase[1]
                    idea_id = args.idea_id or generate_idea_id("phrase")
                    annotated_comp = add_key_idea(
                        annotated_comp,
                        idea_id=idea_id,
                        idea_type="phrase",
                        start=start,
                        duration=duration,
                        description=description,
                        importance=args.importance,
                        development_direction=args.development_direction
                    )
                    annotations_added = True
                    sys.stdout.write(f"Marked phrase '{idea_id}' at {start}-{start+duration} beats\n")
                
                # Mark harmonic progression
                if args.mark_harmonic_progression:
                    start, duration = parse_time_range(args.mark_harmonic_progression[0])
                    description = args.mark_harmonic_progression[1]
                    idea_id = args.idea_id or generate_idea_id("harmonic_progression")
                    annotated_comp = add_key_idea(
                        annotated_comp,
                        idea_id=idea_id,
                        idea_type="harmonic_progression",
                        start=start,
                        duration=duration,
                        description=description,
                        importance=args.importance,
                        development_direction=args.development_direction
                    )
                    annotations_added = True
                    sys.stdout.write(f"Marked harmonic progression '{idea_id}' at {start}-{start+duration} beats\n")
                
                # Mark rhythmic pattern
                if args.mark_rhythmic_pattern:
                    start, duration = parse_time_range(args.mark_rhythmic_pattern[0])
                    description = args.mark_rhythmic_pattern[1]
                    idea_id = args.idea_id or generate_idea_id("rhythmic_pattern")
                    annotated_comp = add_key_idea(
                        annotated_comp,
                        idea_id=idea_id,
                        idea_type="rhythmic_pattern",
                        start=start,
                        duration=duration,
                        description=description,
                        importance=args.importance,
                        development_direction=args.development_direction
                    )
                    annotations_added = True
                    sys.stdout.write(f"Marked rhythmic pattern '{idea_id}' at {start}-{start+duration} beats\n")
                
                # Mark expansion point
                if args.mark_expansion:
                    if args.target_length is None:
                        raise ValueError("--target-length is required with --mark-expansion")
                    if args.development_strategy is None:
                        raise ValueError("--development-strategy is required with --mark-expansion")
                    
                    # Calculate current length
                    current_length = 0.0
                    for track in annotated_comp.tracks:
                        for event in track.events:
                            event_end = event.start + (getattr(event, "duration", 0.0))
                            current_length = max(current_length, event_end)
                    
                    preserve_list = None
                    if args.preserve:
                        preserve_list = [id.strip() for id in args.preserve.split(",")]
                    
                    annotated_comp = add_expansion_point(
                        annotated_comp,
                        section=args.mark_expansion,
                        current_length=current_length,
                        suggested_length=args.target_length,
                        development_strategy=args.development_strategy,
                        preserve=preserve_list
                    )
                    annotations_added = True
                    sys.stdout.write(
                        f"Marked expansion point for section '{args.mark_expansion}': "
                        f"{current_length:.2f} → {args.target_length:.2f} beats\n"
                    )
                
                # Set overall development direction
                if args.overall_direction:
                    annotated_comp = set_development_direction(annotated_comp, args.overall_direction)
                    annotations_added = True
                    sys.stdout.write(f"Set overall development direction\n")
                
                # Add to preserve list
                if args.preserve and not args.mark_expansion:  # Only if not used for expansion point
                    preserve_items = [item.strip() for item in args.preserve.split(",")]
                    annotated_comp = add_to_preserve_list(annotated_comp, preserve_items)
                    annotations_added = True
                    sys.stdout.write(f"Added to preserve list: {', '.join(preserve_items)}\n")
                
                if not annotations_added and not args.auto_detect:
                    sys.stderr.write(
                        "warning: No annotations specified. Use --mark-motif, --mark-expansion, "
                        "--auto-detect, or other annotation flags.\n"
                    )
            
            # Determine output path
            if args.out_path is None:
                # Default: overwrite input file
                out_path = args.in_path
            else:
                out_path = _resolve_output_path(args.out_path, output_dir, args.in_path.name, "annotate")
            
            # Save annotated composition
            annotated_json = composition_to_canonical_json(annotated_comp)
            _write_text(out_path, annotated_json)
            sys.stdout.write(f"Saved to: {out_path}\n")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "expand":
        try:
            # Load composition
            text = _read_text(args.in_path)
            comp = parse_composition_from_text(text)
            
            # Calculate current length
            current_length = 0.0
            for track in comp.tracks:
                for event in track.events:
                    event_end = event.start + (getattr(event, "duration", 0.0))
                    current_length = max(current_length, event_end)
            
            if args.verbose:
                sys.stderr.write(f"Current length: {current_length:.2f} beats\n")
                sys.stderr.write(f"Target length: {args.target_length:.2f} beats\n")
                sys.stderr.write(f"Expansion needed: {args.target_length - current_length:.2f} beats\n")
            
            # If no provider, just show expansion strategy (when analysis module is ready)
            if args.provider is None:
                sys.stderr.write(
                    "warning: Expansion without AI provider is not yet fully implemented. "
                    "Analysis module and expansion strategies are required.\n"
                )
                sys.stderr.write(
                    f"Current: {current_length:.2f} beats, Target: {args.target_length:.2f} beats\n"
                )
                # For now, just copy the composition
                expanded_comp = comp
            else:
                # Generate expansion prompt with analysis
                # Perform musical analysis to inform expansion
                if MUSIC21_AVAILABLE:
                    try:
                        musical_analysis = analyze_composition_musical(comp)
                        
                        # Build expansion instructions with analysis
                        expansion_instructions = (
                            f"Expand this composition from {current_length:.2f} beats to {args.target_length:.2f} beats. "
                            f"Preserve the original musical ideas and develop them naturally. "
                            f"Maintain the same style, tempo ({comp.bpm} bpm), and key signature ({comp.key_signature or 'original'}).\n\n"
                        )
                        
                        # Add analysis results
                        if musical_analysis.motifs:
                            expansion_instructions += f"Detected motifs ({len(musical_analysis.motifs)}): "
                            motif_descriptions = [f"motif at {m.start:.1f}-{m.start+m.duration:.1f} beats (pitches: {m.pitches})" for m in musical_analysis.motifs[:3]]
                            expansion_instructions += ", ".join(motif_descriptions)
                            if len(musical_analysis.motifs) > 3:
                                expansion_instructions += f" (and {len(musical_analysis.motifs)-3} more)"
                            expansion_instructions += ". Develop and vary these motifs throughout the expansion.\n\n"
                        
                        if musical_analysis.phrases:
                            expansion_instructions += f"Detected phrases ({len(musical_analysis.phrases)}): "
                            phrase_descriptions = [f"phrase at {p.start:.1f}-{p.start+p.duration:.1f} beats" for p in musical_analysis.phrases[:3]]
                            expansion_instructions += ", ".join(phrase_descriptions)
                            if len(musical_analysis.phrases) > 3:
                                expansion_instructions += f" (and {len(musical_analysis.phrases)-3} more)"
                            expansion_instructions += ". Extend these phrases naturally and add complementary material.\n\n"
                        
                        if musical_analysis.harmonic_progression and musical_analysis.harmonic_progression.chords:
                            expansion_instructions += f"Harmonic analysis: {len(musical_analysis.harmonic_progression.chords)} chords detected. "
                            if musical_analysis.harmonic_progression.key:
                                expansion_instructions += f"Key: {musical_analysis.harmonic_progression.key}. "
                            expansion_instructions += "Maintain harmonic coherence while expanding.\n\n"
                        
                        if musical_analysis.form:
                            expansion_instructions += f"Musical form: {musical_analysis.form}. Preserve this form structure while expanding sections.\n\n"
                        
                        # Add expansion suggestions
                        if musical_analysis.expansion_suggestions:
                            expansion_instructions += "Expansion strategies:\n"
                            for suggestion in musical_analysis.expansion_suggestions[:3]:
                                expansion_instructions += f"- {suggestion}\n"
                            expansion_instructions += "\n"
                        
                    except Exception as e:
                        if args.verbose:
                            sys.stderr.write(f"warning: Musical analysis failed: {e}. Using basic expansion instructions.\n")
                        # Fall back to basic instructions
                        expansion_instructions = (
                            f"Expand this composition from {current_length:.2f} beats to {args.target_length:.2f} beats. "
                            f"Preserve the original musical ideas and develop them naturally. "
                            f"Maintain the same style, tempo ({comp.bpm} bpm), and key signature ({comp.key_signature or 'original'})."
                        )
                else:
                    # No music21 available, use basic instructions
                    expansion_instructions = (
                        f"Expand this composition from {current_length:.2f} beats to {args.target_length:.2f} beats. "
                        f"Preserve the original musical ideas and develop them naturally. "
                        f"Maintain the same style, tempo ({comp.bpm} bpm), and key signature ({comp.key_signature or 'original'})."
                    )
                
                if args.preserve_motifs:
                    expansion_instructions += " Preserve all marked motifs and develop them throughout."
                
                if args.preserve:
                    preserve_ids = [id.strip() for id in args.preserve.split(",")]
                    expansion_instructions += f" Preserve these specific ideas: {', '.join(preserve_ids)}."
                
                template = iteration_prompt_template(comp, instructions=expansion_instructions)
                prompt = _gemini_prompt_from_template(template)
                
                # Determine output directory and paths
                base_name = _derive_base_name_from_path(args.in_path, "expand-output")
                output_dir = _get_output_base_dir(base_name, "expand")
                
                if args.out_path is not None:
                    out_json_path = _resolve_output_path(
                        args.out_path, output_dir, "composition.json", "expand"
                    )
                else:
                    out_json_path = None
                
                # Determine raw output path
                raw_out_path: Path | None = args.raw_out_path
                if raw_out_path is None and out_json_path is not None:
                    raw_out_path = _derive_gemini_raw_path(out_json_path)
                elif raw_out_path is not None and not raw_out_path.is_absolute():
                    raw_out_path = output_dir / raw_out_path.name
                
                # Check for cached response
                raw_text: str | None = None
                cached_raw_path: Path | None = None
                if raw_out_path is not None and raw_out_path.exists():
                    if args.verbose:
                        sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                    raw_text = _read_text(raw_out_path)
                    cached_raw_path = raw_out_path
                
                # Call AI provider if no cached response
                if raw_text is None:
                    if args.provider == "gemini":
                        if args.verbose:
                            sys.stderr.write("Calling AI provider for expansion...\n")
                        raw_text = generate_text(model=args.model, prompt=prompt, verbose=args.verbose)
                    else:
                        raise ValueError(f"Unsupported provider: {args.provider}")
                
                # Parse expanded composition
                expanded_comp = parse_composition_from_text(raw_text)
                
                # Calculate expanded length
                expanded_length = 0.0
                for track in expanded_comp.tracks:
                    for event in track.events:
                        event_end = event.start + (getattr(event, "duration", 0.0))
                        expanded_length = max(expanded_length, event_end)
                
                if args.verbose:
                    sys.stderr.write(f"Expanded length: {expanded_length:.2f} beats\n")
                
                # Validate if requested
                if args.validate:
                    # TODO: Implement validation using validation module
                    sys.stderr.write(
                        "warning: Validation not yet fully implemented. "
                        "Validation module is required.\n"
                    )
                    # Basic check: did it expand?
                    if expanded_length < current_length:
                        sys.stderr.write(
                            "warning: Expanded composition is shorter than original. "
                            "This may indicate an issue.\n"
                        )
                    elif expanded_length < args.target_length * 0.9:
                        sys.stderr.write(
                            f"warning: Expanded composition ({expanded_length:.2f} beats) "
                            f"is significantly shorter than target ({args.target_length:.2f} beats).\n"
                        )
                
                # Save raw response
                if raw_text is not None and raw_out_path is not None:
                    if cached_raw_path is None:
                        _write_text(raw_out_path, raw_text, version_if_exists=not args.overwrite)
                
                # Save expanded composition
                expanded_json = composition_to_canonical_json(expanded_comp)
                
                if args.out_path is None:
                    sys.stdout.write(expanded_json)
                else:
                    version_output = not args.overwrite
                    actual_json_path = _write_text(out_json_path, expanded_json, version_if_exists=version_output)
                    sys.stdout.write(str(actual_json_path) + "\n")
                
                # Render if requested
                if args.render:
                    if args.out_midi_path is None:
                        if args.out_path is not None:
                            midi_name = args.out_path.stem + ".mid"
                        else:
                            midi_name = args.in_path.stem + "_expanded.mid"
                        out_midi_path = _resolve_output_path(
                            Path(midi_name), output_dir, "composition.mid", "expand"
                        )
                    else:
                        out_midi_path = _resolve_output_path(
                            args.out_midi_path, output_dir, "composition.mid", "expand"
                        )
                    render_midi_mido(expanded_comp, out_midi_path)
                    sys.stdout.write(f"Rendered to: {out_midi_path}\n")
                    return 0
                
                return 0
            
            # No provider case: save unchanged composition
            expanded_json = composition_to_canonical_json(expanded_comp)
            if args.out_path is None:
                sys.stdout.write(expanded_json)
            else:
                out_path = _resolve_output_path(args.out_path, output_dir, args.in_path.name, "expand")
                _write_text(out_path, expanded_json)
                sys.stdout.write(str(out_path) + "\n")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "diff":
        try:
            # Load both compositions
            text1 = _read_text(args.input1)
            comp1 = parse_composition_from_text(text1)
            
            text2 = _read_text(args.input2)
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
                base_name = _derive_base_name_from_path(args.input1, "diff-output")
                output_dir = _get_output_base_dir(base_name, "diff")
                out_path = _resolve_output_path(args.out_path, output_dir, "diff.txt", "diff")
                _write_text(out_path, output)
                sys.stdout.write(str(out_path) + "\n")
            else:
                sys.stdout.write(output)
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    if args.cmd == "analyze":
        try:
            suffix = args.in_path.suffix.lower()
            
            # Handle JSON input (composition analysis)
            if suffix == ".json":
                if not MUSIC21_AVAILABLE:
                    sys.stderr.write(
                        "warning: music21 is not installed. Musical analysis requires music21. "
                        "Install with: pip install music21\n"
                    )
                    return 1
                
                # Load composition from JSON
                text = _read_text(args.in_path)
                comp = parse_composition_from_text(text)
                
                # Perform musical analysis
                musical_analysis = analyze_composition_musical(comp)
                
                # Format analysis results as JSON
                import json
                analysis_result = {
                    "source": str(args.in_path),
                    "composition": {
                        "title": comp.title,
                        "bpm": comp.bpm,
                        "key_signature": comp.key_signature,
                        "time_signature": f"{comp.time_signature.numerator}/{comp.time_signature.denominator}",
                    },
                    "analysis": {
                        "motifs": [
                            {
                                "start": m.start,
                                "duration": m.duration,
                                "pitches": m.pitches,
                                "description": m.description,
                            }
                            for m in musical_analysis.motifs
                        ],
                        "phrases": [
                            {
                                "start": p.start,
                                "duration": p.duration,
                                "description": p.description,
                            }
                            for p in musical_analysis.phrases
                        ],
                        "harmony": {
                            "chords": musical_analysis.harmonic_progression.chords if musical_analysis.harmonic_progression else [],
                            "key": musical_analysis.harmonic_progression.key if musical_analysis.harmonic_progression else None,
                        } if musical_analysis.harmonic_progression else None,
                        "form": musical_analysis.form,
                        "key_ideas": musical_analysis.key_ideas,
                        "expansion_suggestions": musical_analysis.expansion_suggestions,
                    },
                }
                
                # Determine output directory and paths
                base_name = _derive_base_name_from_path(args.in_path, "analyze-output")
                output_dir = _get_output_base_dir(base_name, "analyze")
                
                if args.out_path is not None:
                    out_json_path = _resolve_output_path(
                        args.out_path, output_dir, "analysis.json", "analyze"
                    )
                else:
                    out_json_path = None
                
                # Output analysis
                analysis_json = json.dumps(analysis_result, indent=2)
                if args.out_path is None:
                    sys.stdout.write(analysis_json)
                else:
                    _write_text(out_json_path, analysis_json)
                    sys.stdout.write(str(out_json_path) + "\n")
                
                return 0
            
            # Handle MIDI input (existing behavior)
            if suffix not in (".mid", ".midi"):
                raise ValueError("Input must be a .mid, .midi, or .json file.")

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
            if args.render and args.provider:
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

            if args.provider:
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
                        sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                    raw_text = _read_text(raw_out_path)
                    cached_raw_path = raw_out_path
                
                # If no cached response, call AI provider
                if raw_text is None:
                    if args.provider == "gemini":
                        raw_text = generate_text(model=args.model, prompt=prompt, verbose=args.verbose)
                    else:
                        raise ValueError(f"Unsupported provider: {args.provider}")

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
                            "warning: AI raw output was not saved. Provide --raw (-r) "
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
                raise ValueError("--render is only supported with --provider for 'analyze'.")

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

    if args.cmd == "generate":
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
            output_dir = _get_output_base_dir(base_name, "generate")
            
            # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
            if args.out_path is not None:
                out_json_path = _resolve_output_path(
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
                    out_midi_path = _resolve_output_path(
                        Path(midi_name), output_dir, "composition.mid", "generate"
                    )
                else:
                    out_midi_path = _resolve_output_path(
                        args.out_midi_path, output_dir, "composition.mid", "generate"
                    )
            else:
                out_midi_path = _resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "generate"
                ) if args.out_midi_path is not None else None
            prompt_out_path = _resolve_output_path(
                args.prompt_out_path, output_dir, "prompt.txt", "generate"
            ) if args.prompt_out_path is not None else None
            
            # Generate prompt template
            template = generation_prompt_template(description)
            
            if prompt_out_path is not None:
                _write_text(prompt_out_path, template)
            
            # If no provider specified, just output the prompt
            if args.provider is None:
                if args.out_path is None:
                    sys.stdout.write(template)
                else:
                    _write_text(out_json_path, template)
                    sys.stdout.write(str(out_json_path) + "\n")
                return 0
            
            # Generate composition using AI provider
            prompt = _gemini_prompt_from_template(template)
            
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
                    sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                raw_text = _read_text(raw_out_path)
                cached_raw_path = raw_out_path
            
            # If no cached response, call AI provider
            if raw_text is None:
                if args.provider == "gemini":
                    raw_text = generate_text(model=args.model, prompt=prompt, verbose=args.verbose)
                else:
                    raise ValueError(f"Unsupported provider: {args.provider}")
            
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
                        "warning: AI raw output was not saved. Provide --raw (-r) "
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
                sys.stdout.write(f"Rendered to: {out_midi_path}\n")
        except Exception as exc:
            if args.debug:
                traceback.print_exc(file=sys.stderr)
            sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
            return 1
        return 0

    raise RuntimeError("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())

