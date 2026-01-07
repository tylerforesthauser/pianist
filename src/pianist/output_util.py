"""Unified output path resolution and versioning utilities.

This module provides a consistent interface for writing output files with
automatic versioning and coordinated sidecar file handling (e.g., raw AI responses).
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class OutputWriteResult(NamedTuple):
    """Result of writing output files with optional sidecar."""
    primary_path: Path
    sidecar_path: Path | None


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
        parent = path.parent
        base_stem = f"{stem}.{timestamp}"

        # First try the plain timestamped name
        versioned_path = parent / f"{base_stem}{suffix}"
        if not versioned_path.exists():
            return versioned_path

        # If there is a collision within the same second, append an incremental suffix
        counter = 2
        while True:
            versioned_path = parent / f"{base_stem}.v{counter}{suffix}"
            if not versioned_path.exists():
                return versioned_path
            counter += 1
    else:
        # Use incremental versioning: filename.v2.ext, filename.v3.ext, etc.
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        # Check if stem already ends with .vN pattern
        stem_version_match = re.match(r"^(.+)\.v(\d+)$", stem)
        # Also check if suffix is a version pattern (e.g., ".v2" with no other extension)
        suffix_version_match = re.match(r"^\.v(\d+)$", suffix)
        
        if stem_version_match:
            # Version is in the stem: "output.v2" + ".json" -> "output.v3.json"
            base_stem = stem_version_match.group(1)
            version_num = int(stem_version_match.group(2))
            next_version = version_num + 1
        elif suffix_version_match:
            # Version is in the suffix: "output" + ".v2" -> "output.v3"
            # This handles files like "output.v2" with no other extension
            base_stem = stem
            version_num = int(suffix_version_match.group(1))
            next_version = version_num + 1
            suffix = ""  # No extension, version becomes part of the name
        else:
            # No version found, start at v2
            base_stem = stem
            next_version = 2
        
        # Find the next available version
        while True:
            versioned_path = parent / f"{base_stem}.v{next_version}{suffix}"
            if not versioned_path.exists():
                return versioned_path
            next_version += 1


def derive_sidecar_path(primary_path: Path, provider: str | None = None) -> Path:
    """
    Derive the sidecar file path from the primary output path.
    
    For AI providers, the sidecar contains the raw AI response.
    The sidecar is placed next to the primary file with a provider-specific extension.
    
    Args:
        primary_path: Path to the primary output file
        provider: Optional provider name (e.g., "gemini", "ollama")
    
    Returns:
        Path to the sidecar file
    
    Examples:
        >>> derive_sidecar_path(Path("output.json"), "gemini")
        Path("output.json.gemini.txt")
        >>> derive_sidecar_path(Path("output.json"))
        Path("output.json.txt")
    """
    if provider:
        return primary_path.with_name(primary_path.name + f".{provider}.txt")
    else:
        # Default to generic .txt extension if no provider specified
        return primary_path.with_name(primary_path.name + ".txt")


def write_output_with_sidecar(
    primary_path: Path,
    primary_content: str,
    sidecar_content: str | None = None,
    provider: str | None = None,
    overwrite: bool = False,
) -> OutputWriteResult:
    """
    Write primary output file and optional sidecar with coordinated versioning.
    
    This function ensures that:
    1. If the primary file needs versioning (exists and not overwriting), both files are versioned
    2. The sidecar version always matches the primary file version
    3. Directories are created as needed
    
    Args:
        primary_path: Path for the primary output file
        primary_content: Content to write to the primary file
        sidecar_content: Optional content for sidecar file (e.g., raw AI response)
        provider: Optional provider name for sidecar naming
        overwrite: If True, overwrite existing files; if False, create versioned copies
    
    Returns:
        OutputWriteResult with actual paths used (may be versioned)
    
    Example:
        >>> result = write_output_with_sidecar(
        ...     Path("output/song.json"),
        ...     '{"title": "Song"}',
        ...     sidecar_content="Raw AI response...",
        ...     provider="gemini",
        ...     overwrite=False
        ... )
        >>> print(result.primary_path)  # May be output/song.v2.json if song.json existed
        >>> print(result.sidecar_path)  # Will be output/song.v2.json.gemini.txt
    """
    # Determine if we need to version the primary file
    actual_primary_path = primary_path
    if not overwrite and primary_path.exists():
        actual_primary_path = version_path_if_exists(primary_path, use_timestamp=False)
    
    # Create parent directory if needed
    if actual_primary_path.parent and not actual_primary_path.parent.exists():
        actual_primary_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write primary file
    actual_primary_path.write_text(primary_content, encoding="utf-8")
    
    # Handle sidecar file if content is provided
    actual_sidecar_path = None
    if sidecar_content is not None:
        # Always derive sidecar path from the ACTUAL primary path (which may be versioned)
        # This ensures sidecar version matches primary version
        actual_sidecar_path = derive_sidecar_path(actual_primary_path, provider)
        
        # Write sidecar file (no additional versioning needed - it's already coordinated)
        actual_sidecar_path.write_text(sidecar_content, encoding="utf-8")
    
    return OutputWriteResult(
        primary_path=actual_primary_path,
        sidecar_path=actual_sidecar_path,
    )
