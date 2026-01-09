#!/usr/bin/env python3
"""
Normalize and organize MIDI file review data for database import.

This script processes the review_report.csv to:
1. Rename MIDI files according to suggested names
2. Cross-reference similar and duplicate compositions
3. Generate lists for manual review (duplicates, exclusions)
4. Validate data completeness

Usage:
    # Dry run (show what would be done)
    python3 scripts/normalize_midi_review.py --csv output/review_report.csv --dir references/ --dry-run

    # Actually rename files and generate reports
    python3 scripts/normalize_midi_review.py --csv output/review_report.csv --dir references/

    # Custom quality thresholds
    python3 scripts/normalize_midi_review.py --csv output/review_report.csv --dir references/ --min-quality 0.8 --min-technical 0.7
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Convert a suggested name to a valid filename."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_length:
        name = name[:max_length].rsplit(" ", 1)[0]
    return name


def generate_filename(suggested_name: str, suggested_id: str) -> str:
    """Generate a clean filename from suggested name and ID."""
    clean_name = sanitize_filename(suggested_name)
    if len(clean_name) < 3:
        clean_name = suggested_id
    return f"{clean_name}.mid" if not clean_name.endswith(".mid") else clean_name


def parse_similar_files(similar_files_str: str) -> list[str]:
    """Parse semicolon-separated list of similar files."""
    if not similar_files_str or not similar_files_str.strip():
        return []
    return [f.strip() for f in similar_files_str.split(";") if f.strip()]


def parse_similarity_scores(similarity_scores_str: str) -> dict[str, float]:
    """Parse similarity scores string format: 'file1: 0.85; file2: 0.72'."""
    scores: dict[str, float] = {}
    if not similarity_scores_str or not similarity_scores_str.strip():
        return scores
    for pair_raw in similarity_scores_str.split(";"):
        pair = pair_raw.strip()
        if ":" in pair:
            filename, score_str = pair.split(":", 1)
            try:
                scores[filename.strip()] = float(score_str.strip())
            except ValueError:
                continue
    return scores


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value == "" or value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    if value == "" or value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def build_duplicate_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Build duplicate groups from duplicate_group field or similar_files relationships.

    Uses duplicate_group if available (more efficient), otherwise builds from similar_files graph.
    """
    # First, try using duplicate_group field if available
    groups_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    filename_to_row: dict[str, dict[str, Any]] = {row["filename"]: row for row in rows}

    for row in rows:
        group_id = row.get("duplicate_group", "").strip()
        if group_id:
            groups_by_id[group_id].append(row)

    # If we have groups from duplicate_group field, use them
    if groups_by_id:
        # Filter to only groups with 2+ files
        return {gid: files for gid, files in groups_by_id.items() if len(files) > 1}

    # Otherwise, build from similar_files graph
    similar_graph: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        filename = row["filename"]
        similar_files = parse_similar_files(row.get("similar_files", ""))
        for similar_file in similar_files:
            similar_graph[filename].add(similar_file)
            similar_graph[similar_file].add(filename)

    # Find connected components
    visited: set[str] = set()
    groups: dict[str, list[dict[str, Any]]] = {}
    group_counter = 0

    def dfs(node: str, current_group: list[str]) -> None:
        if node in visited or node not in filename_to_row:
            return
        visited.add(node)
        current_group.append(node)
        for neighbor in similar_graph.get(node, set()):
            if neighbor in filename_to_row:
                dfs(neighbor, current_group)

    for filename in filename_to_row:
        if filename not in visited:
            current_group: list[str] = []
            dfs(filename, current_group)
            if len(current_group) > 1:
                group_id = f"group_{group_counter:03d}"
                groups[group_id] = [filename_to_row[f] for f in current_group]
                group_counter += 1

    return groups


