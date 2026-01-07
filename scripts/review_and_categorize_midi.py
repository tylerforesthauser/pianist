#!/usr/bin/env python3
"""
Comprehensive MIDI file review, analysis, and categorization tool.

This script:
- Reviews MIDI files for quality (using check_midi_quality.py)
- Analyzes musical content (key, form, motifs, harmony)
- Detects duplicate/similar compositions
- Generates descriptive names based on analysis
- Collects metadata for database import
- Outputs CSV and JSON reports
- Supports resumable processing (saves results per-file)
- Supports test mode (limit to N files)

Usage:
    # Test on first 5 files
    python3 scripts/review_and_categorize_midi.py --dir references/ --limit 5 --output test_report.csv

    # Review directory of MIDI files (saves progress automatically)
    python3 scripts/review_and_categorize_midi.py --dir references/ --output review_report.csv

    # Resume from previous run (skips already-analyzed files)
    python3 scripts/review_and_categorize_midi.py --dir references/ --resume --output review_report.csv

    # Review with AI-assisted naming
    python3 scripts/review_and_categorize_midi.py --dir references/ --ai --output review_report.csv

    # Review with duplicate detection threshold
    python3 scripts/review_and_categorize_midi.py --dir references/ --similarity-threshold 0.7

    # Clear cache and start fresh
    python3 scripts/review_and_categorize_midi.py --dir references/ --clear-cache --output review_report.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

# Suppress PedalEvent warnings from iterate.py (they're informational, not errors)
# These warnings occur when MIDI files have pedal events with duration=0
# We suppress them to reduce output clutter during batch processing
warnings.filterwarnings("ignore", message=".*PedalEvent.*duration=0.*", category=UserWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pianist.iterate")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.analyze import analyze_midi
from pianist.iterate import composition_from_midi
from pianist.musical_analysis import (
    analyze_composition,
    detect_motifs,
    detect_form,
    analyze_harmony,
    MUSIC21_AVAILABLE,
)

# Import check_midi_quality functions directly
import importlib.util
check_midi_quality_path = Path(__file__).parent / "check_midi_quality.py"
spec = importlib.util.spec_from_file_location("check_midi_quality", check_midi_quality_path)
check_midi_quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_midi_quality)
check_midi_file = check_midi_quality.check_midi_file
QualityReport = check_midi_quality.QualityReport


@dataclass
class FileMetadata:
    """Metadata collected for a MIDI file."""
    filename: str
    filepath: str
    quality_score: float
    quality_issues: int
    
    # Technical metadata
    duration_beats: float
    duration_seconds: float
    bars: float
    tempo_bpm: float | None
    time_signature: str | None
    key_signature: str | None
    tracks: int
    
    # Musical analysis
    detected_key: str | None
    detected_form: str | None
    motif_count: int
    phrase_count: int
    chord_count: int
    harmonic_progression: str | None
    
    # Generated metadata
    suggested_name: str
    suggested_id: str
    suggested_style: str | None
    suggested_description: str | None
    
    # Duplicate detection
    similar_files: list[str]
    similarity_scores: dict[str, float]
    is_duplicate: bool
    duplicate_group: str | None
    
    # Quality details
    technical_score: float
    musical_score: float
    structure_score: float


def extract_melodic_signature(composition: Any) -> list[int]:
    """
    Extract a melodic signature (pitch sequence) for duplicate detection.
    
    Returns:
        List of MIDI pitch values representing the main melodic line
    """
    if not MUSIC21_AVAILABLE:
        return []
    
    try:
        from music21 import stream, note, chord
        
        s = stream.Stream()
        
        # Convert composition to music21 stream (simplified)
        for track in composition.tracks:
            for event in track.events:
                if hasattr(event, 'pitches') and event.pitches:
                    if len(event.pitches) == 1:
                        n = note.Note(event.pitches[0])
                        n.offset = getattr(event, 'start', 0)
                        s.insert(n)
                    else:
                        # Use lowest pitch for melodic signature
                        c = chord.Chord(sorted(event.pitches))
                        c.offset = getattr(event, 'start', 0)
                        s.insert(c)
        
        # Extract melodic line (first 50 notes, normalized)
        melodic_pitches: list[int] = []
        for element in s.flatten().notes[:50]:  # First 50 notes
            if isinstance(element, note.Note):
                melodic_pitches.append(element.pitch.midi)
            elif isinstance(element, chord.Chord):
                melodic_pitches.append(min(p.midi for p in element.pitches))
        
        return melodic_pitches
    except Exception:
        return []


def calculate_similarity(
    metadata1: FileMetadata,
    metadata2: FileMetadata,
    melodic1: list[int],
    melodic2: list[int],
) -> float:
    """
    Calculate similarity score between two files (0.0 to 1.0).
    
    Factors:
    - Key signature match
    - Form match
    - Harmonic progression similarity
    - Melodic signature similarity
    - Duration similarity
    """
    score = 0.0
    factors = 0
    
    # Key signature match (0.3 weight)
    if metadata1.detected_key and metadata2.detected_key:
        if metadata1.detected_key == metadata2.detected_key:
            score += 0.3
        # Check if same key (ignoring mode)
        key1_base = metadata1.detected_key.split()[0] if ' ' in metadata1.detected_key else metadata1.detected_key
        key2_base = metadata2.detected_key.split()[0] if ' ' in metadata2.detected_key else metadata2.detected_key
        if key1_base == key2_base:
            score += 0.15
        factors += 0.3
    
    # Form match (0.2 weight)
    if metadata1.detected_form and metadata2.detected_form:
        if metadata1.detected_form == metadata2.detected_form:
            score += 0.2
        factors += 0.2
    
    # Harmonic progression similarity (0.2 weight)
    if metadata1.harmonic_progression and metadata2.harmonic_progression:
        prog1 = metadata1.harmonic_progression.split()[:10]  # First 10 chords
        prog2 = metadata2.harmonic_progression.split()[:10]
        if prog1 and prog2:
            matches = sum(1 for a, b in zip(prog1, prog2) if a == b)
            similarity = matches / max(len(prog1), len(prog2))
            score += 0.2 * similarity
        factors += 0.2
    
    # Melodic signature similarity (0.2 weight)
    if melodic1 and melodic2:
        min_len = min(len(melodic1), len(melodic2))
        if min_len >= 5:
            # Normalize to same starting pitch for comparison
            if melodic1 and melodic2:
                offset = melodic2[0] - melodic1[0]
                melodic2_normalized = [p - offset for p in melodic2[:min_len]]
                melodic1_normalized = melodic1[:min_len]
                
                # Count matching pitches
                matches = sum(1 for a, b in zip(melodic1_normalized, melodic2_normalized) if a == b)
                similarity = matches / min_len
                score += 0.2 * similarity
        factors += 0.2
    
    # Duration similarity (0.1 weight)
    if metadata1.duration_beats > 0 and metadata2.duration_beats > 0:
        duration_ratio = min(metadata1.duration_beats, metadata2.duration_beats) / max(
            metadata1.duration_beats, metadata2.duration_beats
        )
        score += 0.1 * duration_ratio
        factors += 0.1
    
    # Normalize by factors used
    if factors > 0:
        return score / factors
    return 0.0


def generate_suggested_name(
    metadata: FileMetadata,
    composition: Any,
    use_ai: bool = False,
) -> tuple[str, str, str | None, str | None]:
    """
    Generate a suggested name, ID, style, and description for a file.
    
    Returns:
        (name, id, style, description)
    """
    # Base name from filename (remove extension, clean up)
    base_name = Path(metadata.filename).stem
    base_name = base_name.replace("_", " ").replace("-", " ").title()
    
    # Build descriptive name
    name_parts: list[str] = []
    
    # Add key if detected
    if metadata.detected_key:
        name_parts.append(metadata.detected_key)
    
    # Add form if detected
    if metadata.detected_form:
        name_parts.append(metadata.detected_form.capitalize())
    
    # Add style hint if available
    style_hint = ""
    if metadata.detected_key:
        # Simple heuristic: minor keys often suggest Romantic/Baroque
        if "minor" in metadata.detected_key.lower():
            style_hint = "Romantic"
        elif metadata.detected_form in ["binary", "ternary"]:
            style_hint = "Classical"
    
    # If we have a good base name, use it; otherwise generate
    if len(base_name) > 3 and base_name.lower() not in ["midi", "track", "song", "piece"]:
        suggested_name = f"{base_name}"
        if metadata.detected_key:
            suggested_name += f" in {metadata.detected_key}"
    else:
        # Generate from analysis
        parts = []
        if metadata.detected_key:
            parts.append(metadata.detected_key)
        if metadata.detected_form:
            parts.append(metadata.detected_form)
        if metadata.motif_count > 0:
            parts.append(f"{metadata.motif_count} motifs")
        
        suggested_name = " - ".join(parts) if parts else "Musical Piece"
    
    # Generate ID (sanitized version of name)
    suggested_id = suggested_name.lower().replace(" ", "_").replace("-", "_")
    suggested_id = "".join(c for c in suggested_id if c.isalnum() or c == "_")
    suggested_id = suggested_id[:50]  # Limit length
    
    # Generate description
    description_parts: list[str] = []
    if metadata.detected_form:
        description_parts.append(f"{metadata.detected_form.capitalize()} form")
    if metadata.motif_count > 0:
        description_parts.append(f"{metadata.motif_count} motif(s)")
    if metadata.phrase_count > 0:
        description_parts.append(f"{metadata.phrase_count} phrase(s)")
    if metadata.chord_count > 0:
        description_parts.append(f"{metadata.chord_count} chord(s)")
    
    suggested_description = ", ".join(description_parts) if description_parts else "Musical composition"
    
    # Use AI for better naming if requested
    if use_ai and MUSIC21_AVAILABLE:
        try:
            from pianist.gemini import call_gemini
            from pianist.iterate import composition_to_canonical_json
            
            comp_json = composition_to_canonical_json(composition)
            
            prompt = f"""Analyze this musical composition and suggest:
