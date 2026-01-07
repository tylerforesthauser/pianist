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

    # Resume and retry AI on files that didn't use AI or failed to identify
    python3 scripts/review_and_categorize_midi.py --dir references/ --resume --ai --retry-ai --output review_report.csv

    # Force AI re-identification on all cached files (even if already identified)
    python3 scripts/review_and_categorize_midi.py --dir references/ --resume --ai --force-ai --output review_report.csv

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
import os
import re
import sys
import time
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


def call_ollama(model: str, prompt: str, verbose: bool = False) -> str:
    """
    Call a local Ollama model.
    
    Requires Ollama to be installed and running locally.
    Install: https://ollama.ai
    
    Example models: gpt-oss:20b, gemma3:4b, deepseek-r1:8b
    """
    try:
        import requests
    except ImportError:
        raise RuntimeError(
            "requests library required for Ollama support. Install with: pip install requests"
        )
    
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    if verbose:
        print(f"  [Ollama] Calling {model} at {ollama_url}...", file=sys.stderr)
    
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=3600,  # 1 hour timeout (large compositions and complex models like deepseek-r1 can take significant time)
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not connect to Ollama at {ollama_url}. "
            "Make sure Ollama is installed and running. See: https://ollama.ai"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Ollama request timed out after 3600 seconds (1 hour). Very large compositions or complex models may require more time.")
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")