def identify_exclusions(
    rows: list[dict[str, Any]],
    min_quality: float = 0.7,
    min_technical: float = 0.5,
    min_musical: float = 0.5,
    min_structure: float = 0.5,
) -> list[dict[str, Any]]:
    """Identify files that should be excluded from the database."""
    exclusions: list[dict[str, Any]] = []

    for row in rows:
        reasons: list[str] = []

        quality_score = safe_float(row.get("quality_score", 0))
        technical_score = safe_float(row.get("technical_score", 0))
        musical_score = safe_float(row.get("musical_score", 0))
        structure_score = safe_float(row.get("structure_score", 0))

        # Quality thresholds
        if quality_score < min_quality:
            reasons.append(f"Low quality score: {quality_score:.3f} < {min_quality}")
        if technical_score < min_technical:
            reasons.append(f"Low technical score: {technical_score:.3f} < {min_technical}")
        if musical_score < min_musical:
            reasons.append(f"Low musical score: {musical_score:.3f} < {min_musical}")
        if structure_score < min_structure:
            reasons.append(f"Low structure score: {structure_score:.3f} < {min_structure}")

        # Duration checks
        duration_beats = safe_float(row.get("duration_beats", 0))
        if duration_beats > 0:
            if duration_beats < 20:
                reasons.append(f"Very short: {duration_beats:.1f} beats (likely fragment)")
            if duration_beats > 1000:
                reasons.append(f"Very long: {duration_beats:.1f} beats (might be multi-movement)")

        # Missing critical metadata
        if not row.get("suggested_name") or not row.get("suggested_name", "").strip():
            reasons.append("Missing suggested_name")
        if not row.get("detected_key"):
            reasons.append("Missing detected_key")
        if not row.get("detected_form"):
            reasons.append("Missing detected_form")

        # Check if marked as original (might want to exclude originals)
        is_original = row.get("is_original", "").strip().lower() in ("yes", "true", "1")
        if is_original:
            reasons.append("Marked as original composition (may want to exclude)")

        if reasons:
            exclusions.append(
                {
                    "filename": row["filename"],
                    "quality_score": quality_score,
                    "technical_score": technical_score,
                    "musical_score": musical_score,
                    "structure_score": structure_score,
                    "suggested_name": row.get("suggested_name", ""),
                    "is_original": is_original,
                    "reasons": reasons,
                }
            )

    return exclusions


