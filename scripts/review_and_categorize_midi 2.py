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

    # Review directory of MIDI files
    python3 scripts/review_and_categorize_midi.py --dir references/ --output review_report.csv

    # Review with specific AI provider
    python3 scripts/review_and_categorize_midi.py --dir references/ --ai-provider ollama --output review_report.csv

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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Suppress PedalEvent warnings from iterate.py (they're informational, not errors)
# These warnings occur when MIDI files have pedal events with duration=0
# We suppress them to reduce output clutter during batch processing
warnings.filterwarnings("ignore", message=".*PedalEvent.*duration=0.*", category=UserWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pianist.iterate")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.comprehensive_analysis import analyze_for_user
from pianist.iterate import composition_from_midi

# ============================================================================
# COMPOSER PATTERNS - Use unified definitions from core module
# ============================================================================
# Import composer definitions from the unified midi_identification module
# This ensures consistency across the codebase
from pianist.midi_identification import COMPOSER_DEFINITIONS
from pianist.midi_identification import (
    identify_midi_file as identify_midi_file_new,
)
from pianist.musical_analysis import (
    MUSIC21_AVAILABLE,
    ChordAnalysis,
    HarmonicAnalysis,
    Motif,
    MusicalAnalysis,
    Phrase,
)

# Import quality checking functions from core module
from pianist.quality import check_midi_file


def _build_composer_patterns() -> dict[str, dict[str, Any]]:
    """
    Build composer pattern dictionaries from COMPOSER_DEFINITIONS.

    Returns:
        dict with keys:
        - "regex_patterns": dict mapping regex patterns to canonical names
        - "simple_patterns": dict mapping simple names to canonical names
        - "end_patterns": dict mapping end-of-filename patterns to canonical names
    """
    regex_patterns: dict[str, str] = {}
    simple_patterns: dict[str, str] = {}
    end_patterns: dict[str, str] = {}

    for canonical, defn in COMPOSER_DEFINITIONS.items():
        # Add full name regex patterns
        for full_name in defn["full_names"]:
            # Escape special regex chars and create word boundary pattern
            escaped = re.escape(full_name)
            pattern = rf"\b{escaped}\b"
            regex_patterns[pattern] = canonical

        # Add abbreviation patterns
        for abbrev in defn["abbreviations"]:
            escaped = re.escape(abbrev)
            pattern = rf"\b{escaped}\b"
            regex_patterns[pattern] = canonical

        # Add simple patterns (for substring matching)
        for simple in defn["simple"]:
            simple_patterns[simple] = canonical

        # Add end patterns (for "Title -- Composer" format)
        # Include full names, simple names, and abbreviations
        for full_name in defn["full_names"]:
            end_patterns[full_name] = canonical
        for simple in defn["simple"]:
            end_patterns[simple] = canonical
        for abbrev in defn["abbreviations"]:
            end_patterns[abbrev] = canonical

    return {
        "regex_patterns": regex_patterns,
        "simple_patterns": simple_patterns,
        "end_patterns": end_patterns,
    }


# Build pattern dictionaries once at module load
_COMPOSER_PATTERNS = _build_composer_patterns()
COMPOSER_REGEX_PATTERNS = _COMPOSER_PATTERNS["regex_patterns"]
COMPOSER_SIMPLE_PATTERNS = _COMPOSER_PATTERNS["simple_patterns"]
COMPOSER_END_PATTERNS = _COMPOSER_PATTERNS["end_patterns"]


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

    # Original composition flag
    is_original: bool


def _reconstruct_musical_analysis(musical_dict: dict[str, Any]) -> MusicalAnalysis | None:
    """
    Reconstruct MusicalAnalysis object from dictionary format.

    This allows us to pass pre-computed analysis to check_midi_file,
    avoiding redundant computation.

    Args:
        musical_dict: Dictionary from _format_musical_analysis()

    Returns:
        MusicalAnalysis object or None if reconstruction fails
    """
    if not musical_dict or not MUSIC21_AVAILABLE:
        return None

    try:
        # Reconstruct motifs
        motifs = []
        for m_dict in musical_dict.get("motifs", []):
            motifs.append(
                Motif(
                    start=m_dict.get("start", 0.0),
                    duration=m_dict.get("duration", 0.0),
                    pitches=m_dict.get("pitches", []),
                    description=m_dict.get("description"),
                )
            )

        # Reconstruct phrases
        phrases = []
        for p_dict in musical_dict.get("phrases", []):
            phrases.append(
                Phrase(
                    start=p_dict.get("start", 0.0),
                    duration=p_dict.get("duration", 0.0),
                    description=p_dict.get("description"),
                )
            )

        # Reconstruct harmonic analysis
        harmony = None
        harmony_dict = musical_dict.get("harmony")
        if harmony_dict:
            chords = []
            for c_dict in harmony_dict.get("chords", []):
                chords.append(
                    ChordAnalysis(
                        start=c_dict.get("start", 0.0),
                        pitches=c_dict.get("pitches", []),
                        name=c_dict.get("name", ""),
                        roman_numeral=c_dict.get("roman_numeral"),
                        function=c_dict.get("function"),
                        inversion=c_dict.get("inversion"),
                        is_cadence=c_dict.get("is_cadence", False),
                        cadence_type=c_dict.get("cadence_type"),
                    )
                )

            harmony = HarmonicAnalysis(
                chords=chords,
                key=harmony_dict.get("key"),
                roman_numerals=harmony_dict.get("roman_numerals"),
                progression=harmony_dict.get("progression"),
                cadences=harmony_dict.get("cadences"),
                voice_leading=None,  # Not included in formatted dict
            )

        # Reconstruct full analysis
        return MusicalAnalysis(
            motifs=motifs,
            phrases=phrases,
            harmonic_progression=harmony,
            form=musical_dict.get("detected_form"),
            key_ideas=[],  # Not included in formatted dict
            expansion_suggestions=[],  # Not included in formatted dict
        )
    except Exception:
        # If reconstruction fails, return None (will trigger recomputation)
        return None


def extract_melodic_signature(composition: Any, music21_stream: Any | None = None) -> list[int]:
    """
    Extract a melodic signature (pitch sequence) for duplicate detection.

    Args:
        composition: The composition to extract signature from
        music21_stream: Optional pre-converted music21 stream (avoids re-conversion)

    Returns:
        List of MIDI pitch values representing the main melodic line
    """
    if not MUSIC21_AVAILABLE:
        return []

    try:
        from music21 import chord, note

        # Use pre-converted stream if provided, otherwise convert
        if music21_stream is None:
            from pianist.musical_analysis import _composition_to_music21_stream

            s = _composition_to_music21_stream(composition)
        else:
            s = music21_stream

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
        key1_base = (
            metadata1.detected_key.split()[0]
            if " " in metadata1.detected_key
            else metadata1.detected_key
        )
        key2_base = (
            metadata2.detected_key.split()[0]
            if " " in metadata2.detected_key
            else metadata2.detected_key
        )
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
            matches = sum(1 for a, b in zip(prog1, prog2, strict=False) if a == b)
            similarity = matches / max(len(prog1), len(prog2))
            score += 0.2 * similarity
        factors += 0.2

    # Melodic signature similarity (0.2 weight)
    if melodic1 and melodic2:
        min_len = min(len(melodic1), len(melodic2))
        if min_len >= 5 and melodic1 and melodic2:
            # Normalize to same starting pitch for comparison
            offset = melodic2[0] - melodic1[0]
            melodic2_normalized = [p - offset for p in melodic2[:min_len]]
            melodic1_normalized = melodic1[:min_len]

            # Count matching pitches
            matches = sum(
                1 for a, b in zip(melodic1_normalized, melodic2_normalized, strict=False) if a == b
            )
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
    except ImportError as err:
        raise RuntimeError(
            "requests library required for Ollama support. Install with: pip install requests"
        ) from err

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    if verbose:
        print(f"  [Ollama] Calling {model} at {ollama_url}...", file=sys.stderr)
        sys.stderr.flush()

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
    except requests.exceptions.ConnectionError as err:
        raise RuntimeError(
            f"Could not connect to Ollama at {ollama_url}. "
            "Make sure Ollama is installed and running. See: https://ollama.ai"
        ) from err
    except requests.exceptions.Timeout as err:
        raise RuntimeError(
            "Ollama request timed out after 3600 seconds (1 hour). Very large compositions or complex models may require more time."
        ) from err
    except Exception as err:
        raise RuntimeError(f"Ollama request failed: {err}") from err


def is_filename_generic_or_unclear(
    filename: str, filename_info: dict[str, Any] | None = None
) -> bool:
    """
    Determine if a filename is generic/unclear and needs content-based identification.

    A filename is considered generic/unclear if:
    - Contains generic patterns (output, track, file, midi, etc.)
    - Doesn't contain composer/artist name
    - Doesn't contain recognizable title patterns
    - Is very short or cryptic

    Args:
        filename: The filename to check
        filename_info: Optional dict with extracted info (composer, title, etc.)

    Returns:
        True if filename is generic/unclear, False if it has useful structure
    """
    filename_lower = filename.lower()

    # Generic patterns that indicate unclear filenames
    generic_patterns = [
        r"^output\d+",
        r"^track\d+",
        r"^file\d+",
        r"^midi\d+",
        r"^song\d+",
        r"^piece\d+",
        r"^composition\d+",
        r"^untitled",
        r"^unknown",
        r"^temp",
        r"^test",
        r"^gen-",
        r"^new_file",
        r"^my_",
        r"^custom_",
    ]

    # Check for generic patterns
    for pattern in generic_patterns:
        if re.search(pattern, filename_lower):
            return True

    # If filename_info is provided, check if we extracted useful info
    if filename_info:
        has_composer = bool(filename_info.get("composer"))
        has_title = bool(filename_info.get("title"))
        has_catalog = bool(filename_info.get("catalog_number"))

        # If we have composer or (title and catalog), filename is not generic
        if has_composer or (has_title and has_catalog):
            return False

    # Check if filename is very short (likely generic)
    base_name = re.sub(r"\.(mid|midi)$", "", filename, flags=re.IGNORECASE)
    if len(base_name) < 5:
        return True

    # Check if filename contains common separators that suggest structure
    # (dash, double dash, underscore patterns suggest structured naming)
    has_structure = bool(re.search(r"[-_]", filename)) or bool(re.search(r"\s+", filename))

    # If no structure and no extracted info, likely generic
    if not has_structure and filename_info:
        if not filename_info.get("composer") and not filename_info.get("title"):
            return True

    return False


def identify_from_filename_with_ai(
    filename: str,
    filename_info: dict[str, Any],
    metadata: FileMetadata,
    composition: Any,
    provider: str = "gemini",
    model: str = "gemini-flash-latest",
    verbose: bool = False,
    delay_seconds: float = 0.0,
) -> dict[str, Any] | None:
    """
    Use AI to parse and enhance a filename to extract artist/composer and title.

    This is for filenames that have some structure but need parsing/enhancement.
    Examples:
    - "what-was-i-made-for--billie-eilish" -> parse artist and title
    - "Hans Zimmer - Interstellar (Main Theme)" -> enhance formatting
    - "chopin-prelude-op28-no7" -> expand to full name

    Args:
        filename: Original filename
        filename_info: Dictionary with basic info extracted from filename
        metadata: FileMetadata with musical analysis
        composition: Composition object
        provider: AI provider
        model: AI model name
        verbose: Verbose output
        delay_seconds: Delay between AI calls

    Returns:
        Dictionary with parsed/enhanced name info, or None if AI call failed
    """
    if not MUSIC21_AVAILABLE:
        if verbose:
            print("  [AI Filename] music21 not available, skipping", file=sys.stderr)
        return None

    try:
        if verbose:
            print(
                f"  [AI Filename] Parsing filename structure using {provider}...", file=sys.stderr
            )
            sys.stderr.flush()

        if delay_seconds > 0:
            time.sleep(delay_seconds)

        harmonic_prog = metadata.harmonic_progression or "Unknown"
        if harmonic_prog and len(harmonic_prog) > 200:
            harmonic_prog = harmonic_prog[:200] + "..."

        composer = filename_info.get("composer", "")
        title = filename_info.get("title", "")
        catalog = filename_info.get("catalog_number", "")
        is_classical = filename_info.get("is_classical", True)

        prompt = f"""You are a musicologist parsing a MIDI filename to extract artist/composer and title information.

Filename: {filename}

Basic extraction found:
- Composer/Artist: {composer or "Not found"}
- Title: {title or "Not found"}
- Catalog/Opus: {catalog or "Not found"}
- Type: {"Classical" if is_classical else "Modern"}

Musical context (for reference):
- Key: {metadata.detected_key or "Unknown"}
- Form: {metadata.detected_form or "Unknown"}
- Tempo: {metadata.tempo_bpm or "Unknown"} BPM
- Duration: {metadata.duration_beats:.1f} beats

Your task: Parse the filename to extract the artist/composer and title, handling both classical and modern naming conventions.

Examples of what to handle:
- "what-was-i-made-for--billie-eilish" -> artist: "Billie Eilish", title: "What Was I Made For?"
- "Hans Zimmer - Interstellar (Main Theme)" -> artist: "Hans Zimmer", title: "Interstellar (Main Theme)"
- "chopin-prelude-op28-no7" -> composer: "Frédéric Chopin", title: "Prelude in A major, Op. 28, No. 7"
- "j.s.-bach---invention-no.-1-bwv-772" -> composer: "J.S. Bach", title: "Invention No. 1 in C major, BWV 772"

Guidelines:
1. Extract artist/composer name (use full canonical name)
2. Extract title (complete, properly formatted)
3. For classical works: include catalog numbers if present
4. For modern works: include album/source if in parentheses
5. Use musical context to infer missing information (e.g., key, piece type)
6. Format consistently (proper capitalization, punctuation)

Respond with JSON:
{{
  "composer": "Full composer/artist name (e.g., 'J.S. Bach', 'Hans Zimmer', 'Billie Eilish')",
  "title": "Complete title (e.g., 'Invention No. 1 in C major, BWV 772' or 'Interstellar (Main Theme)' or 'What Was I Made For?')",
  "catalog_number": "Catalog number for classical works (e.g., 'BWV 772', 'Op. 28, No. 7') or null",
  "album": "Album/source for modern works or null",
  "style": "Baroque|Classical|Romantic|Modern|Contemporary|Film Score|Pop|Other",
  "is_classical": true or false,
  "confidence": "high|medium|low"
}}

Respond ONLY with valid JSON, no other text."""

        # Call AI provider
        if provider == "ollama":
            response = call_ollama(model=model, prompt=prompt, verbose=verbose)
        elif provider == "openrouter":
            from pianist.ai_providers import OpenRouterError, generate_text_openrouter

            try:
                response = generate_text_openrouter(model=model, prompt=prompt, verbose=verbose)
            except OpenRouterError:
                return None
        else:  # gemini
            from pianist.ai_providers import generate_text

            response = generate_text(model=model, prompt=prompt, verbose=verbose)

        # Parse JSON response
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
        if json_match:
            try:
                ai_data = json.loads(json_match.group())
                if verbose:
                    print("  [AI Filename] Successfully parsed filename", file=sys.stderr)
                    sys.stderr.flush()
                return ai_data
            except json.JSONDecodeError:
                # Try to fix JSON
                json_str = json_match.group()
                json_str = re.sub(r",\s*}", "}", json_str)
                json_str = re.sub(r",\s*]", "]", json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        return None
    except Exception as e:
        if verbose:
            print(f"  [AI Filename] Error: {e}", file=sys.stderr)
            sys.stderr.flush()
        return None


def identify_from_content_with_ai(
    metadata: FileMetadata,
    composition: Any,
    filename: str,
    provider: str = "gemini",
    model: str = "gemini-flash-latest",
    verbose: bool = False,
    delay_seconds: float = 0.0,
    is_original: bool = False,
) -> dict[str, Any] | None:
    """
    Use AI to identify a well-known composition by analyzing musical content.

    This is for files with generic/unclear filenames where we need to identify
    the composition from its musical characteristics.

    Args:
        metadata: FileMetadata with musical analysis
        composition: Composition object
        filename: Original filename (may be generic)
        provider: AI provider
        model: AI model name
        verbose: Verbose output
        delay_seconds: Delay between AI calls
        is_original: If True, this is known to be an original composition.
                     AI will provide description only, no identification attempt.

    Returns:
        Dictionary with identified composition info or description, or None if not identified
    """
    if not MUSIC21_AVAILABLE:
        if verbose:
            print("  [AI] music21 not available, skipping AI identification", file=sys.stderr)
        return None

    try:
        from pianist.iterate import composition_to_canonical_json

        if verbose:
            if is_original:
                print(
                    f"  [AI] Analyzing original composition and generating description using {provider}...",
                    file=sys.stderr,
                )
            else:
                print(
                    f"  [AI] Attempting to identify composition using {provider}...",
                    file=sys.stderr,
                )
            sys.stderr.flush()

        # Add delay to avoid rate limits
        if delay_seconds > 0:
            if verbose:
                print(
                    f"  [AI] Waiting {delay_seconds:.1f}s to avoid rate limits...", file=sys.stderr
                )
                sys.stderr.flush()
            time.sleep(delay_seconds)

        comp_json = composition_to_canonical_json(composition)

        # Extract key musical characteristics for identification
        harmonic_prog = metadata.harmonic_progression or "Unknown"
        if harmonic_prog and len(harmonic_prog) > 200:
            harmonic_prog = harmonic_prog[:200] + "..."

        if is_original:
            # Special prompt for original compositions - description only, no identification
            prompt = f"""You are a musicologist analyzing an original/unknown piano composition.

This MIDI file is known to be an original composition (not a well-known work by a famous composer).
Please provide a detailed musical analysis and description.

Filename: {filename}
Key: {metadata.detected_key or "Unknown"}
Form: {metadata.detected_form or "Unknown"}
Time Signature: {metadata.time_signature or "Unknown"}
Tempo: {metadata.tempo_bpm or "Unknown"} BPM
Duration: {metadata.duration_beats:.1f} beats (~{metadata.bars:.1f} bars)
Motifs: {metadata.motif_count}
Phrases: {metadata.phrase_count}
Harmonic progression (first part): {harmonic_prog}

Musical content (first 2000 characters):
{comp_json[:2000]}

Provide a detailed analysis and description. Respond with JSON:
{{
  "identified": false,
  "suggested_title": "Descriptive title based on musical characteristics (NO composer name)",
  "style": "Baroque|Classical|Romantic|Modern|Other",
  "form": "{metadata.detected_form or "unknown"}",
  "description": "Detailed description of the piece's musical characteristics, style, mood, technical features, and what it demonstrates. Be specific about harmonic progressions, melodic patterns, form, and overall character."
}}

CRITICAL: This is an original composition. Do NOT attempt to identify a composer or well-known work.
Focus on providing a rich, detailed description of the musical content.

Respond ONLY with valid JSON, no other text."""
        else:
            # Standard prompt for potentially known compositions (classical and modern)
            prompt = f"""You are a musicologist identifying piano compositions, including both classical and modern works.

Analyze this MIDI file and try to identify if it's a well-known composition.

IMPORTANT: Only identify compositions if you are VERY CONFIDENT they are well-known works.
This includes:
- Classical compositions by established composers (Bach, Beethoven, Chopin, etc.)
- Modern film soundtracks (Hans Zimmer, Ludovico Einaudi, Max Richter, etc.)
- Popular contemporary piano pieces (Yiruma, Billie Eilish piano arrangements, etc.)
- Well-known pop songs in piano arrangements

If this appears to be an original composition, a student work, an unknown piece, or you have any doubt,
you MUST respond with "identified": false.

Filename: {filename}
Key: {metadata.detected_key or "Unknown"}
Form: {metadata.detected_form or "Unknown"}
Time Signature: {metadata.time_signature or "Unknown"}
Tempo: {metadata.tempo_bpm or "Unknown"} BPM
Duration: {metadata.duration_beats:.1f} beats (~{metadata.bars:.1f} bars)
Motifs: {metadata.motif_count}
Phrases: {metadata.phrase_count}
Harmonic progression (first part): {harmonic_prog}

Musical content (first 2000 characters):
{comp_json[:2000]}

If you can identify this as a well-known composition with HIGH confidence, respond with JSON:
{{
  "identified": true,
  "composer": "Composer/Artist name (e.g., 'J.S. Bach', 'Chopin', 'Hans Zimmer', 'Billie Eilish')",
  "title": "Full composition title (e.g., 'Two-Part Invention No. 8 in F major, BWV 779' or 'Interstellar (Main Theme)' or 'What Was I Made For?')",
  "catalog_number": "Catalog number if applicable for classical works (e.g., 'BWV 779', 'Op. 11 No. 4'), or null for modern works",
  "album": "Album or source for modern works (e.g., 'Interstellar (Soundtrack)'), or null for classical",
  "style": "Baroque|Classical|Romantic|Modern|Contemporary|Film Score|Pop|Other",
  "form": "binary|ternary|sonata|invention|prelude|etude|theme|ballad|etc.",
  "description": "Brief description of the piece and what it demonstrates",
  "confidence": "high|medium|low",
  "is_classical": true or false
}}

If you cannot identify it as a well-known composition, or if it appears to be an original/unknown work, respond with:
{{
  "identified": false,
  "suggested_title": "Descriptive title based on characteristics (NO composer name)",
  "style": "Baroque|Classical|Romantic|Modern|Contemporary|Film Score|Pop|Other",
  "form": "{metadata.detected_form or "unknown"}",
  "description": "Brief description based on musical analysis",
  "is_classical": true or false (based on musical style)
}}

CRITICAL: Do NOT guess composer/artist names. Only set "identified": true if you are certain
this is a well-known composition. Original compositions, student works, and unknown pieces
should have "identified": false.

For modern works, use "composer" field for the artist/composer name (e.g., "Hans Zimmer", "Billie Eilish").
For film soundtracks, include the film name in the title (e.g., "Interstellar (Main Theme)").

Respond ONLY with valid JSON, no other text."""

        # Call appropriate provider
        if provider == "ollama":
            try:
                response = call_ollama(model=model, prompt=prompt, verbose=verbose)
            except RuntimeError as e:
                if verbose:
                    print(f"  [AI] {e}", file=sys.stderr)
                    sys.stderr.flush()
                return None
        elif provider == "openrouter":
            try:
                from pianist.ai_providers import OpenRouterError, generate_text_openrouter

                response = generate_text_openrouter(model=model, prompt=prompt, verbose=verbose)
            except OpenRouterError as e:
                if verbose:
                    print(f"  [AI] {e}", file=sys.stderr)
                    sys.stderr.flush()
                # Check if it's a rate limit error
                error_str = str(e)
                if (
                    "429" in error_str
                    or "rate limit" in error_str.lower()
                    or "quota" in error_str.lower()
                ) and verbose:
                    print("  [AI] Rate limit exceeded. Consider using --ai-delay", file=sys.stderr)
                    sys.stderr.flush()
                return None
            except Exception as e:
                if verbose:
                    print(f"  [AI] Error: {e}", file=sys.stderr)
                    sys.stderr.flush()
                return None
        else:  # gemini
            try:
                from pianist.ai_providers import generate_text

                response = generate_text(model=model, prompt=prompt, verbose=verbose)
            except Exception as e:
                # Check if it's a rate limit error
                error_str = str(e)
                if (
                    "429" in error_str
                    or "RESOURCE_EXHAUSTED" in error_str
                    or "quota" in error_str.lower()
                ):
                    if verbose:
                        print(
                            "  [AI] Rate limit exceeded. Consider using --ai-delay or --ai-provider ollama",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()
                    return None
                if verbose:
                    print(f"  [AI] Error: {e}", file=sys.stderr)
                    sys.stderr.flush()
                raise  # Re-raise other errors

        if verbose:
            print(f"  [AI] Received response (length: {len(response)})", file=sys.stderr)
            sys.stderr.flush()

        # Try to parse JSON from response
        # Look for JSON object (handles multi-line)
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
        if json_match:
            try:
                ai_data = json.loads(json_match.group())
                if verbose:
                    identified = ai_data.get("identified", False)
                    print(f"  [AI] Identification result: identified={identified}", file=sys.stderr)
                    if identified:
                        composer = ai_data.get("composer", "")
                        title = ai_data.get("title", "")
                        print(f"  [AI] Identified as: {composer}: {title}", file=sys.stderr)
                    sys.stderr.flush()
                return ai_data
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"  [AI] JSON parse error: {e}", file=sys.stderr)
                # Try to fix common JSON issues
                json_str = json_match.group()
                # Remove trailing commas
                json_str = re.sub(r",\s*}", "}", json_str)
                json_str = re.sub(r",\s*]", "]", json_str)
                try:
                    ai_data = json.loads(json_str)
                    if verbose:
                        print("  [AI] Successfully parsed after fixing JSON", file=sys.stderr)
                    return ai_data
                except json.JSONDecodeError as e2:
                    if verbose:
                        print(f"  [AI] Still failed to parse JSON: {e2}", file=sys.stderr)
                        print(f"  [AI] Response snippet: {response[:200]}", file=sys.stderr)
                        sys.stderr.flush()
        elif verbose:
            print("  [AI] No JSON found in response", file=sys.stderr)
            sys.stderr.flush()
    except ImportError as e:
        if verbose:
            print(f"  [AI] Import error: {e}", file=sys.stderr)
            sys.stderr.flush()
    except Exception as e:
        if verbose:
            print(f"  [AI] Error during identification: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            sys.stderr.flush()

    return None


def enhance_name_with_ai(
    filename_info: dict[str, Any],
    metadata: FileMetadata,
    composition: Any,
    filename: str,
    provider: str = "gemini",
    model: str = "gemini-flash-latest",
    verbose: bool = False,
    delay_seconds: float = 0.0,
) -> dict[str, Any] | None:
    """
    Use AI to enhance/improve a name extracted from filename.

    Takes filename-extracted info (e.g., "Scriabin: op16-no5 (Op. 16)") and uses AI
    to generate a more complete, consistent name (e.g., "Alexander Scriabin: Prelude
    in F-sharp major, Op. 16, No. 5").

    Args:
        filename_info: Dictionary with composer, title, catalog_number, etc. from filename
        metadata: FileMetadata with musical analysis
        composition: Composition object
        filename: Original filename
        provider: AI provider
        model: AI model name
        verbose: Verbose output
        delay_seconds: Delay between AI calls

    Returns:
        Dictionary with enhanced name info, or None if AI call failed
    """
    if not MUSIC21_AVAILABLE:
        if verbose:
            print("  [AI] music21 not available, skipping AI name enhancement", file=sys.stderr)
        return None

    try:
        from pianist.iterate import composition_to_canonical_json

        if verbose:
            print(f"  [AI] Enhancing filename-extracted name using {provider}...", file=sys.stderr)
            sys.stderr.flush()

        # Add delay to avoid rate limits
        if delay_seconds > 0:
            if verbose:
                print(
                    f"  [AI] Waiting {delay_seconds:.1f}s to avoid rate limits...", file=sys.stderr
                )
                sys.stderr.flush()
            time.sleep(delay_seconds)

        comp_json = composition_to_canonical_json(composition)

        # Extract key musical characteristics
        harmonic_prog = metadata.harmonic_progression or "Unknown"
        if harmonic_prog and len(harmonic_prog) > 200:
            harmonic_prog = harmonic_prog[:200] + "..."

        # Build context from filename info
        composer = filename_info.get("composer", "")
        title = filename_info.get("title", "")
        catalog = filename_info.get("catalog_number", "")
        opus = filename_info.get("opus", "")

        # Extract key from filename if present (e.g., "Sonatina in C", "Prelude in F-sharp major")
        filename_key = None
        key_patterns = [
            r"\bin\s+([A-G][#b]?)\s+(major|minor|maj|min)",
            r"\bin\s+([A-G][#b]?)\s*[,\s]",  # Just "in C" or "in F#"
            r"\b([A-G][#b]?)\s+(major|minor|maj|min)\s*[,\s]",  # "C major" or "F# minor"
        ]
        for pattern in key_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                key_note = match.group(1).upper()
                if len(match.groups()) > 1 and match.group(2):
                    key_mode = match.group(2).lower()
                    if key_mode in ["major", "maj"]:
                        filename_key = f"{key_note} major"
                    elif key_mode in ["minor", "min"]:
                        filename_key = f"{key_note} minor"
                else:
                    # Default to major if mode not specified
                    filename_key = f"{key_note} major"
                break

        # Build a basic name from filename info for context
        if title and catalog:
            basic_name = f"{composer}: {title} ({catalog})"
        elif title:
            basic_name = f"{composer}: {title}"
        elif catalog:
            basic_name = f"{composer}: {catalog}"
        else:
            basic_name = composer

        # Determine which key to use - prefer filename key if present
        key_to_use = filename_key or metadata.detected_key or "Unknown"
        key_source = (
            "filename" if filename_key else ("detected" if metadata.detected_key else "unknown")
        )

        prompt = f"""You are a musicologist enhancing a composition name extracted from a filename.

The filename extraction found:
- Composer: {composer or "Unknown"}
- Title: {title or "Unknown"}
- Catalog/Opus: {catalog or opus or "Unknown"}
- Basic name: {basic_name}
{f"- Key from filename: {filename_key}" if filename_key else ""}

Filename: {filename}
Key: {key_to_use} ({key_source})
Detected Key (from analysis): {metadata.detected_key or "Unknown"}
Detected Form: {metadata.detected_form or "Unknown"}
Time Signature: {metadata.time_signature or "Unknown"}
Tempo: {metadata.tempo_bpm or "Unknown"} BPM
Duration: {metadata.duration_beats:.1f} beats (~{metadata.bars:.1f} bars)

Musical content (first 2000 characters):
{comp_json[:2000]}

Your task: Generate a complete, properly formatted composition name using the filename-extracted information as a starting point.

Guidelines:
1. Use the FULL composer name (e.g., "Alexander Scriabin" not just "Scriabin", "Frédéric Chopin" not just "Chopin", "Muzio Clementi" not just "Clementi")
2. If the title is incomplete or unclear (e.g., "op16-no5"), infer the proper piece type (Prelude, Étude, Sonatina, etc.) from the musical content
3. **IMPORTANT: Use the key from the filename if specified (e.g., "Sonatina in C" means C major). Only use the detected key if the filename doesn't specify a key.**
4. Format catalog numbers properly (e.g., "Op. 16, No. 5" not "op16-no5")
5. If you can identify this as a well-known composition, use the canonical title
6. If it's not well-known, create a descriptive title based on the musical characteristics
7. **CRITICAL: The "title" field should NOT include the composer name. Return composer and title separately. The title should be just the composition name (e.g., "Sonatina in C, Op. 36, No. 1b" not "Muzio Clementi: Sonatina in C, Op. 36, No. 1b")**

Respond with JSON:
{{
  "composer": "Full composer name (e.g., 'Alexander Scriabin', 'Frédéric Chopin', 'Muzio Clementi')",
  "title": "Complete composition title WITHOUT composer name (e.g., 'Prelude in F-sharp major, Op. 16, No. 5' or 'Sonatina in C, Op. 36, No. 1b')",
  "catalog_number": "Properly formatted catalog number (e.g., 'Op. 16, No. 5')",
  "style": "Baroque|Classical|Romantic|Modern|Other",
  "description": "Brief description of the piece's musical characteristics, style, and mood"
}}

Respond ONLY with valid JSON, no other text."""

        # Call appropriate provider
        if provider == "ollama":
            try:
                response = call_ollama(model=model, prompt=prompt, verbose=verbose)
            except RuntimeError as e:
                if verbose:
                    print(f"  [AI] {e}", file=sys.stderr)
                    sys.stderr.flush()
                return None
        elif provider == "openrouter":
            try:
                from pianist.ai_providers import OpenRouterError, generate_text_openrouter

                response = generate_text_openrouter(model=model, prompt=prompt, verbose=verbose)
            except OpenRouterError as e:
                if verbose:
                    print(f"  [AI] {e}", file=sys.stderr)
                    sys.stderr.flush()
                return None
            except Exception as e:
                if verbose:
                    print(f"  [AI] Error: {e}", file=sys.stderr)
                    sys.stderr.flush()
                return None
        else:  # gemini
            try:
                from pianist.ai_providers import generate_text

                response = generate_text(model=model, prompt=prompt, verbose=verbose)
            except Exception as e:
                if verbose:
                    print(f"  [AI] Error: {e}", file=sys.stderr)
                    sys.stderr.flush()
                return None

        if verbose:
            print(
                f"  [AI] Received enhancement response (length: {len(response)})", file=sys.stderr
            )
            sys.stderr.flush()

        # Try to parse JSON from response
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
        if json_match:
            try:
                ai_data = json.loads(json_match.group())
                if verbose:
                    print("  [AI] Successfully parsed enhancement response", file=sys.stderr)
                    sys.stderr.flush()
                return ai_data
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"  [AI] JSON parse error: {e}", file=sys.stderr)
                    sys.stderr.flush()
                # Try to fix common JSON issues
                json_str = json_match.group()
                json_str = re.sub(r",\s*}", "}", json_str)
                json_str = re.sub(r",\s*]", "]", json_str)
                try:
                    ai_data = json.loads(json_str)
                    if verbose:
                        print("  [AI] Successfully parsed after fixing JSON", file=sys.stderr)
                        sys.stderr.flush()
                    return ai_data
                except json.JSONDecodeError as e2:
                    if verbose:
                        print(f"  [AI] Still failed to parse JSON: {e2}", file=sys.stderr)
                        print(f"  [AI] Response snippet: {response[:200]}", file=sys.stderr)
                        sys.stderr.flush()
        elif verbose:
            print("  [AI] No JSON found in response", file=sys.stderr)
            sys.stderr.flush()
    except ImportError as e:
        if verbose:
            print(f"  [AI] Import error: {e}", file=sys.stderr)
            sys.stderr.flush()
    except Exception as e:
        if verbose:
            print(f"  [AI] Error during name enhancement: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            sys.stderr.flush()

    return None


def is_original_composition(filename: str) -> bool:
    """
    Detect if a MIDI file should be marked as an original/unknown composition.

    Checks filename patterns that indicate original compositions:
    - Contains "original", "unknown", "composition", "piece", "work"
    - Contains "my_", "custom_", "new_", "untitled"
    - Does NOT contain known composer names or catalog numbers

    Returns:
        True if file should be treated as original/unknown composition
    """
    filename_lower = filename.lower()

    # Patterns that indicate original compositions
    original_indicators = [
        "original",
        "unknown",
        "composition",
        "piece",
        "work",
        "my_",
        "custom_",
        "new_",
        "untitled",
        "sketch",
        "draft",
    ]

    # Check for original indicators
    has_original_indicator = any(indicator in filename_lower for indicator in original_indicators)

    # Known composer patterns (if found, likely NOT original)
    known_composers = [
        "bach",
        "beethoven",
        "mozart",
        "chopin",
        "scriabin",
        "debussy",
        "rachmaninoff",
        "schubert",
        "schumann",
        "liszt",
        "brahms",
        "haydn",
        "handel",
        "vivaldi",
        "tchaikovsky",
        "ravel",
        "satie",
    ]

    # Catalog number patterns (BWV, Op., etc.) indicate known compositions
    has_catalog = bool(re.search(r"\b(bwv|op\.?|opus|k\.?|kv\.?|d\.?)\s*\d+", filename_lower))

    # If filename has original indicators AND no known composer/catalog, mark as original
    return bool(
        has_original_indicator
        and not any(composer in filename_lower for composer in known_composers)
        and not has_catalog
    )


def load_metadata_json(file_path: Path) -> dict[str, Any] | None:
    """
    Load metadata from companion JSON file if it exists.

    Looks for filename.mid.json alongside the MIDI file.

    Returns:
        Dictionary with metadata or None if file doesn't exist
    """
    json_path = file_path.with_suffix(file_path.suffix + ".json")

    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                metadata = json.load(f)
                return metadata
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {json_path}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Warning: Could not load metadata from {json_path}: {e}", file=sys.stderr)
            return None

    return None


def extract_composer_from_directory(file_path: Path) -> str | None:
    """
    Extract composer from directory structure.

    Examples:
    - references/J.S. Bach/file.mid -> "J.S. Bach"
    - references/Chopin/Preludes/file.mid -> "Chopin"
    - references/Original/file.mid -> None (will be marked as original)

    Returns:
        Composer name if found, None otherwise
    """
    parent_dir = file_path.parent.name

    # Check if parent is a known composer directory (exact match)
    for canonical_name in COMPOSER_DEFINITIONS:
        if parent_dir == canonical_name:
            return canonical_name

    # Check if parent matches composer patterns (case-insensitive)
    parent_lower = parent_dir.lower()

    # Try simple patterns first
    for pattern, composer in COMPOSER_SIMPLE_PATTERNS.items():
        if pattern in parent_lower:
            return composer

    # Try regex patterns
    for pattern, composer in COMPOSER_REGEX_PATTERNS.items():
        if re.search(pattern, parent_dir, re.IGNORECASE):
            return composer

    # Check for special directories that indicate original/unknown works
    special_dirs = ["original", "unknown", "traditional", "custom", "my"]
    if parent_lower in special_dirs:
        return None  # Will be handled as original/unknown

    return None


def extract_info_from_filename(filename: str) -> dict[str, Any]:
    """
    Extract composition information from filename patterns.

    Common patterns:
    - "bach-invention-8-bwv-779.mid" -> composer, title, catalog
    - "chopin-prelude-op28-no4.mid" -> composer, opus
    - "scriabin-etude-op2-no1.mid" -> composer, opus
    - "Ludwig van Beethoven - Piano Sonata No.14 in C#-, Op.27, No.2 ('Moonlight') 3. Presto agitato.mid"
      -> composer, title, opus, movement
    """
    info: dict[str, Any] = {
        "composer": None,
        "title": None,
        "catalog_number": None,
        "opus": None,
        "movement": None,
    }

    filename_lower = filename.lower()

    # Pattern 1: "Composer - Title" format (e.g., "Ludwig van Beethoven - Piano Sonata...")
    # Also handles patterns like "chopin---prelude" (multiple dashes)
    dash_separator_match = re.search(
        r"^([^-]+?)\s*-+\s*(.+?)(?:\.mid|\.midi)?$", filename, re.IGNORECASE
    )
    if dash_separator_match:
        composer_part = dash_separator_match.group(1).strip()
        title_part = dash_separator_match.group(2).strip()

        # Extract composer from first part using centralized patterns
        composer_patterns = COMPOSER_REGEX_PATTERNS

        for pattern, composer in composer_patterns.items():
            if re.search(pattern, composer_part, re.IGNORECASE):
                info["composer"] = composer
                break

        # If no match, try simple composer name patterns
        if not info["composer"]:
            simple_composer_patterns = COMPOSER_SIMPLE_PATTERNS
            for pattern, composer in simple_composer_patterns.items():
                if pattern in composer_part.lower():
                    info["composer"] = composer
                    break

        # Extract title from second part (remove movement numbers, opus, etc.)
        # Example: "Piano Sonata No.14 in C#-, Op.27, No.2 ('Moonlight') 3. Presto agitato"
        # -> "Piano Sonata No.14 in C#- ('Moonlight')"
        title_clean = title_part

        # Remove movement number at the end (e.g., "3. Presto agitato")
        title_clean = re.sub(r"\s+\d+\.\s+[^.]*$", "", title_clean)

        # Extract opus number
        opus_match = re.search(
            r"op\.?\s*(\d+)(?:\s*,\s*no\.?\s*(\d+))?", title_clean, re.IGNORECASE
        )
        if opus_match:
            opus_num = opus_match.group(1)
            no_num = opus_match.group(2)
            if no_num:
                info["opus"] = f"Op. {opus_num} No. {no_num}"
            else:
                info["opus"] = f"Op. {opus_num}"
            info["catalog_number"] = info["opus"]

        # Clean up title (remove opus references, keep the main title and nicknames)
        # Keep everything up to the opus number or movement number, but preserve nicknames in quotes/parentheses
        # Example: "Piano Sonata No.14 in C#-, Op.27, No.2 ('Moonlight') 3. Presto"
        # -> "Piano Sonata No.14 in C#- ('Moonlight')"

        # First, extract nickname if present (in quotes or parentheses before opus/movement)
        nickname_match = re.search(r"[(\'\"]([^)\'\"]+)[)\'\"]", title_clean)
        nickname = nickname_match.group(1).strip() if nickname_match else None

        # Extract main title (everything before opus or movement number)
        title_match = re.match(r"^(.+?)(?:\s*,\s*op\.|\.\s*\d+\.)", title_clean)
        if title_match:
            title_clean = title_match.group(1).strip()
        else:
            # Remove opus from anywhere in the string
            title_clean = re.sub(r",\s*op\.?\s*\d+.*$", "", title_clean, flags=re.IGNORECASE)

        # If we found a nickname and it's not already in the title, add it
        if nickname and nickname not in title_clean:
            # Check if title already has quotes/parentheses
            if "(" in title_clean or "'" in title_clean or '"' in title_clean:
                title_clean = f"{title_clean} ('{nickname}')"
            else:
                title_clean = f"{title_clean} ('{nickname}')"

        if title_clean:
            info["title"] = title_clean.strip()

        # If we found composer and title, return early
        if info["composer"] and info["title"]:
            return info

    # Pattern 1b: "Title -- Composer" format (e.g., "gymnopdie-no.1--erik-satie.mid")
    # Check if composer is at the end after dashes
    if not info["composer"]:
        # Pattern: something ending with "--composer" or "-composer"
        # Try double dash first (more specific)
        end_composer_match = re.search(r"--([^-]+?)(?:\.mid|\.midi)?$", filename, re.IGNORECASE)
        if not end_composer_match:
            # Try single dash (but be more careful - might be part of title)
            end_composer_match = re.search(r"-([a-z]+)(?:\.mid|\.midi)?$", filename, re.IGNORECASE)

        if end_composer_match:
            composer_part_end = end_composer_match.group(1).strip()
            # Try to match composer patterns in the end part using centralized patterns
            end_composer_patterns = COMPOSER_END_PATTERNS
            composer_part_lower = composer_part_end.lower().replace("-", " ").replace("_", " ")
            # Sort by length (longest first) to match "erik satie" before "erik"
            for pattern, composer in sorted(
                end_composer_patterns.items(), key=lambda x: -len(x[0])
            ):
                if pattern in composer_part_lower:
                    info["composer"] = composer
                    # Extract title from the beginning part (everything before the composer)
                    # For "gymnopdie-no.1--erik-satie.mid", extract "gymnopdie-no.1"
                    title_end_pos = filename.lower().rfind("--" + composer_part_end.lower())
                    if title_end_pos == -1:
                        title_end_pos = filename.lower().rfind("-" + composer_part_end.lower())
                    if title_end_pos > 0:
                        potential_title = filename[:title_end_pos].strip()
                        # Clean up the title - convert to readable format
                        potential_title = potential_title.replace("_", " ").replace("-", " ")
                        # Capitalize properly
                        potential_title = " ".join(
                            word.capitalize() for word in potential_title.split()
                        )
                        if potential_title and len(potential_title) > 2:
                            info["title"] = potential_title
                    break

    # Pattern 2: Simple patterns (original logic for backward compatibility)
    # Use centralized composer patterns
    composer_patterns = COMPOSER_SIMPLE_PATTERNS

    if not info["composer"]:
        for pattern, composer in composer_patterns.items():
            if pattern in filename_lower:
                info["composer"] = composer
                break

    # Extract BWV numbers (Bach)
    bwv_match = re.search(r"bwv[.\s-]*(\d+)", filename_lower)
    if bwv_match:
        info["catalog_number"] = f"BWV {bwv_match.group(1)}"
        if not info["composer"]:
            info["composer"] = "J.S. Bach"

    # Extract Opus numbers (if not already found)
    if not info["opus"]:
        opus_match = re.search(r"op[.\s-]*(\d+)(?:\s*no[.\s-]*(\d+))?", filename_lower)
        if opus_match:
            opus_num = opus_match.group(1)
            no_num = opus_match.group(2)
            if no_num:
                info["opus"] = f"Op. {opus_num} No. {no_num}"
            else:
                info["opus"] = f"Op. {opus_num}"
            info["catalog_number"] = info["opus"]

    # Extract common piece types (if not already found)
    if not info["title"]:
        piece_types = {
            "invention": "Invention",
            "prelude": "Prelude",
            "etude": "Étude",
            "sonata": "Sonata",
            "sonatina": "Sonatina",
            "nocturne": "Nocturne",
            "waltz": "Waltz",
            "mazurka": "Mazurka",
            "impromptu": "Impromptu",
            "fugue": "Fugue",
            "gymnopédie": "Gymnopédie",
            "gymnopedie": "Gymnopédie",
        }

        for pattern, piece_type in piece_types.items():
            if pattern in filename_lower:
                # Try to extract a more complete title
                # Pattern: "prelude-no-7" or "prelude-op28-no7" -> "Prelude No. 7"
                piece_match = re.search(
                    rf"{pattern}[-\s]*(?:no\.?\s*|op\.?\s*\d+\s*no\.?\s*)(\d+)", filename_lower
                )
                if piece_match:
                    number = piece_match.group(1)
                    info["title"] = f"{piece_type} No. {number}"
                else:
                    # Check for opus + number pattern: "prelude-op28-no7"
                    opus_piece_match = re.search(
                        rf"{pattern}.*?op\.?\s*(\d+).*?no\.?\s*(\d+)", filename_lower
                    )
                    if opus_piece_match:
                        opus_num = opus_piece_match.group(1)
                        no_num = opus_piece_match.group(2)
                        info["title"] = f"{piece_type} No. {no_num}"
                        if not info["opus"]:
                            info["opus"] = f"Op. {opus_num} No. {no_num}"
                            info["catalog_number"] = info["opus"]
                    else:
                        info["title"] = piece_type
                break

    # Pattern 3: Handle hyphenated patterns like "chopin---prelude-no-7" or "prlude-opus-28-no-7"
    # This handles cases where the dash separator pattern didn't match
    if not info["title"] or (info["composer"] and not info["title"]):
        # Look for patterns like: composer-piece-opus-no or piece-opus-no-composer
        # Example: "chopin---prelude-no.-7-in-a-major-op.-28"
        # Example: "prlude-opus-28-no.-7-in-a-major--chopin" (note: "prlude" is a typo for "prelude")

        # Pattern: piece-opus-no (e.g., "prlude-opus-28-no-7" or "prelude-opus-28-no-7")
        # Handle typos like "prlude" -> "prelude"
        piece_opus_no_match = re.search(
            r"(pr?elude|invention|etude|sonata|nocturne|waltz|mazurka|impromptu|fugue)[-\s]*opus[-\s]*(\d+)[-\s]*no\.?\s*(\d+)",
            filename_lower,
        )
        if piece_opus_no_match:
            piece_type_raw = piece_opus_no_match.group(1)
            # Fix common typos
            piece_type = "Prelude" if piece_type_raw == "prlude" else piece_type_raw.capitalize()
            opus_num = piece_opus_no_match.group(2)
            no_num = piece_opus_no_match.group(3)
            info["title"] = f"{piece_type} No. {no_num}"
            if not info["opus"]:
                info["opus"] = f"Op. {opus_num} No. {no_num}"
                info["catalog_number"] = info["opus"]

        # Pattern: piece-no-opus (e.g., "prelude-no-7-op-28" or "prlude-no-7-op-28")
        if not info["title"]:
            piece_no_opus_match = re.search(
                r"(pr?elude|invention|etude|sonata|nocturne|waltz|mazurka|impromptu|fugue)[-\s]*no\.?\s*(\d+).*?op\.?\s*(\d+)",
                filename_lower,
            )
            if piece_no_opus_match:
                piece_type_raw = piece_no_opus_match.group(1)
                if piece_type_raw == "prlude":
                    piece_type = "Prelude"
                else:
                    piece_type = piece_type_raw.capitalize()
                no_num = piece_no_opus_match.group(2)
                opus_num = piece_no_opus_match.group(3)
                info["title"] = f"{piece_type} No. {no_num}"
                if not info["opus"]:
                    info["opus"] = f"Op. {opus_num} No. {no_num}"
                    info["catalog_number"] = info["opus"]

        # Pattern: composer-piece-no-opus (e.g., "chopin---prelude-no-7-op-28")
        if not info["title"] and info["composer"]:
            composer_piece_match = re.search(
                rf"({'|'.join(composer_patterns.keys())})[-\s]+(pr?elude|invention|etude|sonata|nocturne|waltz|mazurka|impromptu|fugue)[-\s]*no\.?\s*(\d+)",
                filename_lower,
            )
            if composer_piece_match:
                piece_type_raw = composer_piece_match.group(2)
                if piece_type_raw == "prlude":
                    piece_type = "Prelude"
                else:
                    piece_type = piece_type_raw.capitalize()
                no_num = composer_piece_match.group(3)
                info["title"] = f"{piece_type} No. {no_num}"

    return info


def generate_suggested_name(
    metadata: FileMetadata,
    composition: Any,
    verbose: bool = False,
    ai_provider: str = "gemini",
    ai_model: str | None = None,
    ai_delay: float = 0.0,
) -> tuple[str, str, str | None, str | None, bool]:
    """
    Generate a suggested name, ID, style, and description for a file.

    Uses multiple strategies (in priority order):
    1. Load metadata from companion JSON file (filename.mid.json)
    2. Extract composer from directory structure
    3. Extract info from filename patterns
    4. Try AI identification to identify well-known compositions
    5. Fall back to analysis-based generation

    Returns:
        (name, id, style, description, ai_identified)
        where ai_identified is True if AI successfully identified the composition
    """
    filename = metadata.filename
    file_path = (
        Path(metadata.filepath) if hasattr(metadata, "filepath") and metadata.filepath else None
    )
    ai_identified = False

    # Strategy 0: Load metadata from companion JSON file (highest priority)
    json_metadata = None
    if file_path:
        json_metadata = load_metadata_json(file_path)
        if json_metadata and verbose:
            print(
                f"  [Metadata JSON] Loaded metadata from {file_path.with_suffix(file_path.suffix + '.json')}",
                file=sys.stderr,
            )
            sys.stderr.flush()

    # If we have JSON metadata, use it (highest priority)
    if json_metadata:
        composer = json_metadata.get("composer", "")
        title = json_metadata.get("title", "")
        catalog = json_metadata.get("catalog_number") or json_metadata.get("opus", "")
        style_hint = json_metadata.get("style")
        suggested_description = json_metadata.get("description", "")

        # Build suggested name
        if composer and title:
            if catalog:
                suggested_name = f"{composer}: {title} ({catalog})"
            else:
                suggested_name = f"{composer}: {title}"
        elif composer:
            suggested_name = composer
            if title:
                suggested_name = f"{composer}: {title}"
        elif title:
            suggested_name = title
        else:
            suggested_name = "Unknown Composition"

        # Generate ID
        suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
        suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
        suggested_id = suggested_id[:50]

        if verbose:
            print(f"  [Name] Using metadata JSON: {suggested_name}", file=sys.stderr)
            sys.stderr.flush()

        return suggested_name, suggested_id, style_hint, suggested_description, False

    # Strategy 1: Extract composer from directory structure
    directory_composer = None
    if file_path:
        directory_composer = extract_composer_from_directory(file_path)
        if directory_composer and verbose:
            print(
                f"  [Directory] Extracted composer from directory: {directory_composer}",
                file=sys.stderr,
            )
            sys.stderr.flush()

    # Strategy 2: Check filename for composer/title info using new unified identification
    # This prevents AI-generated descriptive names from overriding clearly labeled filenames
    if verbose:
        print(f"  [Filename] Extracting info from filename: {filename}", file=sys.stderr)
        sys.stderr.flush()

    # Use new unified identification module
    midi_id = None
    if file_path:
        midi_id = identify_midi_file_new(
            file_path,
            use_json=False,  # Already checked above
            use_directory=True,
            use_filename=True,
        )

    # Convert MidiIdentification to dict format for compatibility
    if midi_id:
        filename_info = {
            "composer": midi_id.composer,
            "title": midi_id.title,
            "catalog_number": midi_id.catalog_number,
            "opus": midi_id.opus,
            "movement": midi_id.movement,
            "is_classical": midi_id.is_classical,
        }
    else:
        # Fallback to old extraction method
        filename_info = extract_info_from_filename(filename)

    # If directory provided composer but filename didn't, use directory composer
    if directory_composer and not filename_info.get("composer"):
        filename_info["composer"] = directory_composer
        if verbose:
            print(f"  [Directory] Using directory composer: {directory_composer}", file=sys.stderr)
            sys.stderr.flush()

    if verbose:
        print(
            f"  [Filename] Extracted: composer={filename_info.get('composer')}, title={filename_info.get('title')}, catalog={filename_info.get('catalog_number')}, is_classical={filename_info.get('is_classical', True)}",
            file=sys.stderr,
        )
        sys.stderr.flush()

    # For original compositions, skip composer extraction from filename
    if metadata.is_original:
        if verbose:
            print(
                "  [Filename] Marked as original composition, clearing extracted info",
                file=sys.stderr,
            )
            sys.stderr.flush()
        filename_info = {
            "composer": None,
            "title": None,
            "catalog_number": None,
            "opus": None,
            "movement": None,
        }

    # If filename contains clear composer and title/catalog info, use it (skip AI descriptive names)
    has_clear_filename_info = filename_info.get("composer") and (
        filename_info.get("title") or filename_info.get("catalog_number")
    )

    if verbose:
        print(f"  [Filename] Has clear info: {has_clear_filename_info}", file=sys.stderr)
        sys.stderr.flush()

    # Strategy 3: Try AI identification/description
    # Use two-stage approach:
    # 1. Filename-based AI parsing (if filename has structure but needs parsing)
    # 2. Content-based AI identification (if filename is generic/unclear)
    if MUSIC21_AVAILABLE:
        # Set default model if not provided
        if ai_model is None:
            from pianist.ai_providers import get_default_model

            ai_model = get_default_model(ai_provider)

        # Determine which AI approach to use
        is_generic = is_filename_generic_or_unclear(filename, filename_info)

        ai_identification = None

        if not is_generic and not has_clear_filename_info:
            # Filename has structure but needs parsing/enhancement
            # Use filename-based AI parsing
            if verbose:
                print(
                    "  [AI] Using filename-based parsing (filename has structure)", file=sys.stderr
                )
                sys.stderr.flush()

            ai_identification = identify_from_filename_with_ai(
                filename=filename,
                filename_info=filename_info,
                metadata=metadata,
                composition=composition,
                provider=ai_provider,
                model=ai_model,
                verbose=verbose,
                delay_seconds=ai_delay,
            )

        if not ai_identification and (is_generic or not has_clear_filename_info):
            # Filename is generic/unclear or filename-based parsing didn't work
            # Use content-based AI identification
            if verbose:
                print(
                    f"  [AI] Using content-based identification (filename is {'generic' if is_generic else 'unclear'})",
                    file=sys.stderr,
                )
                sys.stderr.flush()

            ai_identification = identify_from_content_with_ai(
                metadata=metadata,
                composition=composition,
                filename=filename,
                provider=ai_provider,
                model=ai_model,
                verbose=verbose,
                delay_seconds=ai_delay,
                is_original=metadata.is_original,
            )
        if ai_identification:
            # Check if this is a filename-based result (has composer/title but no "identified" field)
            # or a content-based result (has "identified" field)
            is_filename_based = "identified" not in ai_identification

            if is_filename_based:
                # Filename-based parsing result - use it directly
                composer = ai_identification.get("composer", "")
                title = ai_identification.get("title", "")
                catalog = ai_identification.get("catalog_number", "")
                album = ai_identification.get("album", "")
                is_classical = ai_identification.get("is_classical", True)

                # Build full title
                if composer and title:
                    if is_classical and catalog:
                        suggested_name = f"{composer}: {title} ({catalog})"
                    elif not is_classical and album:
                        suggested_name = f"{composer}: {title} ({album})"
                    else:
                        suggested_name = f"{composer}: {title}"
                else:
                    suggested_name = title or composer or "Parsed Composition"

                style_hint = ai_identification.get("style")
                suggested_description = ai_identification.get("description", "Parsed from filename")
                ai_identified = True  # Mark as AI-identified even though it's filename-based

                # Generate ID
                suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
                suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
                suggested_id = suggested_id[:50]

                if verbose:
                    print(
                        f"  [Name] Using AI filename-parsed name: {suggested_name}", file=sys.stderr
                    )
                    sys.stderr.flush()

                return (
                    suggested_name,
                    suggested_id,
                    style_hint,
                    suggested_description,
                    ai_identified,
                )

            elif ai_identification.get("identified") and not metadata.is_original:
                # We identified a well-known composition! (only if not marked as original)
                ai_identified = True
                composer = ai_identification.get("composer", "")
                title = ai_identification.get("title", "")
                catalog = ai_identification.get("catalog_number", "")
                album = ai_identification.get("album", "")
                is_classical = ai_identification.get("is_classical", True)

                # Build full title (different format for classical vs modern)
                if composer and title:
                    if is_classical and catalog:
                        suggested_name = f"{composer}: {title} ({catalog})"
                    elif not is_classical and album:
                        suggested_name = f"{composer}: {title} ({album})"
                    elif not is_classical:
                        suggested_name = f"{composer}: {title}"
                    else:
                        suggested_name = f"{composer}: {title}"
                else:
                    suggested_name = title or composer or "Identified Composition"

                style_hint = ai_identification.get("style")
                if is_classical:
                    suggested_description = ai_identification.get(
                        "description", "Well-known classical composition"
                    )
                else:
                    suggested_description = ai_identification.get(
                        "description", "Well-known modern composition"
                    )

                # Generate ID
                suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
                suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
                suggested_id = suggested_id[:50]

                if verbose:
                    print(f"  [Name] Using AI-identified name: {suggested_name}", file=sys.stderr)
                    sys.stderr.flush()

                return (
                    suggested_name,
                    suggested_id,
                    style_hint,
                    suggested_description,
                    ai_identified,
                )
            # AI provided description (either couldn't identify, or it's an original composition)
            # Only use AI-generated descriptive names if filename doesn't have clear info
            elif has_clear_filename_info:
                # Filename has clear composer/title info, skip AI descriptive name
                # Fall through to filename extraction below
                pass
            else:
                # Filename doesn't have clear info, use AI descriptive name
                suggested_name = ai_identification.get("suggested_title", "")
                style_hint = ai_identification.get("style")
                suggested_description = ai_identification.get("description", "")

                # For original compositions, ensure the name doesn't include composer
                if metadata.is_original and suggested_name:
                    # Remove any composer names that might have been suggested
                    known_composers = [
                        "Bach",
                        "Beethoven",
                        "Mozart",
                        "Chopin",
                        "Scriabin",
                        "Debussy",
                        "Rachmaninoff",
                        "Schubert",
                        "Schumann",
                        "Liszt",
                        "Brahms",
                    ]
                    for composer in known_composers:
                        suggested_name = suggested_name.replace(composer, "").replace(
                            composer.lower(), ""
                        )
                    suggested_name = " ".join(suggested_name.split())  # Clean up extra spaces
                    if not suggested_name or len(suggested_name) < 3:
                        suggested_name = "Original Composition"

                if suggested_name:
                    suggested_id = suggested_name.lower().replace(" ", "_")
                    suggested_id = "".join(c for c in suggested_id if c.isalnum() or c == "_")
                    suggested_id = suggested_id[:50]

                    if verbose:
                        print(
                            f"  [Name] Using AI-generated descriptive name: {suggested_name}",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()

                    return (
                        suggested_name,
                        suggested_id,
                        style_hint,
                        suggested_description,
                        ai_identified,
                    )

    # Strategy 2: Extract info from filename (skip if original composition)
    # Note: filename_info was already extracted above, but we check again here for clarity
    if not has_clear_filename_info:
        if verbose:
            print(
                "  [Filename] Re-extracting info (no clear info found initially)", file=sys.stderr
            )
            sys.stderr.flush()
        filename_info = extract_info_from_filename(filename)
        if metadata.is_original:
            filename_info = {
                "composer": None,
                "title": None,
                "catalog_number": None,
                "opus": None,
                "movement": None,
            }

    if filename_info.get("composer") and (
        filename_info.get("title") or filename_info.get("catalog_number")
    ):
        # We have composer + title/catalog from filename
        composer = filename_info["composer"]
        title = filename_info.get("title", "")
        catalog = filename_info.get("catalog_number", "")

        if verbose:
            print(
                f"  [Filename] Using filename info: composer={composer}, title={title}, catalog={catalog}",
                file=sys.stderr,
            )
            sys.stderr.flush()

        # Build title with catalog if available
        if title and catalog:
            # Check if catalog is already in the title
            if catalog not in title:
                suggested_name = f"{composer}: {title} ({catalog})"
            else:
                suggested_name = f"{composer}: {title}"
        elif title:
            suggested_name = f"{composer}: {title}"
        elif catalog:
            suggested_name = f"{composer}: {catalog}"
        else:
            suggested_name = composer

        # Infer style from composer
        composer_lower = filename_info["composer"].lower()
        if "bach" in composer_lower:
            style_hint = "Baroque"
        elif "mozart" in composer_lower or "beethoven" in composer_lower:
            style_hint = "Classical"
        elif any(
            c in composer_lower for c in ["chopin", "schumann", "liszt", "rachmaninoff", "scriabin"]
        ):
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
        suggested_description = (
            ", ".join(description_parts) if description_parts else "Classical composition"
        )

        if verbose:
            print(f"  [Name] Using filename-extracted name: {suggested_name}", file=sys.stderr)
            sys.stderr.flush()

        return suggested_name, suggested_id, style_hint, suggested_description, ai_identified

    # Strategy 3: Fall back to analysis-based generation
    base_name = Path(filename).stem
    base_name = base_name.replace("_", " ").replace("-", " ").title()

    # For original compositions, ensure no composer names are included
    if metadata.is_original:
        # Remove any composer names that might have been extracted
        known_composers_lower = [
            c.lower()
            for c in [
                "bach",
                "beethoven",
                "mozart",
                "chopin",
                "scriabin",
                "debussy",
                "rachmaninoff",
                "schubert",
                "schumann",
                "liszt",
                "brahms",
            ]
        ]
        for composer in known_composers_lower:
            base_name = base_name.replace(composer.title(), "").replace(composer.upper(), "")
        base_name = " ".join(base_name.split())  # Clean up extra spaces

    # Build descriptive name
    name_parts: list[str] = []

    # For original compositions, add "Original" prefix or use descriptive name
    if metadata.is_original:
        if len(base_name) > 3 and base_name.lower() not in [
            "midi",
            "track",
            "song",
            "piece",
            "composition",
        ]:
            suggested_name = f"Original: {base_name}"
        else:
            suggested_name = "Original Composition"
    else:
        # Add key if detected
        if metadata.detected_key:
            name_parts.append(metadata.detected_key)

        # Add form if detected
        if metadata.detected_form:
            name_parts.append(metadata.detected_form.capitalize())

    # Add style hint if available
    style_hint = ""
    if not metadata.is_original and metadata.detected_key:
        # Simple heuristic: minor keys often suggest Romantic/Baroque
        if "minor" in metadata.detected_key.lower():
            style_hint = "Romantic"
        elif metadata.detected_form in ["binary", "ternary"]:
            style_hint = "Classical"

    # If we haven't set suggested_name yet (non-original compositions)
    if not metadata.is_original:
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
    if metadata.is_original:
        description_parts.append("Original composition")
    if metadata.detected_form:
        description_parts.append(f"{metadata.detected_form.capitalize()} form")
    if metadata.motif_count > 0:
        description_parts.append(f"{metadata.motif_count} motif(s)")
    if metadata.phrase_count > 0:
        description_parts.append(f"{metadata.phrase_count} phrase(s)")
    if metadata.chord_count > 0:
        description_parts.append(f"{metadata.chord_count} chord(s)")

    suggested_description = (
        ", ".join(description_parts)
        if description_parts
        else ("Original composition" if metadata.is_original else "Musical composition")
    )

    return suggested_name, suggested_id, style_hint, suggested_description, ai_identified


def analyze_file(
    file_path: Path,
    verbose: bool = False,
    ai_provider: str = "gemini",
    ai_model: str | None = None,
    ai_delay: float = 0.0,
    mark_original: bool = False,
) -> tuple[FileMetadata, list[int], bool, bool]:
    """
    Analyze a single MIDI file and extract metadata.

    Uses comprehensive_analysis module for core analysis, then adds
    database curation-specific features (melodic signature, name generation).

    Returns:
        (metadata, melodic_signature, ai_attempted, ai_identified)
    """
    if verbose:
        print(f"  [Analyze] Starting analysis of {file_path.name}...", file=sys.stderr)
        sys.stderr.flush()

    # Load composition ONCE and reuse it everywhere (major performance improvement for large files)
    composition = None
    melodic_signature: list[int] = []

    if MUSIC21_AVAILABLE:
        try:
            if verbose:
                print("  [Analyze] Loading composition from MIDI...", file=sys.stderr)
                sys.stderr.flush()
                load_start = time.time()
            composition = composition_from_midi(file_path)
            if verbose:
                print(
                    f"  [Timing] Load composition from MIDI: {time.time() - load_start:.2f}s",
                    file=sys.stderr,
                )

            # Extract melodic signature for duplicate detection
            # Convert to music21 stream once and reuse for signature extraction
            if verbose:
                sig_start = time.time()
            from pianist.musical_analysis import _composition_to_music21_stream

            music21_stream = _composition_to_music21_stream(composition)
            melodic_signature = extract_melodic_signature(
                composition, music21_stream=music21_stream
            )
            if verbose:
                print(
                    f"  [Timing] Extract melodic signature: {time.time() - sig_start:.2f}s",
                    file=sys.stderr,
                )
        except Exception:
            # Analysis failed, continue without composition
            pass

    # Use comprehensive analysis for core analysis
    # Pass composition to avoid reloading (major performance improvement)
    # Note: analyze_for_user doesn't support AI quality assessment yet,
    # so we handle that separately if needed
    if verbose:
        print("  [Analyze] Running comprehensive analysis...", file=sys.stderr)
        sys.stderr.flush()
        comprehensive_start = time.time()
    comprehensive_result = analyze_for_user(
        file_path,
        ai_provider=ai_provider,
        ai_model=ai_model,
        composition=composition,  # Reuse loaded composition
        verbose=verbose,
    )
    if verbose:
        print(
            f"  [Timing] Comprehensive analysis: {time.time() - comprehensive_start:.2f}s",
            file=sys.stderr,
        )

    # Get quality report (with AI if requested)
    # Pass composition and musical analysis to avoid reloading/recomputation (major performance improvement)
    # Extract musical analysis from comprehensive result if available
    musical_analysis = None
    if comprehensive_result.get("musical_analysis"):
        # Reconstruct MusicalAnalysis object from dict to avoid recomputation
        musical_analysis = _reconstruct_musical_analysis(comprehensive_result["musical_analysis"])

    if verbose:
        print("  [Analyze] Running quality check...", file=sys.stderr)
        sys.stderr.flush()
        quality_start = time.time()
    # Get quality report with AI assessment
    quality_report = check_midi_file(
        file_path,
        provider=ai_provider,
        model=ai_model,
        composition=composition,
        musical_analysis=musical_analysis,
    )
    if verbose:
        print(f"  [Timing] Quality check: {time.time() - quality_start:.2f}s", file=sys.stderr)

    # Extract data from comprehensive analysis result
    technical = comprehensive_result.get("technical", {})
    comprehensive_result.get("quality", {})
    musical = comprehensive_result.get("musical_analysis", {})
    ai_insights = comprehensive_result.get("ai_insights")

    # Extract metadata from comprehensive analysis
    detected_key = musical.get("detected_key")
    detected_form = musical.get("detected_form")
    motif_count = musical.get("motif_count", 0)
    phrase_count = musical.get("phrase_count", 0)
    chord_count = musical.get("chord_count", 0)
    harmonic_progression = musical.get("harmonic_progression")

    tempo_bpm = technical.get("tempo_bpm")
    time_sig = technical.get("time_signature")
    key_sig = technical.get("key_signature")

    # Track AI usage
    ai_attempted = False
    ai_identified = False

    # Check if this is an original composition
    # Use command-line flag if provided, otherwise auto-detect from filename
    is_original = mark_original or is_original_composition(file_path.name)

    # Generate suggested name
    if composition:
        # Create temporary metadata for name generation
        temp_metadata = FileMetadata(
            filename=file_path.name,
            filepath=str(file_path),
            quality_score=quality_report.overall_score,
            quality_issues=len(quality_report.issues),
            duration_beats=technical.get("duration_beats", 0.0),
            duration_seconds=technical.get("duration_seconds", 0.0),
            bars=technical.get("bars", 0.0),
            tempo_bpm=tempo_bpm,
            time_signature=time_sig,
            key_signature=key_sig,
            tracks=technical.get("tracks", 0),
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
            is_original=is_original,
        )

        # Track if AI is being used
        # Generate suggested name using AI
        if MUSIC21_AVAILABLE:
            ai_attempted = True

        # Check if filename has clear info that should take priority over AI
        filename_info = extract_info_from_filename(file_path.name)
        has_clear_filename_info = filename_info.get("composer") and (
            filename_info.get("title") or filename_info.get("catalog_number")
        )

        if verbose:
            print(
                f"  [Filename] Has clear info: {has_clear_filename_info} (composer={filename_info.get('composer')}, title={filename_info.get('title')}, catalog={filename_info.get('catalog_number')})",
                file=sys.stderr,
            )
            sys.stderr.flush()

        # Use AI to enhance names (even if filename has clear info)
        if True:
            if has_clear_filename_info:
                # Filename has clear info - use AI to enhance it
                if verbose:
                    print(
                        "  [AI] Filename has clear info, using AI to enhance name", file=sys.stderr
                    )
                    sys.stderr.flush()

                # Use AI to enhance the filename-extracted name
                enhanced_info = enhance_name_with_ai(
                    filename_info,
                    temp_metadata,
                    composition,
                    file_path.name,
                    provider=ai_provider,
                    model=ai_model,
                    verbose=verbose,
                    delay_seconds=ai_delay,
                )

                if enhanced_info:
                    # Use AI-enhanced name
                    title = enhanced_info.get("title", "")
                    catalog = enhanced_info.get("catalog_number", "")
                    ai_composer = enhanced_info.get("composer", "")

                    # CRITICAL: Always use filename-extracted composer as the source of truth
                    # The AI might not return composer, or might return a different format
                    # We prefer the filename-extracted composer since it's what the user named the file
                    filename_composer = filename_info.get("composer", "")
                    if filename_composer:
                        composer = filename_composer
                        if verbose and ai_composer and ai_composer != filename_composer:
                            print(
                                f"  [AI] Using filename composer '{filename_composer}' instead of AI composer '{ai_composer}'",
                                file=sys.stderr,
                            )
                            sys.stderr.flush()
                    elif ai_composer:
                        composer = ai_composer
                        if verbose:
                            print(
                                f"  [AI] Using AI composer '{ai_composer}' (filename had no composer)",
                                file=sys.stderr,
                            )
                            sys.stderr.flush()
                    else:
                        composer = ""
                        if verbose:
                            print(
                                "  [AI] Warning: No composer found in filename or AI response",
                                file=sys.stderr,
                            )
                            sys.stderr.flush()

                    # Strip composer name from title if AI included it (defensive check)
                    if composer and title:
                        # Remove composer name from title if present
                        composer_variations = [
                            composer,
                            composer.split()[-1] if " " in composer else composer,  # Last name only
                        ]
                        for comp_var in composer_variations:
                            # Remove patterns like "Composer: " or "Composer - " from title
                            title = re.sub(
                                rf"^{re.escape(comp_var)}\s*[:-]\s*", "", title, flags=re.IGNORECASE
                            )
                            title = re.sub(
                                rf"^{re.escape(comp_var)}\s+", "", title, flags=re.IGNORECASE
                            )
                        title = title.strip()

                    if composer and title:
                        if catalog:
                            suggested_name = f"{composer}: {title} ({catalog})"
                        else:
                            suggested_name = f"{composer}: {title}"
                    elif composer:
                        # If we have composer but no title, use catalog or just composer
                        suggested_name = f"{composer}: {catalog}" if catalog else composer
                    elif title:
                        # If we have title but no composer, this shouldn't happen but handle it
                        suggested_name = title
                    else:
                        # Fallback to filename-extracted name if AI enhancement failed
                        composer = filename_info.get("composer", "")
                        title = filename_info.get("title", "")
                        catalog = filename_info.get("catalog_number", "")
                        if title and catalog:
                            suggested_name = f"{composer}: {title} ({catalog})"
                        elif title:
                            suggested_name = f"{composer}: {title}"
                        elif catalog:
                            suggested_name = f"{composer}: {catalog}"
                        else:
                            suggested_name = composer

                    suggested_style = enhanced_info.get("style")
                    suggested_description = enhanced_info.get("description", "")
                    ai_identified = True
                else:
                    # AI enhancement failed, fall back to filename-extracted name
                    if verbose:
                        print(
                            "  [AI] AI enhancement failed, using filename-extracted name",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()
                    composer = filename_info["composer"]
                    title = filename_info.get("title", "")
                    catalog = filename_info.get("catalog_number", "")

                    if title and catalog:
                        suggested_name = f"{composer}: {title} ({catalog})"
                    elif title:
                        suggested_name = f"{composer}: {title}"
                    elif catalog:
                        suggested_name = f"{composer}: {catalog}"
                    else:
                        suggested_name = composer

                    # Infer style from composer
                    composer_lower = filename_info["composer"].lower()
                    if "bach" in composer_lower:
                        suggested_style = "Baroque"
                    elif "mozart" in composer_lower or "beethoven" in composer_lower:
                        suggested_style = "Classical"
                    elif any(
                        c in composer_lower
                        for c in ["chopin", "schumann", "liszt", "rachmaninoff", "scriabin"]
                    ):
                        suggested_style = "Romantic"
                    else:
                        suggested_style = None

                    description_parts = []
                    if filename_info.get("title"):
                        description_parts.append(filename_info["title"])
                    if detected_form:
                        description_parts.append(f"{detected_form} form")
                    suggested_description = (
                        ", ".join(description_parts)
                        if description_parts
                        else "Classical composition"
                    )
                    ai_identified = False

                    if verbose:
                        print(
                            f"  [Name] Using filename-extracted name: {suggested_name}",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()

                # Generate ID for filename-extracted or AI-enhanced names
                suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
                suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
                suggested_id = suggested_id[:50]
            # Filename doesn't have clear info - use AI insights from comprehensive analysis
            elif ai_insights:
                if verbose:
                    print(
                        "  [AI] Using AI insights from comprehensive analysis (filename has no clear info)",
                        file=sys.stderr,
                    )
                    sys.stderr.flush()
                suggested_name = ai_insights.get("suggested_name", Path(file_path).stem)
                suggested_style = ai_insights.get("suggested_style")
                suggested_description = ai_insights.get("suggested_description")
                ai_identified = True
                # Generate ID
                suggested_id = (
                    suggested_name.lower().replace(" ", "_").replace("'", "").replace(",", "")
                )
                suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
                suggested_id = suggested_id[:50]
            else:
                # No AI insights available, use generate_suggested_name
                if verbose:
                    naming_start = time.time()
                (
                    suggested_name,
                    suggested_id,
                    suggested_style,
                    suggested_description,
                    ai_identified,
                ) = generate_suggested_name(
                    temp_metadata,
                    composition,
                    verbose=verbose,
                    ai_provider=ai_provider,
                    ai_model=ai_model,
                    ai_delay=ai_delay,
                )
                if verbose:
                    print(
                        f"  [Timing] Generate suggested name: {time.time() - naming_start:.2f}s",
                        file=sys.stderr,
                    )
                    print(f"  [Name] Generated name: {suggested_name}", file=sys.stderr)
                    sys.stderr.flush()

            if verbose:
                print(f"  [Name] Final name: {suggested_name}", file=sys.stderr)
                sys.stderr.flush()
        elif has_clear_filename_info:
            # No AI enabled, use filename-extracted info directly
            if verbose:
                print(
                    "  [Filename] Using filename-extracted info (AI not enabled)", file=sys.stderr
                )
                sys.stderr.flush()
            composer = filename_info["composer"]
            title = filename_info.get("title", "")
            catalog = filename_info.get("catalog_number", "")

            # Build title with catalog if available
            if title and catalog:
                if catalog not in title:
                    suggested_name = f"{composer}: {title} ({catalog})"
                else:
                    suggested_name = f"{composer}: {title}"
            elif title:
                suggested_name = f"{composer}: {title}"
            elif catalog:
                suggested_name = f"{composer}: {catalog}"
            else:
                suggested_name = composer

            # Infer style from composer
            composer_lower = filename_info["composer"].lower()
            if "bach" in composer_lower:
                suggested_style = "Baroque"
            elif "mozart" in composer_lower or "beethoven" in composer_lower:
                suggested_style = "Classical"
            elif any(
                c in composer_lower
                for c in ["chopin", "schumann", "liszt", "rachmaninoff", "scriabin"]
            ):
                suggested_style = "Romantic"
            else:
                suggested_style = None

            suggested_id = suggested_name.lower().replace(" ", "_").replace(":", "_")
            suggested_id = "".join(c for c in suggested_id if c.isalnum() or c in ["_", "-"])
            suggested_id = suggested_id[:50]

            # Build description
            description_parts = []
            if filename_info.get("title"):
                description_parts.append(filename_info["title"])
            if detected_form:
                description_parts.append(f"{detected_form} form")
            suggested_description = (
                ", ".join(description_parts) if description_parts else "Classical composition"
            )
            ai_identified = False

            if verbose:
                print(f"  [Name] Using filename-extracted name: {suggested_name}", file=sys.stderr)
                sys.stderr.flush()
        else:
            if verbose:
                naming_start = time.time()
            suggested_name, suggested_id, suggested_style, suggested_description, ai_identified = (
                generate_suggested_name(
                    temp_metadata,
                    composition,
                    verbose=verbose,
                    ai_provider=ai_provider,
                    ai_model=ai_model,
                    ai_delay=ai_delay,
                )
            )
            if verbose:
                print(
                    f"  [Timing] Generate suggested name: {time.time() - naming_start:.2f}s",
                    file=sys.stderr,
                )
    # Use AI insights if available, otherwise use filename
    # Use AI insights if available
    elif ai_insights:
        if verbose:
            print(
                "  [AI] Using AI insights from comprehensive analysis (no composition available)",
                file=sys.stderr,
            )
            sys.stderr.flush()
        suggested_name = ai_insights.get("suggested_name", Path(file_path).stem)
        suggested_style = ai_insights.get("suggested_style")
        suggested_description = ai_insights.get("suggested_description")
        suggested_id = suggested_name.lower().replace(" ", "_").replace("'", "").replace(",", "")
        ai_identified = True
        if verbose:
            print(
                f"  [Name] Using AI-generated name from comprehensive analysis: {suggested_name}",
                file=sys.stderr,
            )
            sys.stderr.flush()
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
        duration_beats=technical.get("duration_beats", 0.0),
        duration_seconds=technical.get("duration_seconds", 0.0),
        bars=technical.get("bars", 0.0),
        tempo_bpm=tempo_bpm,
        time_signature=time_sig,
        key_signature=key_sig,
        tracks=technical.get("tracks", 0),
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
        is_original=is_original,
    )

    return metadata, melodic_signature, ai_attempted, ai_identified


def retry_ai_naming_only(
    file_path: Path,
    cached_metadata: FileMetadata,
    cached_signature: list[int],  # noqa: ARG001
    verbose: bool = False,
    ai_provider: str = "gemini",
    ai_model: str | None = None,
    ai_delay: float = 0.0,
) -> tuple[FileMetadata, bool, bool]:
    """
    Retry only the AI naming part without re-running the full analysis.

    This is used when --retry-ai or --force-ai is specified to avoid
    re-running expensive music21 analysis.

    Returns:
        (updated_metadata, ai_attempted, ai_identified)
    """
    # Get composition for name generation (only if we need it)
    composition = None
    if MUSIC21_AVAILABLE:
        from contextlib import suppress

        with suppress(Exception):
            composition = composition_from_midi(file_path)

    # Generate suggested name with AI
    ai_attempted = False
    ai_identified = False

    if composition and MUSIC21_AVAILABLE:
        ai_attempted = True

        # Use generate_suggested_name with AI enabled
        suggested_name, suggested_id, suggested_style, suggested_description, ai_identified = (
            generate_suggested_name(
                cached_metadata,
                composition,
                verbose=verbose,
                ai_provider=ai_provider,
                ai_model=ai_model,
                ai_delay=ai_delay,
            )
        )
    else:
        # Can't use AI without composition, use fallback
        suggested_name = cached_metadata.suggested_name
        suggested_id = cached_metadata.suggested_id
        suggested_style = cached_metadata.suggested_style
        suggested_description = cached_metadata.suggested_description

    # Create updated metadata with new AI results
    updated_metadata = FileMetadata(
        filename=cached_metadata.filename,
        filepath=cached_metadata.filepath,
        quality_score=cached_metadata.quality_score,
        quality_issues=cached_metadata.quality_issues,
        duration_beats=cached_metadata.duration_beats,
        duration_seconds=cached_metadata.duration_seconds,
        bars=cached_metadata.bars,
        tempo_bpm=cached_metadata.tempo_bpm,
        time_signature=cached_metadata.time_signature,
        key_signature=cached_metadata.key_signature,
        tracks=cached_metadata.tracks,
        detected_key=cached_metadata.detected_key,
        detected_form=cached_metadata.detected_form,
        motif_count=cached_metadata.motif_count,
        phrase_count=cached_metadata.phrase_count,
        chord_count=cached_metadata.chord_count,
        harmonic_progression=cached_metadata.harmonic_progression,
        suggested_name=suggested_name,
        suggested_id=suggested_id,
        suggested_style=suggested_style,
        suggested_description=suggested_description,
        similar_files=cached_metadata.similar_files.copy(),
        similarity_scores=cached_metadata.similarity_scores.copy(),
        is_duplicate=cached_metadata.is_duplicate,
        duplicate_group=cached_metadata.duplicate_group,
        technical_score=cached_metadata.technical_score,
        musical_score=cached_metadata.musical_score,
        structure_score=cached_metadata.structure_score,
        is_original=cached_metadata.is_original,
    )

    return updated_metadata, ai_attempted, ai_identified


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
    Checks metadata to avoid false positives (different pieces that are musically similar).
    """
    # Compare new file against all existing files
    for existing_meta, existing_sig in zip(existing_metadata, existing_signatures, strict=False):
        similarity = calculate_similarity(new_metadata, existing_meta, new_signature, existing_sig)

        if similarity >= similarity_threshold:
            # Check if they're actually different pieces before marking as duplicates
            name1 = new_metadata.suggested_name or ""
            name2 = existing_meta.suggested_name or ""
            if are_different_pieces(name1, name2):
                # Musically similar but different pieces - don't mark as duplicates
                continue

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
    Filters out false positives (different pieces) before grouping.
    """
    groups: dict[str, list[int]] = defaultdict(list)
    group_counter = 0

    # First pass: filter out false positives from all similar_files relationships
    for _i, meta in enumerate(all_metadata):
        if meta.similar_files:
            name1 = meta.suggested_name or ""
            filtered_similar = []
            for similar_filename in meta.similar_files:
                # Find the metadata for this similar file
                similar_meta = next(
                    (m for m in all_metadata if m.filename == similar_filename), None
                )
                if similar_meta:
                    name2 = similar_meta.suggested_name or ""
                    # Only keep if they're NOT different pieces
                    if not are_different_pieces(name1, name2):
                        filtered_similar.append(similar_filename)
                    else:
                        # Remove from the other file's list too (clean up both sides)
                        if meta.filename in similar_meta.similar_files:
                            similar_meta.similar_files.remove(meta.filename)
                        if meta.filename in similar_meta.similarity_scores:
                            del similar_meta.similarity_scores[meta.filename]

            # Update similar_files to only include legitimate duplicates
            meta.similar_files = filtered_similar

    # Second pass: assign groups (only files with legitimate similar_files)
    for i, meta in enumerate(all_metadata):
        if not meta.similar_files:
            continue

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
    Checks metadata to avoid false positives (different pieces that are musically similar).
    """
    # Compare all pairs
    for i, (meta1, sig1) in enumerate(zip(all_metadata, all_signatures, strict=False)):
        for j, (meta2, sig2) in enumerate(zip(all_metadata, all_signatures, strict=False)):
            if i >= j:
                continue

            similarity = calculate_similarity(meta1, meta2, sig1, sig2)

            if similarity >= similarity_threshold:
                # Check if they're actually different pieces before marking as duplicates
                name1 = meta1.suggested_name or ""
                name2 = meta2.suggested_name or ""
                if are_different_pieces(name1, name2):
                    # Musically similar but different pieces - don't mark as duplicates
                    continue

                meta1.similar_files.append(meta2.filename)
                meta1.similarity_scores[meta2.filename] = similarity
                meta2.similar_files.append(meta1.filename)
                meta2.similarity_scores[meta1.filename] = similarity

    # Assign duplicate groups
    assign_duplicate_groups(all_metadata)


def are_different_pieces(name1: str, name2: str) -> bool:
    """
    Check if two files represent different pieces (not duplicates).

    This prevents false positives where musically similar pieces are incorrectly
    grouped as duplicates (e.g., prelude vs prelude+fugue, movement vs full work).

    Returns True if they are different pieces and should NOT be considered duplicates.
    """
    name1_lower = name1.lower()
    name2_lower = name2.lower()

    # Check for prelude vs prelude+fugue
    has_prelude_only_1 = "prelude" in name1_lower and "fugue" not in name1_lower
    has_prelude_fugue_1 = "prelude" in name1_lower and "fugue" in name1_lower
    has_prelude_only_2 = "prelude" in name2_lower and "fugue" not in name2_lower
    has_prelude_fugue_2 = "prelude" in name2_lower and "fugue" in name2_lower

    if (has_prelude_only_1 and has_prelude_fugue_2) or (has_prelude_fugue_1 and has_prelude_only_2):
        return True

    # Check for movement vs full work
    movement_indicators = [
        "i.",
        "ii.",
        "iii.",
        "iv.",
        "v.",
        "allegro",
        "andante",
        "adagio",
        "presto",
        "largo",
        "movement",
    ]
    has_movement_1 = any(indicator in name1_lower for indicator in movement_indicators)
    has_movement_2 = any(indicator in name2_lower for indicator in movement_indicators)

    # Check if one is a full work (has "sonata", "suite", etc. but no movement indicator)
    has_full_work_1 = (
        any(x in name1_lower for x in ["sonata", "suite", "concerto"]) and not has_movement_1
    )
    has_full_work_2 = (
        any(x in name2_lower for x in ["sonata", "suite", "concerto"]) and not has_movement_2
    )

    if (has_movement_1 and has_full_work_2) or (has_full_work_1 and has_movement_2):
        return True

    # Check for collection vs single piece
    # Collections have: "nos.", "nos 1-2", "24 preludes", "3 nocturnes", etc.
    # Single pieces have: "no. 1", "op. 9, no. 1" (but not "nos.")
    collection_indicators = [
        "nos.",
        "nos ",  # Multiple numbers
        "24 preludes",
        "3 nocturnes",
        "5 mazurkas",  # Explicit counts
    ]
    has_collection_1 = any(indicator in name1_lower for indicator in collection_indicators)
    has_collection_2 = any(indicator in name2_lower for indicator in collection_indicators)

    # Check if it's a single piece (has "no. X" but not "nos.")
    # Single pieces typically have format like "Op. 9, No. 1" or end with "No. X"
    is_single_1 = (
        ":" in name1 and not has_collection_1 and ("no. " in name1_lower or ", no. " in name1_lower)
    )
    is_single_2 = (
        ":" in name2 and not has_collection_2 and ("no. " in name2_lower or ", no. " in name2_lower)
    )

    # Also check for explicit collection patterns
    explicit_collection_1 = any(
        x in name1_lower
        for x in ["24 preludes", "3 nocturnes", "5 mazurkas", "nos. 1-2", "nos 1-2"]
    )
    explicit_collection_2 = any(
        x in name2_lower
        for x in ["24 preludes", "3 nocturnes", "5 mazurkas", "nos. 1-2", "nos 1-2"]
    )

    # If one is explicitly a collection and the other is a single piece, they're different
    return bool((explicit_collection_1 and is_single_2) or (is_single_1 and explicit_collection_2))


def filter_duplicates_and_quality(
    all_metadata: list[FileMetadata],
    min_quality: float = 0.0,
    verbose: bool = False,
) -> list[FileMetadata]:
    """
    Filter dataset to remove duplicates and low-quality files.

    Args:
        all_metadata: List of FileMetadata objects
        min_quality: Minimum quality score to keep (default: 0.0 = no filtering)
        verbose: Print detailed progress

    Returns:
        Filtered list of FileMetadata objects
    """
    original_count = len(all_metadata)

    # Filter by quality
    if min_quality > 0:
        all_metadata = [m for m in all_metadata if m.quality_score >= min_quality]
        if verbose:
            print(
                f"Filtered {original_count - len(all_metadata)} files below quality threshold {min_quality}"
            )

    # Group by duplicate_group
    duplicate_groups: dict[str, list[FileMetadata]] = defaultdict(list)
    non_duplicates: list[FileMetadata] = []

    for meta in all_metadata:
        if meta.duplicate_group:
            duplicate_groups[meta.duplicate_group].append(meta)
        else:
            non_duplicates.append(meta)

    if not duplicate_groups:
        return all_metadata

    if verbose:
        print(
            f"Found {len(duplicate_groups)} duplicate groups with {sum(len(files) for files in duplicate_groups.values())} files"
        )
        print(f"Found {len(non_duplicates)} non-duplicate files")

    # Process duplicate groups - keep only the best file from each group
    kept_files: list[FileMetadata] = []

    for _group_name, files in duplicate_groups.items():
        if len(files) < 2:
            # Single file in group - treat as non-duplicate
            files[0].is_duplicate = False
            files[0].duplicate_group = ""
            files[0].similar_files = []
            files[0].similarity_scores = {}
            non_duplicates.extend(files)
            continue

            # All groups at this point are legitimate duplicates (false positives prevented during detection)
            # Keep only the best one
            # Sort by quality score (descending)
            sorted_files = sorted(files, key=lambda m: m.quality_score, reverse=True)

            # If there's a clear winner (quality difference > 0.01), use it
            best_file = sorted_files[0]
            if len(sorted_files) > 1:
                best_quality = sorted_files[0].quality_score
                second_quality = sorted_files[1].quality_score
                if best_quality - second_quality <= 0.01:
                    # Tie - prefer files with better filenames (no typos)
                    typos = ["prlude", "frdric", "gymnopdie"]
                    for f in sorted_files:
                        filename_lower = f.filename.lower()
                        if not any(typo in filename_lower for typo in typos):
                            best_file = f
                            break

            # Clear duplicate flags for the kept file
            best_file.is_duplicate = False
            best_file.duplicate_group = ""
            best_file.similar_files = []
            best_file.similarity_scores = {}
            kept_files.append(best_file)

    if verbose:
        print(
            f"Reduced {len(duplicate_groups)} duplicate groups to {len(kept_files)} files (kept best file from each group)"
        )

    # Combine kept files with non-duplicates
    final_files = non_duplicates + kept_files

    if verbose:
        print(f"\nFiltered dataset: {len(final_files)} files (reduced from {original_count})")
        print(
            f"Reduction: {original_count - len(final_files)} files removed ({100 * (original_count - len(final_files)) / original_count:.1f}%)"
        )

    return final_files


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
            ],
        )
        writer.writeheader()

        for meta in all_metadata:
            # Format similarity scores as "file1: 0.85; file2: 0.72"
            similarity_scores_str = "; ".join(
                f"{filename}: {score:.3f}" for filename, score in meta.similarity_scores.items()
            )

            writer.writerow(
                {
                    "filename": meta.filename,
                    "filepath": meta.filepath,
                    "quality_score": f"{meta.quality_score:.3f}",
                    "quality_issues": meta.quality_issues,
                    "suggested_name": meta.suggested_name,
                    "suggested_id": meta.suggested_id,
                    "suggested_style": meta.suggested_style or "",
                    "suggested_description": meta.suggested_description or "",
                    "detected_key": meta.detected_key or "",
                    "detected_form": meta.detected_form or "",
                    "duration_beats": f"{meta.duration_beats:.1f}",
                    "duration_seconds": f"{meta.duration_seconds:.2f}",
                    "bars": f"{meta.bars:.1f}",
                    "tempo_bpm": f"{meta.tempo_bpm:.1f}" if meta.tempo_bpm else "",
                    "time_signature": meta.time_signature or "",
                    "key_signature": meta.key_signature or "",
                    "tracks": meta.tracks,
                    "motif_count": meta.motif_count,
                    "phrase_count": meta.phrase_count,
                    "chord_count": meta.chord_count,
                    "harmonic_progression": (meta.harmonic_progression or "")[
                        :200
                    ],  # Limit length for CSV readability
                    "is_duplicate": "Yes" if meta.is_duplicate else "No",
                    "duplicate_group": meta.duplicate_group or "",
                    "similar_files": "; ".join(meta.similar_files),
                    "similarity_scores": similarity_scores_str,
                    "technical_score": f"{meta.technical_score:.3f}",
                    "musical_score": f"{meta.musical_score:.3f}",
                    "structure_score": f"{meta.structure_score:.3f}",
                    "is_original": "Yes" if meta.is_original else "No",
                }
            )


def write_json_report(
    all_metadata: list[FileMetadata],
    output_path: Path,
) -> None:
    """Write JSON report with all metadata."""
    data = {
        "total_files": len(all_metadata),
        "duplicate_groups": len({m.duplicate_group for m in all_metadata if m.duplicate_group}),
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
        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct metadata
        metadata_dict = data["metadata"]
        # Handle backward compatibility: if is_original field is missing, auto-detect from filename
        if "is_original" not in metadata_dict:
            metadata_dict["is_original"] = is_original_composition(
                Path(metadata_dict.get("filepath", "")).name
            )
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
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)

            metadata_dict = data["metadata"]
            # Handle backward compatibility: if is_original field is missing, auto-detect from filename
            if "is_original" not in metadata_dict:
                metadata_dict["is_original"] = is_original_composition(
                    Path(metadata_dict.get("filepath", "")).name
                )
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

    # Import config system
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from pianist.config import get_ai_delay, get_ai_model, get_ai_provider

    parser.add_argument(
        "--ai-provider",
        type=str,
        choices=["gemini", "ollama", "openrouter"],
        default=None,
        help=f"AI provider to use: 'gemini' (cloud), 'ollama' (local), or 'openrouter' (cloud). Defaults to config file or '{get_ai_provider()}'. AI is always used for quality assessment and naming.",
    )

    parser.add_argument(
        "--ai-model",
        type=str,
        default=None,
        help="AI model name. Defaults to config file or provider default (mistralai/devstral-2512:free for OpenRouter). Free OpenRouter options: mistralai/devstral-2512:free (recommended), xiaomi/mimo-v2-flash:free, tngtech/deepseek-r1t2-chimera:free, nex-agi/deepseek-v3.1-nex-n1:free",
    )

    parser.add_argument(
        "--ai-delay",
        type=float,
        default=None,
        help=f"Delay in seconds between AI calls to avoid rate limits. Defaults to config file or {get_ai_delay()}.",
    )

    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for duplicate detection (0.0-1.0, default: 0.7)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
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
        "--mark-original",
        action="store_true",
        help="Mark all files as original/unknown compositions (skip AI identification and composer name suggestions)",
    )

    parser.add_argument(
        "--filter-duplicates",
        action="store_true",
        help="Filter out duplicate files, keeping only the best file from each duplicate group",
    )

    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.0,
        help="Minimum quality score to keep when filtering (default: 0.0 = no quality filtering)",
    )

    args = parser.parse_args()

    # Set up temp directory
    temp_dir = args.temp_dir or Path(".midi_review_cache")

    # Clear cache if requested
    if args.clear_cache:
        print("Clearing cached results...")
        sys.stdout.flush()
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
        files = files[: args.limit]
        print(f"Testing mode: Limited to first {args.limit} files")
        sys.stdout.flush()

    print(f"Found {len(files)} MIDI file(s) to analyze")
    sys.stdout.flush()

    # Load existing results if resuming
    existing_results: dict[str, tuple[FileMetadata, list[int], bool, bool]] = {}
    if args.resume:
        print("Loading existing results...")
        sys.stdout.flush()
        # Load all cached results
        for result_file in temp_dir.glob("*.json") if temp_dir.exists() else []:
            try:
                with open(result_file, encoding="utf-8") as f:
                    data = json.load(f)

                source_file = data.get("source_file")
                if source_file:
                    metadata_dict = data["metadata"]
                    # Handle backward compatibility: if is_original field is missing, auto-detect from filename
                    if "is_original" not in metadata_dict:
                        metadata_dict["is_original"] = is_original_composition(
                            Path(source_file).name
                        )
                    metadata = FileMetadata(**metadata_dict)
                    signature = data.get("signature", [])
                    ai_attempted = data.get("ai_attempted", False)
                    ai_identified = data.get("ai_identified", False)
                    existing_results[source_file] = (
                        metadata,
                        signature,
                        ai_attempted,
                        ai_identified,
                    )
            except Exception:
                continue
        print(f"Found {len(existing_results)} previously analyzed files")
        sys.stdout.flush()

        # Check if loaded files need duplicate detection (in case script was interrupted)
        # We check if any file has duplicate_group set - if none do, duplicate detection was never run
        # This is more reliable than checking similar_files/is_duplicate, as files without duplicates
        # will legitimately have empty similar_files and is_duplicate=False
        loaded_metadata_list = [meta for meta, _, _, _ in existing_results.values()]
        needs_duplicate_detection = len(loaded_metadata_list) > 1 and not any(
            meta.duplicate_group is not None for meta in loaded_metadata_list
        )
        if needs_duplicate_detection:
            if args.verbose:
                print("Running duplicate detection on loaded files...")
                sys.stdout.flush()
            loaded_signatures_list = [sig for _, sig, _, _ in existing_results.values()]
            detect_duplicates(
                loaded_metadata_list, loaded_signatures_list, args.similarity_threshold
            )
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
        if args.resume and file_str in existing_results:
            meta, sig, _cached_ai_attempted, _cached_ai_identified = existing_results[file_str]

            # Check if this file should be treated as original composition
            # (either from cached metadata, command-line flag, or filename detection)
            (meta.is_original or args.mark_original or is_original_composition(file_path.name))

            # Normal resume - skip already analyzed files
            if args.verbose:
                print(f"[{i}/{len(files)}] Skipping (already analyzed): {file_path.name}")
                sys.stdout.flush()
            all_metadata.append(meta)
            all_signatures.append(sig)
            skipped_count += 1
            continue

        # Analyze new file (or re-analyze with AI)
        print(f"[{i}/{len(files)}] Analyzing: {file_path.name}")
        sys.stdout.flush()

        try:
            start_time = time.time()

            # Get provider and model from args or config
            from pianist.ai_providers import get_default_model
            from pianist.config import get_ai_model, get_ai_provider

            ai_provider = args.ai_provider or get_ai_provider()
            ai_model = args.ai_model or get_ai_model(ai_provider) or get_default_model(ai_provider)
            ai_delay = args.ai_delay if args.ai_delay is not None else get_ai_delay()

            # Run analysis with AI (always used)
            metadata, signature, ai_attempted, ai_identified = analyze_file(
                file_path,
                verbose=args.verbose,
                ai_provider=ai_provider,
                ai_model=ai_model,
                ai_delay=ai_delay,
                mark_original=args.mark_original,
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

            # Note: We don't call assign_duplicate_groups here because it reassigns group numbers
            # from scratch each time, which could cause group names to change as more files are processed.
            # Instead, we call it once at the end to ensure stable group assignments.

            # Save result immediately (includes duplicate detection results)
            save_file_result(metadata, signature, temp_dir, file_path, ai_attempted, ai_identified)

            analyzed_count += 1
        except KeyboardInterrupt:
            print(
                f"\n\nInterrupted! Progress saved. {analyzed_count} files analyzed, {skipped_count} skipped."
            )
            print("Run with --resume to continue from here.")
            # Still write what we have so far
            if all_metadata:
                # Filter duplicates and quality if requested
                if args.filter_duplicates:
                    if args.verbose:
                        print("\nFiltering duplicates and low-quality files...")
                    all_metadata = filter_duplicates_and_quality(
                        all_metadata,
                        min_quality=args.min_quality,
                        verbose=args.verbose,
                    )
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

    print("\nAnalysis complete:")
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
        print(
            f"Warning: all_metadata ({len(all_metadata)}) and all_signatures ({len(all_signatures)}) have different lengths",
            file=sys.stderr,
        )

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
    print("\nSummary:")
    print(f"  Total files: {len(all_metadata)}")
    print(f"  Duplicates found: {len(duplicates)}")
    print(f"  Unique files: {len(all_metadata) - len(duplicates)}")

    if duplicates:
        print("\nDuplicate groups:")
        groups = defaultdict(list)
        for meta in duplicates:
            if meta.duplicate_group:
                groups[meta.duplicate_group].append(meta.filename)
        for group_name, filenames in groups.items():
            print(f"  {group_name}: {', '.join(filenames)}")

    # Filter duplicates and quality if requested
    if args.filter_duplicates:
        if args.verbose:
            print("\nFiltering duplicates and low-quality files...")
        all_metadata = filter_duplicates_and_quality(
            all_metadata,
            min_quality=args.min_quality,
            verbose=args.verbose,
        )

    # Write reports
    output_csv = args.output or Path("review_report.csv")
    write_csv_report(all_metadata, output_csv)
    print(f"\nCSV report written to: {output_csv}")

    if args.json_output:
        write_json_report(all_metadata, args.json_output)
        print(f"JSON report written to: {args.json_output}")

    print(f"\nTemporary results saved in: {temp_dir}")
    print("  (Use --resume to continue from here, or --clear-cache to start fresh)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