1. A descriptive title (2-6 words)
2. Musical style (Baroque, Classical, Romantic, Modern, or Other)
3. A brief description (1 sentence)

Composition analysis:
- Key: {metadata.detected_key or 'Unknown'}
- Form: {metadata.detected_form or 'Unknown'}
- Motifs: {metadata.motif_count}
- Phrases: {metadata.phrase_count}
- Duration: {metadata.duration_beats:.1f} beats (~{metadata.bars:.1f} bars)

Composition JSON (first 1000 chars):
{comp_json[:1000]}

Respond in JSON format:
{{
  "title": "suggested title",
  "style": "Baroque|Classical|Romantic|Modern|Other",
  "description": "brief description"
}}"""
            
            response = call_gemini(prompt, model="gemini-flash-latest")
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group())
                suggested_name = ai_data.get("title", suggested_name)
                style_hint = ai_data.get("style", style_hint)
                suggested_description = ai_data.get("description", suggested_description)
        except Exception:
            # If AI fails, use generated values
            pass
    
    return suggested_name, suggested_id, style_hint, suggested_description


def analyze_file(
    file_path: Path,
    use_ai_quality: bool = False,
    use_ai_naming: bool = False,
) -> tuple[FileMetadata, list[int]]:
    """Analyze a single MIDI file and extract metadata."""
    # Run quality check
    quality_report = check_midi_file(file_path, use_ai=use_ai_quality)
    
    # Basic MIDI analysis
    midi_analysis = analyze_midi(file_path)
    
    # Convert to composition for musical analysis
    composition = None
    detected_key = None
    detected_form = None
    motif_count = 0
    phrase_count = 0
    chord_count = 0
    harmonic_progression = None
    
    melodic_signature: list[int] = []
    
    if MUSIC21_AVAILABLE:
        try:
            composition = composition_from_midi(file_path)
            
            # Musical analysis
            analysis = analyze_composition(composition)
            
            detected_key = analysis.harmonic_progression.key if analysis.harmonic_progression else None
            detected_form = analysis.form
            motif_count = len(analysis.motifs)
            phrase_count = len(analysis.phrases)
            
            if analysis.harmonic_progression:
                chord_count = len(analysis.harmonic_progression.chords)
                if analysis.harmonic_progression.progression:
                    harmonic_progression = " ".join(analysis.harmonic_progression.progression[:10])
            
            # Extract melodic signature for duplicate detection
            melodic_signature = extract_melodic_signature(composition)
        except Exception as e:
            # Analysis failed, continue with basic metadata
            pass
    
    # Extract metadata
    tempo_bpm = None
    if midi_analysis.tempo:
        tempo_bpm = midi_analysis.tempo[0].bpm
    
    time_sig = None
    if midi_analysis.time_signature:
        ts = midi_analysis.time_signature[0]
        time_sig = f"{ts.numerator}/{ts.denominator}"
    
    key_sig = None
    if midi_analysis.key_signature:
        key_sig = midi_analysis.key_signature[0].key
    
    # Generate suggested name
    if composition:
        suggested_name, suggested_id, suggested_style, suggested_description = generate_suggested_name(
            FileMetadata(
                filename=file_path.name,
                filepath=str(file_path),
                quality_score=quality_report.overall_score,
                quality_issues=len(quality_report.issues),
                duration_beats=midi_analysis.duration_beats,
                duration_seconds=midi_analysis.duration_seconds,
                bars=midi_analysis.estimated_bar_count,
                tempo_bpm=tempo_bpm,
                time_signature=time_sig,
                key_signature=key_sig,
                tracks=len(midi_analysis.tracks),
                detected_key=detected_key,
                detected_form=detected_form,
                motif_count=motif_count,
                phrase_count=phrase_count,
                chord_count=chord_count,
                harmonic_progression=harmonic_progression,
                suggested_name="",
                suggested_id="",
                suggested_style=None,
                suggested_description=None,
                similar_files=[],
                similarity_scores={},
                is_duplicate=False,
                duplicate_group=None,
                technical_score=quality_report.scores.get("technical", 0.0),
                musical_score=quality_report.scores.get("musical", 0.0),
                structure_score=quality_report.scores.get("structure", 0.0),
            ),
            composition,
            use_ai_naming,
        )
    else:
        suggested_name = Path(file_path).stem
        suggested_id = suggested_name.lower().replace(" ", "_")
        suggested_style = None
        suggested_description = "Musical composition"
    
    metadata = FileMetadata(
        filename=file_path.name,
        filepath=str(file_path),
        quality_score=quality_report.overall_score,
        quality_issues=len(quality_report.issues),
        duration_beats=midi_analysis.duration_beats,
        duration_seconds=midi_analysis.duration_seconds,
        bars=midi_analysis.estimated_bar_count,
        tempo_bpm=tempo_bpm,
        time_signature=time_sig,
        key_signature=key_sig,
        tracks=len(midi_analysis.tracks),
        detected_key=detected_key,
        detected_form=detected_form,
        motif_count=motif_count,
        phrase_count=phrase_count,
        chord_count=chord_count,
        harmonic_progression=harmonic_progression,
        suggested_name=suggested_name,
        suggested_id=suggested_id,
        suggested_style=suggested_style,
        suggested_description=suggested_description,
        similar_files=[],
        similarity_scores={},
        is_duplicate=False,
        duplicate_group=None,
        technical_score=quality_report.scores.get("technical", 0.0),
        musical_score=quality_report.scores.get("musical", 0.0),
        structure_score=quality_report.scores.get("structure", 0.0),
    )
    
    return metadata, melodic_signature


def detect_duplicates(
    all_metadata: list[FileMetadata],
    all_signatures: list[list[int]],
    similarity_threshold: float = 0.7,
) -> None:
    """Detect duplicate/similar files and group them."""
    # Compare all pairs
    for i, (meta1, sig1) in enumerate(zip(all_metadata, all_signatures)):
        for j, (meta2, sig2) in enumerate(zip(all_metadata, all_signatures)):
            if i >= j:
                continue
            
            similarity = calculate_similarity(meta1, meta2, sig1, sig2)
            
            if similarity >= similarity_threshold:
                meta1.similar_files.append(meta2.filename)
                meta1.similarity_scores[meta2.filename] = similarity
                meta2.similar_files.append(meta1.filename)
                meta2.similarity_scores[meta1.filename] = similarity
    
    # Group duplicates
    groups: dict[str, list[int]] = defaultdict(list)
    group_counter = 0
    
    for i, meta in enumerate(all_metadata):
        if meta.similar_files:
            # Check if already in a group
            found_group = None
            for group_name, group_indices in groups.items():
                if any(i in group_indices for similar_file in meta.similar_files):
                    found_group = group_name
                    break
            
            if found_group:
                groups[found_group].append(i)
            else:
                group_name = f"group_{group_counter}"
                groups[group_name].append(i)
                group_counter += 1
            
            meta.is_duplicate = True
    
    # Assign group names
    for group_name, group_indices in groups.items():
        for idx in group_indices:
            all_metadata[idx].duplicate_group = group_name


def write_csv_report(
    all_metadata: list[FileMetadata],
    output_path: Path,
) -> None:
    """Write CSV report with all metadata."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "quality_score",
                "suggested_name",
                "suggested_id",
                "suggested_style",
                "suggested_description",
                "detected_key",
                "detected_form",
                "duration_beats",
                "bars",
                "tempo_bpm",
                "time_signature",
                "motif_count",
                "phrase_count",
                "chord_count",
                "is_duplicate",
                "duplicate_group",
                "similar_files",
                "technical_score",
                "musical_score",
                "structure_score",
            ],
        )
        writer.writeheader()
        
        for meta in all_metadata:
            writer.writerow({
                "filename": meta.filename,
                "quality_score": f"{meta.quality_score:.3f}",
                "suggested_name": meta.suggested_name,
                "suggested_id": meta.suggested_id,
                "suggested_style": meta.suggested_style or "",
                "suggested_description": meta.suggested_description or "",
                "detected_key": meta.detected_key or "",
                "detected_form": meta.detected_form or "",
                "duration_beats": f"{meta.duration_beats:.1f}",
                "bars": f"{meta.bars:.1f}",
                "tempo_bpm": f"{meta.tempo_bpm:.1f}" if meta.tempo_bpm else "",
                "time_signature": meta.time_signature or "",
                "motif_count": meta.motif_count,
                "phrase_count": meta.phrase_count,
                "chord_count": meta.chord_count,
                "is_duplicate": "Yes" if meta.is_duplicate else "No",
                "duplicate_group": meta.duplicate_group or "",
                "similar_files": "; ".join(meta.similar_files),
                "technical_score": f"{meta.technical_score:.3f}",
                "musical_score": f"{meta.musical_score:.3f}",
                "structure_score": f"{meta.structure_score:.3f}",
            })


