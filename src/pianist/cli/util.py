"""Shared CLI utilities for output path handling, file versioning, and text I/O."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# Default output directory for all generated files
DEFAULT_OUTPUT_DIR = Path("output")


def get_output_base_dir(base_name: str, command: str) -> Path:
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
    return DEFAULT_OUTPUT_DIR / base_name / command


def resolve_output_path(
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


def derive_base_name_from_path(path: Path | None, fallback: str = "output") -> str:
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
        abs_output_dir = DEFAULT_OUTPUT_DIR.resolve()
        
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


def read_text(path: Path | None) -> str:
    """Read text from a file or stdin."""
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


def version_path_if_exists(path: Path, use_timestamp: bool = False) -> Path:
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


def write_text(path: Path, text: str, version_if_exists: bool = False) -> Path:
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
        path = version_path_if_exists(path, use_timestamp=False)
    
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def derive_raw_path(out_path: Path, provider: str | None = None) -> Path:
    """
    Derive the raw AI response file path from the JSON output path.
    Keeps it simple and discoverable: next to the JSON output.
    """
    if provider:
        return out_path.with_name(out_path.name + f".{provider}.txt")
    else:
        # Default to generic .txt extension if no provider specified
        return out_path.with_name(out_path.name + ".txt")


def prompt_from_template(template: str) -> str:
    """
    The CLI prompt templates are optimized for copy/paste into chat UIs.
    For API calls, we send a single text prompt that includes both the
    "system" and "user" sections explicitly.
    """
    return template.strip() + "\n"


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
