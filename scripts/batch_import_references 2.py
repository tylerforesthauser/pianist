#!/usr/bin/env python3
"""
Batch import script for adding multiple references to the reference database.

This script can import references from:
- JSON files (Pianist format)
- MIDI files (converted to JSON first)
- A metadata CSV file to specify style, form, techniques, etc.

Usage:
    # Import from directory with metadata CSV
    python3 scripts/batch_import_references.py --dir references/ --metadata metadata.csv

    # Import from directory (auto-detect metadata from filenames)
    python3 scripts/batch_import_references.py --dir references/

    # Import single file
    python3 scripts/batch_import_references.py --file example.json --style Classical --form ternary
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.iterate import composition_from_midi
from pianist.parser import parse_composition_from_text
from pianist.reference_db import MusicalReference, get_default_database


def parse_metadata_csv(csv_path: Path) -> dict[str, dict[str, Any]]:
    """
    Parse metadata CSV file (supports both basic and enhanced metadata from review script).

    Expected columns (basic):
    - filename: Name of the file (required)
    - id: Reference ID (optional, auto-generated if not provided)
    - title: Title (optional, uses composition title if not provided)
    - description: Description (required)
    - style: Musical style (optional)
    - form: Musical form (optional)
    - techniques: Comma-separated list of techniques (optional)

    Enhanced columns (from review script, optional):
    - detected_key, tempo_bpm, duration_beats, quality_score, etc.

    Returns:
        Dictionary mapping filename to metadata dict
    """
    metadata: dict[str, dict[str, Any]] = {}

    def safe_float(value: Any, default: float | None = None) -> float | None:
        if value == "" or value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def safe_int(value: Any, default: int | None = None) -> int | None:
        if value == "" or value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get("filename", "").strip()
            if not filename:
                continue

            # Parse techniques if present
            techniques = None
            if row.get("techniques"):
                techniques = [t.strip() for t in row["techniques"].split(",") if t.strip()]

            # Basic metadata
            meta = {
                "id": row.get("id", "").strip() or None,
                "title": row.get("title", "").strip() or None,
                "description": row.get("description", "").strip() or "",
                "style": row.get("style", "").strip() or None,
                "form": row.get("form", "").strip() or None,
                "techniques": techniques,
            }

            # Enhanced metadata (from review script)
            if "detected_key" in row:
                meta["detected_key"] = row.get("detected_key", "").strip() or None
            if "tempo_bpm" in row:
                meta["tempo_bpm"] = safe_float(row.get("tempo_bpm"))
            if "duration_beats" in row:
                meta["duration_beats"] = safe_float(row.get("duration_beats"))
            if "quality_score" in row:
                meta["quality_score"] = safe_float(row.get("quality_score"))
            if "technical_score" in row:
                meta["technical_score"] = safe_float(row.get("technical_score"))
            if "musical_score" in row:
                meta["musical_score"] = safe_float(row.get("musical_score"))
            if "structure_score" in row:
                meta["structure_score"] = safe_float(row.get("structure_score"))
            if "motif_count" in row:
                meta["motif_count"] = safe_int(row.get("motif_count"))
            if "phrase_count" in row:
                meta["phrase_count"] = safe_int(row.get("phrase_count"))
            if "chord_count" in row:
                meta["chord_count"] = safe_int(row.get("chord_count"))
            if "harmonic_progression" in row:
                prog = row.get("harmonic_progression", "").strip()
                if prog:
                    meta["harmonic_progression"] = " ".join(prog.split()[:10])
            if "time_signature" in row:
                meta["time_signature"] = row.get("time_signature", "").strip() or None
            if "bars" in row:
                meta["bars"] = safe_float(row.get("bars"))

            metadata[filename] = meta

    return metadata


def import_reference(
    file_path: Path,
    metadata: dict[str, Any] | None = None,
    ref_db: Any | None = None,
    verbose: bool = False,
) -> tuple[bool, str]:
    """
    Import a single reference file.

    Args:
        file_path: Path to JSON or MIDI file
        metadata: Optional metadata dict (id, title, description, style, form, techniques)
        ref_db: Reference database instance (creates new if None)
        verbose: Print verbose output

    Returns:
        Tuple of (success: bool, message: str)
    """
    if ref_db is None:
        ref_db = get_default_database()

    try:
        # Determine file type and load composition
        suffix = file_path.suffix.lower()

        if suffix in (".mid", ".midi"):
            # Import MIDI file
            if verbose:
                print(f"  Importing MIDI: {file_path.name}")
            comp = composition_from_midi(file_path)
        elif suffix == ".json":
            # Load JSON file
            if verbose:
                print(f"  Loading JSON: {file_path.name}")
            text = file_path.read_text(encoding="utf-8")
            comp = parse_composition_from_text(text)
        else:
            return False, f"Unsupported file type: {suffix}"

        # Extract basic metadata
        ref_id = metadata.get("id") if metadata else None
        if not ref_id:
            ref_id = (comp.title or file_path.stem).lower().replace(" ", "_").replace("-", "_")

        title = metadata.get("title") if metadata else comp.title or file_path.stem
        description = metadata.get("description", "")
        style = metadata.get("style") if metadata else None
        form = metadata.get("form") if metadata else None
        techniques = metadata.get("techniques") if metadata else None

        # Extract enhanced metadata fields
        enhanced_fields = {
            "detected_key": metadata.get("detected_key") if metadata else None,
            "tempo_bpm": metadata.get("tempo_bpm") if metadata else None,
            "duration_beats": metadata.get("duration_beats") if metadata else None,
            "quality_score": metadata.get("quality_score") if metadata else None,
            "technical_score": metadata.get("technical_score") if metadata else None,
            "musical_score": metadata.get("musical_score") if metadata else None,
            "structure_score": metadata.get("structure_score") if metadata else None,
            "motif_count": metadata.get("motif_count") if metadata else None,
            "phrase_count": metadata.get("phrase_count") if metadata else None,
            "chord_count": metadata.get("chord_count") if metadata else None,
            "harmonic_progression": metadata.get("harmonic_progression") if metadata else None,
            "time_signature": metadata.get("time_signature") if metadata else None,
            "bars": metadata.get("bars") if metadata else None,
        }

        # Create reference
        reference = MusicalReference(
            id=ref_id,
            title=title,
            description=description,
            composition=comp,
            style=style,
            form=form,
            techniques=techniques,
            metadata=None,
            **enhanced_fields,
        )

        # Add to database
        ref_db.add_reference(reference)

        return True, f"✓ Added: {ref_id} - {title}"

    except Exception as e:
        return False, f"✗ Error importing {file_path.name}: {e}"


def import_from_directory(
    dir_path: Path,
    metadata_csv: Path | None = None,
    pattern: str = "*",
    verbose: bool = False,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Import all matching files from a directory.

    Args:
        dir_path: Directory containing files to import
        metadata_csv: Optional CSV file with metadata
        pattern: Glob pattern for files (default: "*" matches all)
        verbose: Print verbose output
        dry_run: Don't actually import, just show what would be imported

    Returns:
        Tuple of (successful_count, failed_count)
    """
    ref_db = get_default_database() if not dry_run else None

    # Load metadata if provided
    metadata_map: dict[str, dict[str, Any]] = {}
    if metadata_csv and metadata_csv.exists():
        if verbose:
            print(f"Loading metadata from: {metadata_csv}")
        metadata_map = parse_metadata_csv(metadata_csv)

    # Find all JSON and MIDI files
    json_files = list(dir_path.glob(f"{pattern}.json"))
    midi_files = list(dir_path.glob(f"{pattern}.mid")) + list(dir_path.glob(f"{pattern}.midi"))
    all_files = json_files + midi_files

    if not all_files:
        print(f"No matching files found in {dir_path}")
        return 0, 0

    if verbose or dry_run:
        print(f"Found {len(all_files)} files to import")
        if dry_run:
            print("DRY RUN - No files will be imported")

    successful = 0
    failed = 0

    for file_path in sorted(all_files):
        # Get metadata for this file
        filename = file_path.name
        metadata = metadata_map.get(filename)

        if dry_run:
            print(f"Would import: {filename}")
            if metadata:
                print(f"  Metadata: {metadata}")
            successful += 1
        else:
            success, message = import_reference(file_path, metadata, ref_db, verbose)
            print(message)
            if success:
                successful += 1
            else:
                failed += 1

    return successful, failed


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch import references to the reference database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import all files from directory with metadata CSV
  python3 scripts/batch_import_references.py --dir references/ --metadata metadata.csv

  # Import all JSON files from directory
  python3 scripts/batch_import_references.py --dir references/ --pattern "*.json"

  # Import single file with metadata
  python3 scripts/batch_import_references.py --file example.json \\
    --style Classical --form ternary --techniques sequence,inversion \\
    --description "Example of sequential development"

  # Dry run to see what would be imported
  python3 scripts/batch_import_references.py --dir references/ --dry-run
        """,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--dir",
        type=Path,
        help="Directory containing files to import",
    )
    input_group.add_argument(
        "--file",
        type=Path,
        help="Single file to import",
    )

    # Metadata options
    parser.add_argument(
        "--metadata",
        type=Path,
        help="CSV file with metadata (filename, id, title, description, style, form, techniques)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*",
        help="Glob pattern for files in directory (default: *)",
    )

    # Per-file metadata (for single file import)
    parser.add_argument(
        "--id",
        type=str,
        help="Reference ID (auto-generated if not provided)",
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Reference title (uses composition title if not provided)",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Description of the reference",
    )
    parser.add_argument(
        "--style",
        type=str,
        help="Musical style (e.g., Baroque, Classical, Romantic, Modern)",
    )
    parser.add_argument(
        "--form",
        type=str,
        help="Musical form (e.g., binary, ternary, sonata)",
    )
    parser.add_argument(
        "--techniques",
        type=str,
        help="Comma-separated list of techniques (e.g., sequence,inversion,augmentation)",
    )

    # Options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually import, just show what would be imported",
    )

    args = parser.parse_args()

    # Validate file paths
    if args.file and not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    if args.dir and not args.dir.is_dir():
        print(f"Error: Not a directory: {args.dir}", file=sys.stderr)
        return 1

    if args.metadata and not args.metadata.exists():
        print(f"Error: Metadata file not found: {args.metadata}", file=sys.stderr)
        return 1

    # Import
    if args.file:
        # Single file import
        metadata = None
        if args.id or args.title or args.description or args.style or args.form or args.techniques:
            techniques = None
            if args.techniques:
                techniques = [t.strip() for t in args.techniques.split(",") if t.strip()]

            metadata = {
                "id": args.id,
                "title": args.title,
                "description": args.description,
                "style": args.style,
                "form": args.form,
                "techniques": techniques,
            }

        ref_db = get_default_database() if not args.dry_run else None
        success, message = import_reference(args.file, metadata, ref_db, args.verbose)
        print(message)
        return 0 if success else 1

    elif args.dir:
        # Directory import
        successful, failed = import_from_directory(
            args.dir,
            args.metadata,
            args.pattern,
            args.verbose,
            args.dry_run,
        )

        if not args.dry_run:
            ref_db = get_default_database()
            total = ref_db.count_references()
            print(f"\nImport complete: {successful} successful, {failed} failed")
            print(f"Total references in database: {total}")

        return 0 if failed == 0 else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