def validate_data_completeness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Check if all required fields are present."""
    # All fields that the review script can generate
    all_fields = [
        "filename",
        "filepath",
        "quality_score",
        "quality_issues",
        "suggested_name",
        "suggested_id",
        "suggested_style",
        "suggested_description",
        "detected_key",
        "detected_form",
        "duration_beats",
        "duration_seconds",
        "bars",
        "tempo_bpm",
        "time_signature",
        "key_signature",
        "tracks",
        "motif_count",
        "phrase_count",
        "chord_count",
        "harmonic_progression",
        "is_duplicate",
        "duplicate_group",
        "similar_files",
        "similarity_scores",
        "technical_score",
        "musical_score",
        "structure_score",
        "is_original",
    ]

    missing_fields: dict[str, list[str]] = defaultdict(list)
    total_rows = len(rows)

    # Get available fields from first row
    available_fields = set(rows[0].keys()) if rows else set()

    for row in rows:
        filename = row.get("filename", "unknown")
        for field in all_fields:
            if field not in available_fields:
                continue  # Field not in CSV, skip
            value = row.get(field, "")
            if value == "" or value is None:
                missing_fields[field].append(filename)

    return {
        "total_files": total_rows,
        "available_fields": sorted(available_fields),
        "missing_fields": dict(missing_fields),
        "completeness": {
            field: (total_rows - len(files)) / total_rows * 100
            for field, files in missing_fields.items()
        },
    }


def extract_metadata(row: dict[str, Any]) -> dict[str, Any]:
    """Extract all available metadata from a row."""
    return {
        "filename": row.get("filename", ""),
        "filepath": row.get("filepath", ""),
        "quality_score": safe_float(row.get("quality_score", 0)),
        "quality_issues": safe_int(row.get("quality_issues", 0)),
        "suggested_name": row.get("suggested_name", ""),
        "suggested_id": row.get("suggested_id", ""),
        "suggested_style": row.get("suggested_style", ""),
        "suggested_description": row.get("suggested_description", ""),
        "detected_key": row.get("detected_key", ""),
        "detected_form": row.get("detected_form", ""),
        "duration_beats": safe_float(row.get("duration_beats", 0)),
        "duration_seconds": safe_float(row.get("duration_seconds", 0)),
        "bars": safe_float(row.get("bars", 0)),
        "tempo_bpm": safe_float(row.get("tempo_bpm", 0)) if row.get("tempo_bpm") else None,
        "time_signature": row.get("time_signature", ""),
        "key_signature": row.get("key_signature", ""),
        "tracks": safe_int(row.get("tracks", 0)),
        "motif_count": safe_int(row.get("motif_count", 0)),
        "phrase_count": safe_int(row.get("phrase_count", 0)),
        "chord_count": safe_int(row.get("chord_count", 0)),
        "harmonic_progression": row.get("harmonic_progression", ""),
        "is_duplicate": row.get("is_duplicate", "").strip().lower() in ("yes", "true", "1"),
        "duplicate_group": row.get("duplicate_group", ""),
        "similar_files": parse_similar_files(row.get("similar_files", "")),
        "similarity_scores": parse_similarity_scores(row.get("similarity_scores", "")),
        "technical_score": safe_float(row.get("technical_score", 0)),
        "musical_score": safe_float(row.get("musical_score", 0)),
        "structure_score": safe_float(row.get("structure_score", 0)),
        "is_original": row.get("is_original", "").strip().lower() in ("yes", "true", "1"),
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Normalize and organize MIDI file review data")
    parser.add_argument("--csv", type=Path, required=True, help="Path to review_report.csv")
    parser.add_argument("--dir", type=Path, required=True, help="Directory containing MIDI files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for renamed files (default: same as --dir)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--min-quality", type=float, default=0.7, help="Minimum quality score (default: 0.7)"
    )
    parser.add_argument(
        "--min-technical", type=float, default=0.5, help="Minimum technical score (default: 0.5)"
    )
    parser.add_argument(
        "--min-musical", type=float, default=0.5, help="Minimum musical score (default: 0.5)"
    )
    parser.add_argument(
        "--min-structure", type=float, default=0.5, help="Minimum structure score (default: 0.5)"
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Directory for output reports (default: same directory as CSV)",
    )
    parser.add_argument(
        "--include-originals",
        action="store_true",
        help="Include original compositions in import metadata (default: exclude)",
    )
    parser.add_argument(
        "--include-excluded",
        action="store_true",
        help="Include files flagged for exclusion in import metadata (default: exclude)",
    )

    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        return 1
    if not args.dir.exists():
        print(f"Error: Directory not found: {args.dir}", file=sys.stderr)
        return 1

    output_dir = args.output_dir or args.dir
    reports_dir = args.reports_dir or args.csv.parent

    # Read CSV
    print(f"Reading review report: {args.csv}")
    with open(args.csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} file records")

    # Validate data completeness
    print("\n=== Data Completeness Check ===")
    completeness = validate_data_completeness(rows)
    print(f"Total files: {completeness['total_files']}")
    print(f"Available fields: {len(completeness['available_fields'])}")
    if completeness["missing_fields"]:
        print("\nField completeness:")
        for field, percent in sorted(completeness["completeness"].items()):
            missing_count = len(completeness["missing_fields"].get(field, []))
            if missing_count > 0:
                print(f"  {field}: {percent:.1f}% ({missing_count} missing)")

    # Build duplicate groups
    print("\n=== Duplicate Detection ===")
    duplicate_groups = build_duplicate_groups(rows)
    print(f"Found {len(duplicate_groups)} duplicate groups")

    # Identify exclusions
    print("\n=== Exclusion Analysis ===")
    exclusions = identify_exclusions(
        rows, args.min_quality, args.min_technical, args.min_musical, args.min_structure
    )
    print(f"Found {len(exclusions)} files to review for exclusion")

    # Filter files for import (calculate early for summary report)
    excluded_filenames = (
        {excl["filename"] for excl in exclusions} if not args.include_excluded else set()
    )

    files_for_import = []
    for row in rows:
        # Skip if excluded (unless --include-excluded)
        if row["filename"] in excluded_filenames:
            continue

        # Skip originals unless --include-originals (default: exclude)
        is_original = row.get("is_original", "").strip().lower() in ("yes", "true", "1")
        if is_original and not args.include_originals:
            continue

        files_for_import.append(row)

    # Generate reports
    print("\n=== Generating Reports ===")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Duplicate groups report (with full metadata)
    duplicate_report = {"total_groups": len(duplicate_groups), "groups": {}}
    for group_id, group_files in duplicate_groups.items():
        duplicate_report["groups"][group_id] = {
            "count": len(group_files),
            "files": [extract_metadata(f) for f in group_files],
        }

    duplicate_report_path = reports_dir / "duplicate_groups_report.json"
    with open(duplicate_report_path, "w", encoding="utf-8") as f:
        json.dump(duplicate_report, f, indent=2, ensure_ascii=False)
    print(f"  Duplicate groups JSON: {duplicate_report_path}")

    # 2. Exclusions report
    exclusions_report_path = reports_dir / "exclusions_report.json"
    with open(exclusions_report_path, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2, ensure_ascii=False)
    print(f"  Exclusions JSON: {exclusions_report_path}")

    # 3. Rename mapping
    rename_mapping: list[dict[str, str]] = []
    rename_conflicts: list[dict[str, Any]] = []
    used_names: dict[str, tuple[str, str]] = {}

    for row in rows:
        original_filename = row["filename"]
        suggested_name = row.get("suggested_name", "")
        suggested_id = row.get("suggested_id", "")

        if not suggested_name:
            continue

        new_filename = generate_filename(suggested_name, suggested_id)

        if new_filename in used_names:
            conflict_original, conflict_suggested = used_names[new_filename]
            rename_conflicts.append(
                {
                    "new_filename": new_filename,
                    "original_1": conflict_original,
                    "original_2": original_filename,
                    "suggested_name_1": conflict_suggested,
                    "suggested_name_2": suggested_name,
                }
            )
            base_name = new_filename[:-4]
            counter = 1
            while new_filename in used_names:
                new_filename = f"{base_name}_{counter:02d}.mid"
                counter += 1

        used_names[new_filename] = (original_filename, suggested_name)
        rename_mapping.append(
            {
                "original": original_filename,
                "new": new_filename,
                "suggested_name": suggested_name,
                "suggested_id": suggested_id,
            }
        )

    rename_report_path = reports_dir / "rename_mapping.json"
    with open(rename_report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_files": len(rename_mapping),
                "conflicts": len(rename_conflicts),
                "mapping": rename_mapping,
                "conflicts_detail": rename_conflicts,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  Rename mapping JSON: {rename_report_path}")

    if rename_conflicts:
        print(f"  WARNING: {len(rename_conflicts)} filename conflicts detected")

    # 4. Generate CSV reports
    print("\n=== Generating CSV Reports ===")

    # Duplicate groups CSV (with all metadata)
    duplicate_csv_path = reports_dir / "duplicate_groups_report.csv"
    with open(duplicate_csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "group_id",
            "filename",
            "suggested_name",
            "suggested_style",
            "quality_score",
            "technical_score",
            "musical_score",
            "structure_score",
            "detected_key",
            "detected_form",
            "duration_beats",
            "bars",
            "tempo_bpm",
            "time_signature",
            "motif_count",
            "phrase_count",
            "chord_count",
            "is_original",
            "similarity_scores",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for group_id, group_files in duplicate_groups.items():
            for file_data in group_files:
                meta = extract_metadata(file_data)
                similarity_str = "; ".join(
                    f"{f}: {s:.3f}" for f, s in meta["similarity_scores"].items()
                )
                writer.writerow(
                    {
                        "group_id": group_id,
                        "filename": meta["filename"],
                        "suggested_name": meta["suggested_name"],
                        "suggested_style": meta["suggested_style"],
                        "quality_score": f"{meta['quality_score']:.3f}",
                        "technical_score": f"{meta['technical_score']:.3f}",
                        "musical_score": f"{meta['musical_score']:.3f}",
                        "structure_score": f"{meta['structure_score']:.3f}",
                        "detected_key": meta["detected_key"],
                        "detected_form": meta["detected_form"],
                        "duration_beats": f"{meta['duration_beats']:.1f}",
                        "bars": f"{meta['bars']:.1f}",
                        "tempo_bpm": f"{meta['tempo_bpm']:.1f}" if meta["tempo_bpm"] else "",
                        "time_signature": meta["time_signature"],
                        "motif_count": meta["motif_count"],
                        "phrase_count": meta["phrase_count"],
                        "chord_count": meta["chord_count"],
                        "is_original": "Yes" if meta["is_original"] else "No",
                        "similarity_scores": similarity_str,
                    }
                )
    print(f"  Duplicate groups CSV: {duplicate_csv_path}")

    # Exclusions CSV
    exclusions_csv_path = reports_dir / "exclusions_report.csv"
    with open(exclusions_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "filename",
                "suggested_name",
                "quality_score",
                "technical_score",
                "musical_score",
                "structure_score",
                "is_original",
                "reasons",
            ]
        )
        for excl in exclusions:
            writer.writerow(
                [
                    excl["filename"],
                    excl["suggested_name"],
                    excl["quality_score"],
                    excl["technical_score"],
                    excl["musical_score"],
                    excl["structure_score"],
                    "Yes" if excl["is_original"] else "No",
                    "; ".join(excl["reasons"]),
                ]
            )
    print(f"  Exclusions CSV: {exclusions_csv_path}")

    # Rename mapping CSV
    rename_csv_path = reports_dir / "rename_mapping.csv"
    with open(rename_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["original_filename", "new_filename", "suggested_name", "suggested_id"])
        for mapping in rename_mapping:
            writer.writerow(
                [
                    mapping["original"],
                    mapping["new"],
                    mapping["suggested_name"],
                    mapping["suggested_id"],
                ]
            )
    print(f"  Rename mapping CSV: {rename_csv_path}")

    # 5. Generate metadata CSV for batch import (ready for reference database)
    print("\n=== Generating Database Import Metadata ===")

    # Create metadata CSV for batch import (with all enhanced metadata)
    import_metadata_path = reports_dir / "import_metadata.csv"
    with open(import_metadata_path, "w", encoding="utf-8", newline="") as f:
        # Include all enhanced metadata fields for batch import
        fieldnames = [
            "filename",
            "id",
            "title",
            "description",
            "style",
            "form",
            "techniques",
            "detected_key",
            "tempo_bpm",
            "duration_beats",
            "quality_score",
            "technical_score",
            "musical_score",
            "structure_score",
            "motif_count",
            "phrase_count",
            "chord_count",
            "harmonic_progression",
            "time_signature",
            "bars",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in files_for_import:
            meta = extract_metadata(row)
            # Use new filename if rename mapping exists
            filename = next(
                (m["new"] for m in rename_mapping if m["original"] == row["filename"]),
                row["filename"],
            )

            # Limit harmonic progression length
            harmonic_prog = meta["harmonic_progression"]
            if harmonic_prog:
                harmonic_prog = " ".join(harmonic_prog.split()[:10])

            writer.writerow(
                {
                    "filename": filename,
                    "id": meta["suggested_id"]
                    or meta["filename"].replace(".mid", "").replace(".midi", ""),
                    "title": meta["suggested_name"]
                    or meta["filename"].replace(".mid", "").replace(".midi", ""),
                    "description": meta["suggested_description"]
                    or meta["suggested_name"]
                    or "Musical composition",
                    "style": meta["suggested_style"] or "",
                    "form": meta["detected_form"] or "",
                    "techniques": "",  # Left empty for manual addition
                    "detected_key": meta["detected_key"] or "",
                    "tempo_bpm": f"{meta['tempo_bpm']:.1f}" if meta["tempo_bpm"] else "",
                    "duration_beats": f"{meta['duration_beats']:.1f}"
                    if meta["duration_beats"]
                    else "",
                    "quality_score": f"{meta['quality_score']:.3f}"
                    if meta["quality_score"]
                    else "",
                    "technical_score": f"{meta['technical_score']:.3f}"
                    if meta["technical_score"]
                    else "",
                    "musical_score": f"{meta['musical_score']:.3f}"
                    if meta["musical_score"]
                    else "",
                    "structure_score": f"{meta['structure_score']:.3f}"
                    if meta["structure_score"]
                    else "",
                    "motif_count": meta["motif_count"] if meta["motif_count"] else "",
                    "phrase_count": meta["phrase_count"] if meta["phrase_count"] else "",
                    "chord_count": meta["chord_count"] if meta["chord_count"] else "",
                    "harmonic_progression": harmonic_prog or "",
                    "time_signature": meta["time_signature"] or "",
                    "bars": f"{meta['bars']:.1f}" if meta["bars"] else "",
                }
            )

    print(f"  Import metadata CSV: {import_metadata_path}")
    print(f"  Files ready for import: {len(files_for_import)}")

    # 7. Coverage analysis
    print("\n=== Coverage Analysis ===")
    coverage = {
        "by_style": defaultdict(int),
        "by_form": defaultdict(int),
        "by_quality": {"high": 0, "medium": 0, "low": 0},
    }

    for row in files_for_import:
        meta = extract_metadata(row)
        style = meta["suggested_style"] or "Unknown"
        form = meta["detected_form"] or "Unknown"
        quality = meta["quality_score"]

        coverage["by_style"][style] += 1
        coverage["by_form"][form] += 1

        if quality >= 0.8:
            coverage["by_quality"]["high"] += 1
        elif quality >= 0.6:
            coverage["by_quality"]["medium"] += 1
        else:
            coverage["by_quality"]["low"] += 1

    coverage_report_path = reports_dir / "coverage_analysis.json"
    with open(coverage_report_path, "w", encoding="utf-8") as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    print(f"  Coverage analysis: {coverage_report_path}")

    print("\nCoverage Summary:")
    print("  By Style:")
    for style, count in sorted(coverage["by_style"].items(), key=lambda x: -x[1]):
        print(f"    {style}: {count}")
    print("  By Form:")
    for form, count in sorted(coverage["by_form"].items(), key=lambda x: -x[1]):
        print(f"    {form}: {count}")
    print("  By Quality:")
    for quality, count in coverage["by_quality"].items():
        print(f"    {quality}: {count}")

    # 6. Summary report (generated after all analysis is complete)
    summary = {
        "total_files": len(rows),
        "duplicate_groups": len(duplicate_groups),
        "files_in_duplicate_groups": sum(len(g) for g in duplicate_groups.values()),
        "exclusions": len(exclusions),
        "files_to_rename": len(rename_mapping),
        "rename_conflicts": len(rename_conflicts),
        "files_for_import": len(files_for_import),
        "coverage": coverage,
        "data_completeness": completeness,
    }

    summary_report_path = reports_dir / "normalization_summary.json"
    with open(summary_report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n  Summary JSON: {summary_report_path}")

    # Perform renames if not dry-run
    if not args.dry_run:
        print("\n=== Renaming Files ===")
        renamed_count = 0
        not_found_count = 0

        for mapping in rename_mapping:
            original_path = args.dir / mapping["original"]
            new_path = output_dir / mapping["new"]

            if not original_path.exists():
                print(f"  WARNING: File not found: {original_path}")
                not_found_count += 1
                continue

            if original_path == new_path:
                continue

            if new_path.exists():
                print(f"  WARNING: Target exists, skipping: {new_path}")
                continue

            try:
                original_path.rename(new_path)
                print(f"  Renamed: {mapping['original']} -> {mapping['new']}")
                renamed_count += 1
            except Exception as e:
                print(f"  ERROR renaming {mapping['original']}: {e}")

        print(f"\nRenamed {renamed_count} files")
        if not_found_count > 0:
            print(f"  {not_found_count} files not found")
    else:
        print("\n=== DRY RUN - No files renamed ===")
        print(f"Would rename {len(rename_mapping)} files")

    # Print summary
    print("\n=== Summary ===")
    print(f"Total files: {len(rows)}")
    print(f"Duplicate groups: {len(duplicate_groups)}")
    print(f"Files in duplicate groups: {sum(len(g) for g in duplicate_groups.values())}")
    print(f"Files to review for exclusion: {len(exclusions)}")
    print(f"Files to rename: {len(rename_mapping)}")
    print(f"Files ready for import: {len(files_for_import)}")
    if rename_conflicts:
        print(f"Rename conflicts: {len(rename_conflicts)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
