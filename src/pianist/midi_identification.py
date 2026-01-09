"""
Unified MIDI file identification module supporting both classical and modern works.

This module provides flexible identification that handles:
- Classical works: "J.S. Bach - Invention No. 1 BWV 772", "chopin-prelude-op28-no7"
- Modern works: "Hans Zimmer - Interstellar (Main Theme)", "what-was-i-made-for--billie-eilish"
- Film soundtracks, pop songs, contemporary compositions
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

# Composer definitions - supports both classical and modern composers
COMPOSER_DEFINITIONS: dict[str, dict[str, Any]] = {
    # Classical composers
    "J.S. Bach": {
        "canonical": "J.S. Bach",
        "full_names": ["johann sebastian bach", "j.s. bach"],
        "simple": ["bach"],
        "abbreviations": [],
    },
    "Beethoven": {
        "canonical": "Beethoven",
        "full_names": ["ludwig van beethoven"],
        "simple": ["beethoven"],
        "abbreviations": [],
    },
    "Mozart": {
        "canonical": "Mozart",
        "full_names": ["wolfgang amadeus mozart", "w.a. mozart"],
        "simple": ["mozart"],
        "abbreviations": [],
    },
    "Chopin": {
        "canonical": "Chopin",
        "full_names": ["frédéric chopin", "frederic chopin"],
        "simple": ["chopin"],
        "abbreviations": [],
    },
    # Modern composers and artists
    "Hans Zimmer": {
        "canonical": "Hans Zimmer",
        "full_names": ["hans zimmer"],
        "simple": ["zimmer"],
        "abbreviations": [],
    },
    "Billie Eilish": {
        "canonical": "Billie Eilish",
        "full_names": ["billie eilish"],
        "simple": ["eilish", "billie"],
        "abbreviations": [],
    },
    "Ludovico Einaudi": {
        "canonical": "Ludovico Einaudi",
        "full_names": ["ludovico einaudi"],
        "simple": ["einaudi"],
        "abbreviations": [],
    },
    "Yiruma": {
        "canonical": "Yiruma",
        "full_names": ["yiruma", "lee ru-ma"],
        "simple": ["yiruma"],
        "abbreviations": [],
    },
    "Max Richter": {
        "canonical": "Max Richter",
        "full_names": ["max richter"],
        "simple": ["richter"],
        "abbreviations": [],
    },
    # Additional classical composers
    "Alexander Scriabin": {
        "canonical": "Alexander Scriabin",
        "full_names": ["alexander scriabin"],
        "simple": ["scriabin"],
        "abbreviations": ["a. scriabin"],
    },
    "Claude Debussy": {
        "canonical": "Claude Debussy",
        "full_names": ["claude debussy"],
        "simple": ["debussy"],
        "abbreviations": ["c. debussy"],
    },
    "Rachmaninoff": {
        "canonical": "Rachmaninoff",
        "full_names": ["sergei rachmaninoff", "sergei rachmaninov"],
        "simple": ["rachmaninoff", "rachmaninov"],
        "abbreviations": [],
    },
    "Schubert": {
        "canonical": "Schubert",
        "full_names": ["franz schubert", "franz peter schubert"],
        "simple": ["schubert"],
        "abbreviations": [],
    },
    "Robert Schumann": {
        "canonical": "Robert Schumann",
        "full_names": ["robert schumann", "robert alexander schumann"],
        "simple": ["schumann"],
        "abbreviations": [],
    },
    "Liszt": {
        "canonical": "Liszt",
        "full_names": ["franz liszt"],
        "simple": ["liszt"],
        "abbreviations": [],
    },
    "Brahms": {
        "canonical": "Brahms",
        "full_names": ["johannes brahms"],
        "simple": ["brahms"],
        "abbreviations": [],
    },
    "Muzio Clementi": {
        "canonical": "Muzio Clementi",
        "full_names": ["muzio clementi"],
        "simple": ["clementi"],
        "abbreviations": [],
    },
    "Erik Satie": {
        "canonical": "Erik Satie",
        "full_names": ["erik satie"],
        "simple": ["satie"],
        "abbreviations": [],
    },
    "Felix Mendelssohn": {
        "canonical": "Felix Mendelssohn",
        "full_names": ["felix mendelssohn", "felix mendelssohn-bartholdy"],
        "simple": ["mendelssohn"],
        "abbreviations": [],
    },
    "George Frideric Handel": {
        "canonical": "George Frideric Handel",
        "full_names": ["george frideric handel", "g.f. handel"],
        "simple": ["handel"],
        "abbreviations": [],
    },
    "Domenico Scarlatti": {
        "canonical": "Domenico Scarlatti",
        "full_names": ["domenico scarlatti"],
        "simple": ["scarlatti"],
        "abbreviations": [],
    },
    "Joseph Haydn": {
        "canonical": "Joseph Haydn",
        "full_names": ["joseph haydn", "franz joseph haydn"],
        "simple": ["haydn"],
        "abbreviations": [],
    },
    "Alban Berg": {
        "canonical": "Alban Berg",
        "full_names": ["alban berg"],
        "simple": ["berg"],
        "abbreviations": [],
    },
}


# Build regex patterns from composer definitions
def _build_composer_patterns() -> dict[str, dict[str, Any]]:
    """Build regex patterns for composer matching."""
    patterns: dict[str, dict[str, Any]] = {}

    for composer, defs in COMPOSER_DEFINITIONS.items():
        # Full name patterns
        full_patterns = [re.escape(name) for name in defs.get("full_names", [])]
        # Simple patterns
        simple_patterns = [re.escape(name) for name in defs.get("simple", [])]
        # Abbreviation patterns
        abbrev_patterns = [re.escape(name) for name in defs.get("abbreviations", [])]

        # Combine all patterns
        all_patterns = full_patterns + simple_patterns + abbrev_patterns

        if all_patterns:
            # Create regex that matches any of the patterns
            pattern_str = "|".join(all_patterns)
            patterns[pattern_str] = {
                "composer": composer,
                "canonical": defs["canonical"],
            }

    return patterns


COMPOSER_PATTERNS = _build_composer_patterns()


@dataclass
class MidiIdentification:
    """Identified metadata from a MIDI filename."""

    composer: str | None = None
    title: str | None = None
    catalog_number: str | None = None  # BWV, Op., K., etc.
    opus: str | None = None
    movement: str | None = None
    artist: str | None = None  # For modern works (may be same as composer)
    album: str | None = None  # For modern works
    year: int | None = None
    is_classical: bool = True  # True for classical, False for modern
    confidence: float = 0.0  # 0.0-1.0 confidence in identification


def identify_from_filename(filename: str) -> MidiIdentification:
    """
    Identify MIDI file metadata from filename patterns.

    Supports both classical and modern naming conventions:
    - Classical: "J.S. Bach - Invention No. 1 BWV 772"
    - Classical: "chopin-prelude-op28-no7"
    - Modern: "Hans Zimmer - Interstellar (Main Theme)"
    - Modern: "what-was-i-made-for--billie-eilish"
    - Modern: "River Flows in You - Yiruma"

    Returns:
        MidiIdentification with extracted metadata
    """
    result = MidiIdentification()
    filename_lower = filename.lower()

    # Remove file extension
    base_name = re.sub(r"\.(mid|midi)$", "", filename, flags=re.IGNORECASE)

    # Strategy 1: "Composer - Title" format (classical and modern)
    dash_match = re.search(r"^([^-]+?)\s*-+\s*(.+?)$", base_name, re.IGNORECASE)
    if dash_match:
        composer_part = dash_match.group(1).strip()
        title_part = dash_match.group(2).strip()

        # Try to identify composer
        identified_composer = _identify_composer(composer_part)
        if identified_composer:
            result.composer = identified_composer
            result.title = _clean_title(title_part)
            result.is_classical = _is_classical_composer(identified_composer)

            # Extract catalog numbers for classical works
            if result.is_classical:
                _extract_classical_metadata(title_part, result)
            else:
                # For modern works, title might contain additional info
                _extract_modern_metadata(title_part, result)

            result.confidence = 0.8
            return result

    # Strategy 2: "Title -- Composer" format (common in modern works)
    double_dash_match = re.search(r"(.+?)\s*--\s*([^-]+?)$", base_name, re.IGNORECASE)
    if double_dash_match:
        title_part = double_dash_match.group(1).strip()
        composer_part = double_dash_match.group(2).strip()

        identified_composer = _identify_composer(composer_part)
        if identified_composer:
            result.composer = identified_composer
            result.title = _clean_title(title_part)
            result.is_classical = _is_classical_composer(identified_composer)
            result.confidence = 0.7
            return result

    # Strategy 3: Hyphenated/slug format (e.g., "what-was-i-made-for--billie-eilish")
    # Look for composer at the end
    slug_match = re.search(r"(.+?)[-_]+([a-z]+(?:[-_][a-z]+)*)$", base_name, re.IGNORECASE)
    if slug_match:
        title_part = slug_match.group(1).replace("-", " ").replace("_", " ")
        composer_part = slug_match.group(2).replace("-", " ").replace("_", " ")

        identified_composer = _identify_composer(composer_part)
        if identified_composer:
            result.composer = identified_composer
            result.title = _clean_title(title_part)
            result.is_classical = _is_classical_composer(identified_composer)
            result.confidence = 0.6
            return result

    # Strategy 4: Simple composer name in filename
    for pattern_info in COMPOSER_PATTERNS.values():
        pattern = pattern_info["composer"]
        if pattern.lower() in filename_lower:
            result.composer = pattern_info["canonical"]
            result.is_classical = _is_classical_composer(result.composer)

            # Try to extract title by removing composer name
            title_candidate = base_name
            for name_variant in COMPOSER_DEFINITIONS[result.composer].get(
                "full_names", []
            ) + COMPOSER_DEFINITIONS[result.composer].get("simple", []):
                title_candidate = re.sub(
                    re.escape(name_variant), "", title_candidate, flags=re.IGNORECASE
                )

            title_candidate = re.sub(r"[-_\s]+", " ", title_candidate).strip()
            if title_candidate and len(title_candidate) > 2:
                result.title = _clean_title(title_candidate)

            result.confidence = 0.5
            break

    # Extract catalog numbers even if composer not found
    _extract_classical_metadata(base_name, result)

    # If we have a title but no composer, might be a modern work
    if result.title and not result.composer:
        result.is_classical = False
        result.confidence = 0.3

    return result


def _identify_composer(text: str) -> str | None:
    """Identify composer from text using pattern matching."""
    text_lower = text.lower()

    # Check each composer definition
    for _composer, defs in COMPOSER_DEFINITIONS.items():
        # Check full names
        for full_name in defs.get("full_names", []):
            if full_name in text_lower:
                return defs["canonical"]

        # Check simple names
        for simple_name in defs.get("simple", []):
            if simple_name in text_lower:
                return defs["canonical"]

        # Check abbreviations
        for abbrev in defs.get("abbreviations", []):
            if abbrev in text_lower:
                return defs["canonical"]

    return None


def _is_classical_composer(composer: str) -> bool:
    """Determine if composer is classical or modern."""
    # Modern composers/artists (explicit list)
    modern_composers = {
        "Hans Zimmer",
        "Billie Eilish",
        "Ludovico Einaudi",
        "Yiruma",
        "Max Richter",
    }
    # Everything else is assumed classical (can be refined later)
    # This includes all composers in COMPOSER_DEFINITIONS that aren't in modern_composers
    return composer not in modern_composers


def _extract_classical_metadata(text: str, result: MidiIdentification) -> None:
    """Extract classical metadata (BWV, Op., K., etc.) from text."""
    text_lower = text.lower()

    # BWV (Bach)
    bwv_match = re.search(r"bwv[.\s-]*(\d+)", text_lower)
    if bwv_match:
        result.catalog_number = f"BWV {bwv_match.group(1)}"
        if not result.composer:
            result.composer = "J.S. Bach"

    # Opus numbers
    opus_match = re.search(r"op[.\s-]*(\d+)(?:\s*no[.\s-]*(\d+))?", text_lower)
    if opus_match:
        opus_num = opus_match.group(1)
        no_num = opus_match.group(2)
        if no_num:
            result.opus = f"Op. {opus_num} No. {no_num}"
        else:
            result.opus = f"Op. {opus_num}"
        if not result.catalog_number:
            result.catalog_number = result.opus

    # Köchel (Mozart)
    k_match = re.search(r"\bk[.\s-]*(\d+)", text_lower)
    if k_match:
        result.catalog_number = f"K. {k_match.group(1)}"
        if not result.composer:
            result.composer = "Mozart"

    # Hoboken (Haydn)
    hob_match = re.search(r"hob[.\s-]*(\d+)(?:\s*:\s*(\d+))?", text_lower)
    if hob_match:
        result.catalog_number = f"Hob. {hob_match.group(1)}"
        if hob_match.group(2):
            result.catalog_number += f":{hob_match.group(2)}"
        if not result.composer:
            result.composer = "Joseph Haydn"


def _extract_modern_metadata(text: str, result: MidiIdentification) -> None:
    """Extract modern work metadata (album, year, etc.) from text."""
    # Look for album in parentheses
    album_match = re.search(r"\(([^)]+)\)", text)
    if album_match:
        album_text = album_match.group(1)
        # Check if it's an album name (not "Main Theme" or similar)
        if "theme" not in album_text.lower() and "main" not in album_text.lower():
            result.album = album_text

    # Look for year
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    if year_match:
        with contextlib.suppress(ValueError):
            result.year = int(year_match.group(0))


def _clean_title(title: str) -> str:
    """Clean and format title string."""
    # Remove extra whitespace
    title = re.sub(r"\s+", " ", title).strip()

    # Capitalize properly (title case)
    words = title.split()
    capitalized = []
    for word in words:
        # Don't capitalize small words unless first word
        if word.lower() in ["a", "an", "the", "of", "in", "on", "at", "to", "for"] and capitalized:
            capitalized.append(word.lower())
        else:
            capitalized.append(word.capitalize())

    return " ".join(capitalized)


def identify_from_metadata_json(file_path: Path) -> MidiIdentification | None:
    """
    Load identification from companion JSON metadata file.

    Looks for filename.mid.json alongside the MIDI file.

    Returns:
        MidiIdentification if JSON file exists and is valid, None otherwise
    """
    json_path = file_path.with_suffix(file_path.suffix + ".json")

    if not json_path.exists():
        return None

    try:
        import json

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        result = MidiIdentification()
        result.composer = data.get("composer")
        result.title = data.get("title")
        result.catalog_number = data.get("catalog_number") or data.get("opus")
        result.opus = data.get("opus")
        result.movement = data.get("movement")
        result.artist = data.get("artist")  # For modern works
        result.album = data.get("album")
        result.year = data.get("year")
        result.is_classical = data.get("is_classical", True)
        result.confidence = 1.0  # JSON metadata is authoritative

        return result
    except Exception:
        return None


def identify_from_directory(file_path: Path) -> MidiIdentification | None:
    """
    Extract composer/artist from parent directory name.

    Example: references/Hans Zimmer/interstellar.mid -> composer: "Hans Zimmer"

    Returns:
        MidiIdentification with composer extracted from directory, None if not found
    """
    parent_dir = file_path.parent.name

    # Skip common non-composer directory names
    skip_dirs = {"references", "input", "output", "midi", "music", "classical", "modern"}
    if parent_dir.lower() in skip_dirs:
        return None

    identified_composer = _identify_composer(parent_dir)
    if identified_composer:
        result = MidiIdentification()
        result.composer = identified_composer
        result.is_classical = _is_classical_composer(identified_composer)
        result.confidence = 0.6
        return result

    return None


def identify_midi_file(
    file_path: Path,
    use_json: bool = True,
    use_directory: bool = True,
    use_filename: bool = True,
) -> MidiIdentification:
    """
    Comprehensive MIDI file identification using multiple strategies.

    Priority order:
    1. Metadata JSON file (filename.mid.json) - highest priority
    2. Directory structure (parent directory name)
    3. Filename parsing

    Args:
        file_path: Path to MIDI file
        use_json: Check for companion JSON metadata file
        use_directory: Extract composer from directory structure
        use_filename: Parse filename for metadata

    Returns:
        MidiIdentification with best available metadata
    """
    # Strategy 1: JSON metadata (highest priority)
    if use_json:
        json_result = identify_from_metadata_json(file_path)
        if json_result:
            return json_result

    # Strategy 2: Directory structure
    if use_directory:
        dir_result = identify_from_directory(file_path)
        if dir_result:
            # Try to enhance with filename parsing
            filename_result = identify_from_filename(file_path.name)
            if filename_result.title:
                dir_result.title = filename_result.title
                dir_result.catalog_number = filename_result.catalog_number
                dir_result.opus = filename_result.opus
                dir_result.movement = filename_result.movement
                dir_result.confidence = max(dir_result.confidence, filename_result.confidence)
            return dir_result

    # Strategy 3: Filename parsing
    if use_filename:
        return identify_from_filename(file_path.name)

    # Fallback: empty identification
    return MidiIdentification()