def identify_composition_with_ai(
    metadata: FileMetadata,
    composition: Any,
    filename: str,
    provider: str = "gemini",
    model: str = "gemini-flash-latest",
    verbose: bool = False,
    delay_seconds: float = 0.0,
) -> dict[str, Any] | None:
    """
    Use AI to identify a well-known composition based on musical characteristics.
    
    Returns:
        Dictionary with identified composition info, or None if not identified
    """
    if not MUSIC21_AVAILABLE:
        if verbose:
            print(f"  [AI] music21 not available, skipping AI identification", file=sys.stderr)
        return None
    
    try:
        from pianist.iterate import composition_to_canonical_json
        
        if verbose:
            print(f"  [AI] Attempting to identify composition using {provider}...", file=sys.stderr)
        
        # Add delay to avoid rate limits
        if delay_seconds > 0:
            if verbose:
                print(f"  [AI] Waiting {delay_seconds:.1f}s to avoid rate limits...", file=sys.stderr)
            time.sleep(delay_seconds)
        
        comp_json = composition_to_canonical_json(composition)
        
        # Extract key musical characteristics for identification
        harmonic_prog = metadata.harmonic_progression or "Unknown"
        if harmonic_prog and len(harmonic_prog) > 200:
            harmonic_prog = harmonic_prog[:200] + "..."
        
        prompt = f"""You are a musicologist identifying classical piano compositions.

Analyze this MIDI file and try to identify if it's a well-known composition.

Filename: {filename}
Key: {metadata.detected_key or 'Unknown'}
Form: {metadata.detected_form or 'Unknown'}
Time Signature: {metadata.time_signature or 'Unknown'}
Tempo: {metadata.tempo_bpm or 'Unknown'} BPM
Duration: {metadata.duration_beats:.1f} beats (~{metadata.bars:.1f} bars)
Motifs: {metadata.motif_count}
Phrases: {metadata.phrase_count}
Harmonic progression (first part): {harmonic_prog}

Musical content (first 2000 characters):
{comp_json[:2000]}

If you can identify this as a well-known composition, respond with JSON:
{{
  "identified": true,
  "composer": "Composer name (e.g., 'J.S. Bach', 'Chopin', 'Beethoven')",
  "title": "Full composition title (e.g., 'Two-Part Invention No. 8 in F major, BWV 779')",
  "catalog_number": "Catalog number if applicable (e.g., 'BWV 779', 'Op. 11 No. 4')",
  "style": "Baroque|Classical|Romantic|Modern|Other",
  "form": "binary|ternary|sonata|invention|prelude|etude|etc.",
  "description": "Brief description of the piece and what it demonstrates",
  "confidence": "high|medium|low"
}}

If you cannot identify it as a well-known composition, respond with:
{{
  "identified": false,
  "suggested_title": "Descriptive title based on characteristics",
  "style": "Baroque|Classical|Romantic|Modern|Other",
  "form": "{metadata.detected_form or 'unknown'}",
  "description": "Brief description based on musical analysis"
}}

Respond ONLY with valid JSON, no other text."""
        
        # Call appropriate provider
        if provider == "ollama":
            try:
                response = call_ollama(model=model, prompt=prompt, verbose=verbose)
            except RuntimeError as e:
                if verbose:
                    print(f"  [AI] {e}", file=sys.stderr)
                return None
        else:  # gemini
            try:
                from pianist.ai_providers import generate_text
                response = generate_text(model=model, prompt=prompt, verbose=verbose)
            except Exception as e:
                # Check if it's a rate limit error
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if verbose:
                        print(f"  [AI] Rate limit exceeded. Consider using --ai-delay or --ai-provider ollama", file=sys.stderr)
                    return None
                raise  # Re-raise other errors
        
        if verbose:
            print(f"  [AI] Received response (length: {len(response)})", file=sys.stderr)
        
        # Try to parse JSON from response
        # Look for JSON object (handles multi-line)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        if json_match:
            try:
                ai_data = json.loads(json_match.group())
                if verbose:
                    identified = ai_data.get("identified", False)
                    print(f"  [AI] Identification result: identified={identified}", file=sys.stderr)
                return ai_data
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"  [AI] JSON parse error: {e}", file=sys.stderr)
                # Try to fix common JSON issues
                json_str = json_match.group()
                # Remove trailing commas
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                try:
                    ai_data = json.loads(json_str)
                    if verbose:
                        print(f"  [AI] Successfully parsed after fixing JSON", file=sys.stderr)
                    return ai_data
                except json.JSONDecodeError as e2:
                    if verbose:
                        print(f"  [AI] Still failed to parse JSON: {e2}", file=sys.stderr)
                        print(f"  [AI] Response snippet: {response[:200]}", file=sys.stderr)
        else:
            if verbose:
                print(f"  [AI] No JSON found in response", file=sys.stderr)
    except ImportError as e:
        if verbose:
            print(f"  [AI] Import error: {e}", file=sys.stderr)
    except Exception as e:
        if verbose:
            print(f"  [AI] Error during identification: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    return None


def extract_info_from_filename(filename: str) -> dict[str, Any]:
    """
    Extract composition information from filename patterns.
    
    Common patterns:
    - "bach-invention-8-bwv-779.mid" -> composer, title, catalog
    - "chopin-prelude-op28-no4.mid" -> composer, opus
    - "scriabin-etude-op2-no1.mid" -> composer, opus
    """
    info: dict[str, Any] = {
        "composer": None,
        "title": None,
        "catalog_number": None,
        "opus": None,
    }
    
    filename_lower = filename.lower()
    
    # Common composer patterns
    composer_patterns = {
        "bach": "J.S. Bach",
        "beethoven": "Beethoven",
        "mozart": "Mozart",
        "chopin": "Chopin",
        "scriabin": "Scriabin",
        "debussy": "Debussy",
        "rachmaninoff": "Rachmaninoff",
        "schubert": "Schubert",
        "schumann": "Schumann",
        "liszt": "Liszt",
        "brahms": "Brahms",
    }
    
    for pattern, composer in composer_patterns.items():
        if pattern in filename_lower:
            info["composer"] = composer
            break
    
    # Extract BWV numbers (Bach)
    bwv_match = re.search(r'bwv[.\s-]*(\d+)', filename_lower)
    if bwv_match:
        info["catalog_number"] = f"BWV {bwv_match.group(1)}"
        if not info["composer"]:
            info["composer"] = "J.S. Bach"
    
    # Extract Opus numbers
    opus_match = re.search(r'op[.\s-]*(\d+)(?:\s*no[.\s-]*(\d+))?', filename_lower)
    if opus_match:
        opus_num = opus_match.group(1)
        no_num = opus_match.group(2)
        if no_num:
            info["opus"] = f"Op. {opus_num} No. {no_num}"
        else:
            info["opus"] = f"Op. {opus_num}"
        info["catalog_number"] = info["opus"]
    
    # Extract common piece types
    piece_types = {
        "invention": "Invention",
        "prelude": "Prelude",
        "etude": "Étude",
        "sonata": "Sonata",
        "nocturne": "Nocturne",
        "waltz": "Waltz",
        "mazurka": "Mazurka",
        "impromptu": "Impromptu",
    }
    
    for pattern, piece_type in piece_types.items():
        if pattern in filename_lower:
            info["title"] = piece_type
            break
    
    return info


def generate_suggested_name(
    metadata: FileMetadata,
    composition: Any,
    use_ai: bool = False,
    verbose: bool = False,
    ai_provider: str = "gemini",
    ai_model: str | None = None,
    ai_delay: float = 0.0,
) -> tuple[str, str, str | None, str | None, bool]:
    """
    Generate a suggested name, ID, style, and description for a file.
    
    Uses multiple strategies:
    1. Try AI identification (if use_ai=True) to identify well-known compositions
    2. Extract info from filename patterns
    3. Fall back to analysis-based generation
    
    Returns:
        (name, id, style, description, ai_identified)
        where ai_identified is True if AI successfully identified the composition
    """
    filename = metadata.filename
    ai_identified = False
    
    # Strategy 1: Try AI identification if enabled
    if use_ai and MUSIC21_AVAILABLE:
        # Set default model if not provided
        if ai_model is None:
            ai_model = "gemini-flash-latest" if ai_provider == "gemini" else "gpt-oss:20b"
        
        ai_identification = identify_composition_with_ai(
            metadata, composition, filename,
            provider=ai_provider,
            model=ai_model,
            verbose=verbose,
            delay_seconds=ai_delay,
        )
        if ai_identification and ai_identification.get("identified"):
            # We identified a well-known composition!
            ai_identified = True
            composer = ai_identification.get("composer", "")
            title = ai_identification.get("title", "")
            catalog = ai_identification.get("catalog_number", "")
            
            # Build full title
            if composer and title:
                if catalog:
                    suggested_name = f"{composer}: {title} ({catalog})"
                else:
                    suggested_name = f"{composer}: {title}"
            else:
                suggested_name = title or composer or "Identified Composition"
            
            style_hint = ai_identification.get("style")
            suggested_description = ai_identification.get("description", "Well-known classical composition")
            
            # Generate ID
            suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
            suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
            suggested_id = suggested_id[:50]
            
            return suggested_name, suggested_id, style_hint, suggested_description, ai_identified
        elif ai_identification and not ai_identification.get("identified"):
            # AI couldn't identify but provided suggestions
            suggested_name = ai_identification.get("suggested_title", "")
            style_hint = ai_identification.get("style")
            suggested_description = ai_identification.get("description", "")
            if suggested_name:
                suggested_id = suggested_name.lower().replace(" ", "_")
                suggested_id = "".join(c for c in suggested_id if c.isalnum() or c == "_")
                suggested_id = suggested_id[:50]
                return suggested_name, suggested_id, style_hint, suggested_description, ai_identified
    
    # Strategy 2: Extract info from filename
    filename_info = extract_info_from_filename(filename)
    
    if filename_info.get("composer") and (filename_info.get("title") or filename_info.get("catalog_number")):
        # We have composer + title/catalog from filename
        parts = [filename_info["composer"]]
        if filename_info.get("title"):
            parts.append(filename_info["title"])
        if filename_info.get("catalog_number"):
            parts.append(f"({filename_info['catalog_number']})")
        suggested_name = ": ".join(parts)
        
        # Infer style from composer
        composer_lower = filename_info["composer"].lower()
        if "bach" in composer_lower:
            style_hint = "Baroque"
        elif "mozart" in composer_lower or "beethoven" in composer_lower:
            style_hint = "Classical"
        elif any(c in composer_lower for c in ["chopin", "schumann", "liszt", "rachmaninoff", "scriabin"]):
            style_hint = "Romantic"
        else:
            style_hint = None
        
        suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
        suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
        suggested_id = suggested_id[:50]
        
        # Build description
        description_parts = []
        if filename_info.get("title"):
            description_parts.append(filename_info["title"])
        if metadata.detected_form:
            description_parts.append(f"{metadata.detected_form} form")
        suggested_description = ", ".join(description_parts) if description_parts else "Classical composition"
        
        return suggested_name, suggested_id, style_hint, suggested_description, ai_identified
    
    # Strategy 3: Fall back to analysis-based generation
    base_name = Path(filename).stem
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
    
    return suggested_name, suggested_id, style_hint, suggested_description, ai_identified


def analyze_file(
    file_path: Path,
    use_ai_quality: bool = False,
    use_ai_naming: bool = False,
    verbose: bool = False,
    ai_provider: str = "gemini",
    ai_model: str | None = None,
    ai_delay: float = 0.0,
) -> tuple[FileMetadata, list[int], bool, bool]:
    """
    Analyze a single MIDI file and extract metadata.
    
    Returns:
        (metadata, melodic_signature, ai_attempted, ai_identified)
    """
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
    
    # Track AI usage
    ai_attempted = False
    ai_identified = False
    
    # Generate suggested name
    if composition:
        # Create temporary metadata for name generation
        temp_metadata = FileMetadata(
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
        )
        
        # Track if AI is being used
        if use_ai_naming and MUSIC21_AVAILABLE:
            ai_attempted = True
        
        suggested_name, suggested_id, suggested_style, suggested_description, ai_identified = generate_suggested_name(
            temp_metadata,
            composition,
            use_ai=use_ai_naming,
            verbose=verbose,
            ai_provider=ai_provider,
            ai_model=ai_model,
            ai_delay=ai_delay,
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
    
    return metadata, melodic_signature, ai_attempted, ai_identified


def detect_duplicates_incremental(
    new_metadata: FileMetadata,
    new_signature: list[int],
    existing_metadata: list[FileMetadata],
    existing_signatures: list[list[int]],
    similarity_threshold: float = 0.7,
) -> None:
    """
    Detect duplicates for a new file against existing files.
    
    Updates both the new file's metadata and existing files' metadata if duplicates are found.
    """
    # Compare new file against all existing files
    for existing_meta, existing_sig in zip(existing_metadata, existing_signatures):
        similarity = calculate_similarity(new_metadata, existing_meta, new_signature, existing_sig)
        
        if similarity >= similarity_threshold:
            new_metadata.similar_files.append(existing_meta.filename)
            new_metadata.similarity_scores[existing_meta.filename] = similarity
            existing_meta.similar_files.append(new_metadata.filename)
            existing_meta.similarity_scores[new_metadata.filename] = similarity


def assign_duplicate_groups(
    all_metadata: list[FileMetadata],
) -> None:
    """
    Assign duplicate group names to all files with similar files.
    
    This should be called after all incremental duplicate detection is complete.
    """
    groups: dict[str, list[int]] = defaultdict(list)
    group_counter = 0
    
    for i, meta in enumerate(all_metadata):
        if meta.similar_files:
            # Check if already in a group
            found_group = None
            for group_name, group_indices in groups.items():
                # Check if any file in this group is similar to the current file
                for idx in group_indices:
                    if all_metadata[idx].filename in meta.similar_files:
                        found_group = group_name
                        break
                if found_group:
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


def detect_duplicates(
    all_metadata: list[FileMetadata],
    all_signatures: list[list[int]],
    similarity_threshold: float = 0.7,
) -> None:
    """
    Detect duplicate/similar files and group them.
    
    This is the full batch version - compares all pairs.
    For incremental detection, use detect_duplicates_incremental instead.
    """
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
    
    # Assign duplicate groups
    assign_duplicate_groups(all_metadata)


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


def format_elapsed_time(seconds: float) -> str:
    """
    Format elapsed time in a human-readable format.
    
    Returns:
        Formatted string (e.g., "2.34s", "1m 23s", "2h 15m")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{hours}h"


def get_file_hash(file_path: Path) -> str:
    """Generate a hash for a file path (for temp file naming)."""
    return hashlib.md5(str(file_path).encode()).hexdigest()


def save_file_result(
    metadata: FileMetadata,
    signature: list[int],
    temp_dir: Path,
    file_path: Path,
    ai_attempted: bool = False,
    ai_identified: bool = False,
) -> None:
    """Save individual file analysis result to temp file."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_hash = get_file_hash(file_path)
    result_file = temp_dir / f"{file_hash}.json"
    
    data = {
        "metadata": asdict(metadata),
        "signature": signature,
        "source_file": str(file_path),
        "ai_attempted": ai_attempted,
        "ai_identified": ai_identified,
    }
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_file_result(
    temp_dir: Path,
    file_path: Path,
) -> tuple[FileMetadata, list[int], bool, bool] | None:
    """
    Load individual file analysis result from temp file.
    
    Returns:
        (metadata, signature, ai_attempted, ai_identified) or None if not found
    """
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
        ai_attempted = data.get("ai_attempted", False)
        ai_identified = data.get("ai_identified", False)
        
        return metadata, signature, ai_attempted, ai_identified
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
        "--ai-provider",
        type=str,
        choices=["gemini", "ollama"],
        default=os.getenv("AI_PROVIDER", "gemini"),
        help="AI provider to use: 'gemini' (cloud) or 'ollama' (local). Default: gemini",
    )
    
    parser.add_argument(
        "--ai-model",
        type=str,
        help="AI model name. Default: gemini-flash-latest (Gemini) or gpt-oss:20b (Ollama)",
    )
    
    parser.add_argument(
        "--ai-delay",
        type=float,
        default=float(os.getenv("AI_DELAY_SECONDS", "0")),
        help="Delay in seconds between AI calls to avoid rate limits (default: 0)",
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
    
    parser.add_argument(
        "--retry-ai",
        action="store_true",
        help="Re-run AI identification on cached files that didn't use AI or failed to identify (requires --resume and --ai)",
    )
    
    parser.add_argument(
        "--force-ai",
        action="store_true",
        help="Force AI re-identification on all cached files, even if AI already successfully identified them (requires --resume and --ai)",
    )
    
    args = parser.parse_args()
    
    # Validate flag combinations
    if args.force_ai and not (args.resume and args.ai):
        parser.error("--force-ai requires both --resume and --ai flags")
    
    if args.retry_ai and not (args.resume and args.ai):
        parser.error("--retry-ai requires both --resume and --ai flags")
    
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
    
    # Sort files by size (smallest to largest) for consistent ordering
    files = sorted(files, key=lambda f: f.stat().st_size)
    
    # Apply limit for testing
    if args.limit:
        files = files[:args.limit]
        print(f"Testing mode: Limited to first {args.limit} files")
    
    print(f"Found {len(files)} MIDI file(s) to analyze")
    
    # Load existing results if resuming
    existing_results: dict[str, tuple[FileMetadata, list[int], bool, bool]] = {}
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
                    ai_attempted = data.get("ai_attempted", False)
                    ai_identified = data.get("ai_identified", False)
                    existing_results[source_file] = (metadata, signature, ai_attempted, ai_identified)
            except Exception:
                continue
        print(f"Found {len(existing_results)} previously analyzed files")
        
        # Check if loaded files need duplicate detection (in case script was interrupted)
        # A file needs duplicate detection if it has no similar_files entries and is_duplicate is False
        # This indicates duplicate detection was never run (interrupted before completion)
        loaded_metadata_list = [meta for meta, _, _, _ in existing_results.values()]
        needs_duplicate_detection = any(
            not meta.similar_files and not meta.is_duplicate 
            for meta in loaded_metadata_list
        )
        if needs_duplicate_detection and len(loaded_metadata_list) > 1:
            if args.verbose:
                print("Running duplicate detection on loaded files...")
            loaded_signatures_list = [sig for _, sig, _, _ in existing_results.values()]
            detect_duplicates(loaded_metadata_list, loaded_signatures_list, args.similarity_threshold)
            # Save updated results with duplicate detection
            for meta, sig, ai_attempted, ai_identified in existing_results.values():
                file_path = Path(meta.filepath)
                save_file_result(meta, sig, temp_dir, file_path, ai_attempted, ai_identified)
    
    # Analyze files
    all_metadata: list[FileMetadata] = []
    all_signatures: list[list[int]] = []
    # Track AI info for newly analyzed files to avoid reloading from cache
    file_ai_info: dict[str, tuple[list[int], bool, bool]] = {}
    analyzed_count = 0
    skipped_count = 0
    
    for i, file_path in enumerate(files, 1):
        file_str = str(file_path)
        
        # Check if we already have results for this file
        should_retry_ai = False
        should_force_ai = False
        if args.resume and file_str in existing_results:
            meta, sig, cached_ai_attempted, cached_ai_identified = existing_results[file_str]
            
            # Check if we should force AI (overrides retry-ai logic)
            if args.force_ai and args.ai:
                should_force_ai = True
                if args.verbose:
                    print(f"[{i}/{len(files)}] Re-analyzing with AI (forced): {file_path.name}")
            # Check if we should retry AI
            elif args.retry_ai and args.ai:
                # Retry if: AI wasn't attempted before, or AI was attempted but didn't identify
                if not cached_ai_attempted or (cached_ai_attempted and not cached_ai_identified):
                    should_retry_ai = True
                    if args.verbose:
                        reason = "AI not attempted" if not cached_ai_attempted else "AI failed to identify"
                        print(f"[{i}/{len(files)}] Re-analyzing with AI ({reason}): {file_path.name}")
                else:
                    # AI already identified, skip
                    if args.verbose:
                        print(f"[{i}/{len(files)}] Skipping (already analyzed, AI identified): {file_path.name}")
                    all_metadata.append(meta)
                    all_signatures.append(sig)
                    skipped_count += 1
                    continue
            else:
                # Normal resume - skip already analyzed files
                if args.verbose:
                    print(f"[{i}/{len(files)}] Skipping (already analyzed): {file_path.name}")
                all_metadata.append(meta)
                all_signatures.append(sig)
                skipped_count += 1
                continue
        
        # Analyze new file (or re-analyze with AI)
        if args.verbose:
            print(f"[{i}/{len(files)}] Analyzing: {file_path.name}")
        else:
            print(f"[{i}/{len(files)}] Analyzing: {file_path.name}")
        
        try:
            start_time = time.time()
            
            # Set default model if not provided
            ai_model = args.ai_model
            if ai_model is None:
                ai_model = "gemini-flash-latest" if args.ai_provider == "gemini" else "llama3.2"
            
            # Run analysis (including any retry/force logic decided earlier) with AI parameters
            metadata, signature, ai_attempted, ai_identified = analyze_file(
                file_path,
                use_ai_quality=args.ai,
                use_ai_naming=args.ai,
                verbose=args.verbose,
                ai_provider=args.ai_provider,
                ai_model=ai_model,
                ai_delay=args.ai_delay,
            )
            
            elapsed_time = time.time() - start_time
            
            if args.verbose:
                print(f"  Processing time: {format_elapsed_time(elapsed_time)}", file=sys.stderr)
            
            # Run incremental duplicate detection against already processed files
            # This compares the new file against all previously processed files (including skipped ones)
            # Note: We compare before adding to all_metadata to avoid self-comparison
            detect_duplicates_incremental(
                metadata,
                signature,
                all_metadata,
                all_signatures,
                args.similarity_threshold,
            )
            
            # Add to lists after duplicate detection (to avoid self-comparison)
            all_metadata.append(metadata)
            all_signatures.append(signature)
            # Track AI info for efficient saving at the end
            file_ai_info[str(file_path)] = (signature, ai_attempted, ai_identified)
            
            # Assign/update duplicate groups periodically (every 10 files) or at the end
            # This is more efficient than calling after every file
            # Note: We call assign_duplicate_groups on all_metadata (not all_metadata + [metadata])
            # because metadata is already appended above, and the function modifies objects in place
            if len(all_metadata) % 10 == 0:
                assign_duplicate_groups(all_metadata)
            
            # Save result immediately (includes duplicate detection results)
            save_file_result(metadata, signature, temp_dir, file_path, ai_attempted, ai_identified)
            
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
    
    # Duplicate detection was done incrementally during processing
    # Just ensure all groups are properly assigned
    print(f"\nFinalizing duplicate groups (threshold: {args.similarity_threshold})...")
    assign_duplicate_groups(all_metadata)
    
    # Save all results with updated duplicate detection info
    # This ensures that duplicate detection results are persisted even if script is interrupted
    if args.verbose:
        print("Saving all results with duplicate detection updates...")
    
    # Create a mapping of filepath to (signature, ai_attempted, ai_identified)
    file_info_map: dict[str, tuple[list[int], bool, bool]] = {}
    
    # Add info from existing results (loaded from cache)
    for file_str, (_, sig, ai_att, ai_id) in existing_results.items():
        file_info_map[file_str] = (sig, ai_att, ai_id)
    
    # Add info from newly analyzed files (tracked during processing)
    file_info_map.update(file_ai_info)
    
    # Validate that all_metadata and all_signatures have the same length
    # They should always be parallel lists
    if len(all_metadata) != len(all_signatures):
        print(f"Warning: all_metadata ({len(all_metadata)}) and all_signatures ({len(all_signatures)}) have different lengths", file=sys.stderr)
    
    # For any files not in the map (shouldn't happen, but handle gracefully)
    for i, metadata in enumerate(all_metadata):
        file_str = str(metadata.filepath)
        if file_str not in file_info_map:
            if i < len(all_signatures):
                # Fallback: use signature from all_signatures, assume no AI
                file_info_map[file_str] = (all_signatures[i], False, False)
            else:
                # Last resort: try to load from cache
                result = load_file_result(temp_dir, Path(metadata.filepath))
                if result:
                    _, sig, ai_att, ai_id = result
                    file_info_map[file_str] = (sig, ai_att, ai_id)
    
    # Save all metadata with updated duplicate detection
    for metadata in all_metadata:
        file_path = Path(metadata.filepath)
        file_str = str(file_path)
        if file_str in file_info_map:
            signature, ai_attempted, ai_identified = file_info_map[file_str]
            save_file_result(metadata, signature, temp_dir, file_path, ai_attempted, ai_identified)
    
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