def write_json_report(
    all_metadata: list[FileMetadata],
    output_path: Path,
) -> None:
    """Write JSON report with all metadata."""
    data = {
        "total_files": len(all_metadata),
        "duplicate_groups": len(set(m.duplicate_group for m in all_metadata if m.duplicate_group)),
        "files": [asdict(meta) for meta in all_metadata],
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_file_hash(file_path: Path) -> str:
    """Generate a hash for a file path (for temp file naming)."""
    return hashlib.md5(str(file_path).encode()).hexdigest()


def save_file_result(
    metadata: FileMetadata,
    signature: list[int],
    temp_dir: Path,
    file_path: Path,
) -> None:
    """Save individual file analysis result to temp file."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_hash = get_file_hash(file_path)
    result_file = temp_dir / f"{file_hash}.json"
    
    data = {
        "metadata": asdict(metadata),
        "signature": signature,
        "source_file": str(file_path),
    }
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_file_result(
    temp_dir: Path,
    file_path: Path,
) -> tuple[FileMetadata, list[int]] | None:
    """Load individual file analysis result from temp file."""
    file_hash = get_file_hash(file_path)
    result_file = temp_dir / f"{file_hash}.json"
    
    if not result_file.exists():
        return None
    
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Reconstruct metadata
        metadata_dict = data["metadata"]
        metadata = FileMetadata(**metadata_dict)
        signature = data.get("signature", [])
        
        return metadata, signature
    except Exception:
        return None


def load_all_results(temp_dir: Path) -> tuple[list[FileMetadata], list[list[int]]]:
    """Load all saved results from temp directory."""
    all_metadata: list[FileMetadata] = []
    all_signatures: list[list[int]] = []
    
    if not temp_dir.exists():
        return all_metadata, all_signatures
    
    # Load all JSON files
    for result_file in temp_dir.glob("*.json"):
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            metadata_dict = data["metadata"]
            metadata = FileMetadata(**metadata_dict)
            signature = data.get("signature", [])
            
            all_metadata.append(metadata)
            all_signatures.append(signature)
        except Exception:
            continue
    
    return all_metadata, all_signatures


def clear_temp_results(temp_dir: Path) -> None:
    """Clear all temporary result files."""
    if temp_dir.exists():
        for result_file in temp_dir.glob("*.json"):
            result_file.unlink()
        if temp_dir.exists() and not any(temp_dir.iterdir()):
            temp_dir.rmdir()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Review, analyze, and categorize MIDI files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--dir",
        type=Path,
        required=True,
        help="Directory containing MIDI files",
    )
    
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.mid",
        help="Glob pattern for files (default: *.mid)",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output CSV file path (default: review_report.csv)",
    )
    
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Output JSON file path (optional)",
    )
    
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Use AI for quality assessment and naming",
    )
    
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for duplicate detection (0.0-1.0, default: 0.7)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit analysis to first N files (for testing)",
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous run (skip already-analyzed files)",
    )
    
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cached results and start fresh",
    )
    
    parser.add_argument(
        "--temp-dir",
        type=Path,
        help="Directory for temporary result files (default: .midi_review_cache)",
    )
    
    args = parser.parse_args()
    
    # Set up temp directory
    temp_dir = args.temp_dir or Path(".midi_review_cache")
    
    # Clear cache if requested
    if args.clear_cache:
        print("Clearing cached results...")
        clear_temp_results(temp_dir)
    
    # Find MIDI files
    files = list(args.dir.glob(args.pattern)) + list(args.dir.glob("*.midi"))
    if not files:
        print(f"Error: No MIDI files found in {args.dir}", file=sys.stderr)
        return 1
    
    # Sort files for consistent ordering
    files = sorted(files)
    
    # Apply limit for testing
    if args.limit:
        files = files[:args.limit]
        print(f"Testing mode: Limited to first {args.limit} files")
    
    print(f"Found {len(files)} MIDI file(s) to analyze")
    
    # Load existing results if resuming
    existing_results: dict[str, tuple[FileMetadata, list[int]]] = {}
    if args.resume:
        print("Loading existing results...")
        # Load all cached results
        for result_file in temp_dir.glob("*.json") if temp_dir.exists() else []:
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                source_file = data.get("source_file")
                if source_file:
                    metadata_dict = data["metadata"]
                    metadata = FileMetadata(**metadata_dict)
                    signature = data.get("signature", [])
                    existing_results[source_file] = (metadata, signature)
            except Exception:
                continue
        print(f"Found {len(existing_results)} previously analyzed files")
    
    # Analyze files
    all_metadata: list[FileMetadata] = []
    all_signatures: list[list[int]] = []
    analyzed_count = 0
    skipped_count = 0
    
    for i, file_path in enumerate(files, 1):
        file_str = str(file_path)
        
        # Check if we already have results for this file
        if args.resume and file_str in existing_results:
            if args.verbose:
                print(f"[{i}/{len(files)}] Skipping (already analyzed): {file_path.name}")
            meta, sig = existing_results[file_str]
            all_metadata.append(meta)
            all_signatures.append(sig)
            skipped_count += 1
            continue
        
        # Analyze new file
        if args.verbose:
            print(f"[{i}/{len(files)}] Analyzing: {file_path.name}")
        else:
            print(f"[{i}/{len(files)}] Analyzing: {file_path.name}")
        
        try:
            metadata, signature = analyze_file(
                file_path,
                use_ai_quality=args.ai,
                use_ai_naming=args.ai,
            )
            
            # Save result immediately
            save_file_result(metadata, signature, temp_dir, file_path)
            
            all_metadata.append(metadata)
            all_signatures.append(signature)
            analyzed_count += 1
        except KeyboardInterrupt:
            print(f"\n\nInterrupted! Progress saved. {analyzed_count} files analyzed, {skipped_count} skipped.")
            print(f"Run with --resume to continue from here.")
            # Still write what we have so far
            if all_metadata:
                output_csv = args.output or Path("review_report.csv")
                write_csv_report(all_metadata, output_csv)
                print(f"Partial report written to: {output_csv}")
            return 130  # Exit code for interrupted
        except Exception as e:
            print(f"Error analyzing {file_path.name}: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            continue
    
    print(f"\nAnalysis complete:")
    print(f"  Analyzed: {analyzed_count} new files")
    print(f"  Skipped: {skipped_count} previously analyzed files")
    print(f"  Total: {len(all_metadata)} files")
    
    if len(all_metadata) == 0:
        print("No files to process.", file=sys.stderr)
        return 1
    
    print(f"\nDetecting duplicates (threshold: {args.similarity_threshold})...")
    
    # Detect duplicates
    detect_duplicates(all_metadata, all_signatures, args.similarity_threshold)
    
    # Print summary
    duplicates = [m for m in all_metadata if m.is_duplicate]
    print(f"\nSummary:")
    print(f"  Total files: {len(all_metadata)}")
    print(f"  Duplicates found: {len(duplicates)}")
    print(f"  Unique files: {len(all_metadata) - len(duplicates)}")
    
    if duplicates:
        print(f"\nDuplicate groups:")
        groups = defaultdict(list)
        for meta in duplicates:
            if meta.duplicate_group:
                groups[meta.duplicate_group].append(meta.filename)
        for group_name, filenames in groups.items():
            print(f"  {group_name}: {', '.join(filenames)}")
    
    # Write reports
    output_csv = args.output or Path("review_report.csv")
    write_csv_report(all_metadata, output_csv)
    print(f"\nCSV report written to: {output_csv}")
    
    if args.json_output:
        write_json_report(all_metadata, args.json_output)
        print(f"JSON report written to: {args.json_output}")
    
    print(f"\nTemporary results saved in: {temp_dir}")
    print(f"  (Use --resume to continue from here, or --clear-cache to start fresh)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

