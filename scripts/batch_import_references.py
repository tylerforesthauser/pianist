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
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.parser import parse_composition_from_text
from pianist.reference_db import MusicalReference, get_default_database
from pianist.iterate import composition_from_midi


def parse_metadata_csv(csv_path: Path) -> dict[str, dict[str, Any]]:
    """
    Parse metadata CSV file.
    
    Expected columns:
    - filename: Name of the file (required)
    - id: Reference ID (optional, auto-generated if not provided)
    - title: Title (optional, uses composition title if not provided)
    - description: Description (required)
    - style: Musical style (optional)
    - form: Musical form (optional)
    - techniques: Comma-separated list of techniques (optional)
    
    Returns:
        Dictionary mapping filename to metadata dict
    """
    metadata: dict[str, dict[str, Any]] = {}
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get("filename", "").strip()
            if not filename:
                continue
            
            # Parse techniques if present
            techniques = None
            if row.get("techniques"):
                techniques = [t.strip() for t in row["techniques"].split(",") if t.strip()]
            
            metadata[filename] = {
                "id": row.get("id", "").strip() or None,
                "title": row.get("title", "").strip() or None,
                "description": row.get("description", "").strip() or "",
                "style": row.get("style", "").strip() or None,
                "form": row.get("form", "").strip() or None,
                "techniques": techniques,
            }
    
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
        
        # Extract metadata
        ref_id = metadata.get("id") if metadata else None
        if not ref_id:
            # Generate ID from filename or title
            if comp.title:
                ref_id = comp.title.lower().replace(" ", "_").replace("-", "_")
            else:
                ref_id = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        
        title = metadata.get("title") if metadata else comp.title or file_path.stem
        description = metadata.get("description") if metadata else ""
        style = metadata.get("style") if metadata else None
        form = metadata.get("form") if metadata else None
        techniques = metadata.get("techniques") if metadata else None
        
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
        "--verbose", "-v",
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

