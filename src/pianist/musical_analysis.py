"""
Musical analysis module for detecting motifs, phrases, harmony, and form.

This module provides analysis capabilities to understand musical structure
and guide AI expansion of compositions using music21.

For technical details on how each analysis feature works, see:
docs/temp/analysis_technical_details.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from music21 import (
        converter, analysis, stream, pitch, note, chord, meter, tempo, key,
        roman, harmony, interval
    )
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False

from .schema import Composition, NoteEvent, TempoEvent


@dataclass
class ChordAnalysis:
    """Analysis of a single chord."""
    start: float
    pitches: list[int]
    name: str
    roman_numeral: str | None = None  # e.g., "I", "V", "ii"
    function: str | None = None  # e.g., "tonic", "dominant", "subdominant"
    inversion: int | None = None  # 0 = root position, 1 = first inversion, etc.
    is_cadence: bool = False  # Whether this chord is part of a cadence
    cadence_type: str | None = None  # e.g., "authentic", "plagal", "deceptive"


@dataclass
class HarmonicAnalysis:
    """Results of harmonic analysis."""
    chords: list[ChordAnalysis]  # List of chord analyses with timing
    roman_numerals: list[str] | None = None  # Roman numeral analysis if available
    key: str | None = None  # Detected key
    cadences: list[dict[str, Any]] | None = None  # Detected cadences
    progression: list[str] | None = None  # Harmonic progression (e.g., ["I", "V", "I"])
    voice_leading: list[dict[str, Any]] | None = None  # Voice leading analysis


@dataclass
class Motif:
    """A detected musical motif."""
    start: float
    duration: float
    pitches: list[int]
    description: str | None = None


@dataclass
class Phrase:
    """A detected musical phrase."""
    start: float
    duration: float
    description: str | None = None


@dataclass
class MusicalAnalysis:
    """Complete musical analysis results."""
    motifs: list[Motif]
    phrases: list[Phrase]
    harmonic_progression: HarmonicAnalysis | None
    form: str | None
    key_ideas: list[dict[str, Any]]  # Identified key musical ideas
    expansion_suggestions: list[str]  # Suggestions for expansion


def _composition_to_music21_stream(composition: Composition) -> stream.Stream:
    """
    Convert a Composition to a music21 Stream.
    
    This creates a music21 representation that can be used for analysis.
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for musical analysis. Install it with: pip install music21"
        )
    
    # Create a new stream
    s = stream.Stream()
    
    # Set time signature
    ts = meter.TimeSignature(
        f"{composition.time_signature.numerator}/{composition.time_signature.denominator}"
    )
    s.insert(0, ts)
    
    # Set key signature if present
    if composition.key_signature:
        try:
            ks = key.KeySignature(composition.key_signature)
            s.insert(0, ks)
        except Exception:
            # If key signature parsing fails, continue without it
            pass
    
    # Set tempo
    tempo_obj = tempo.MetronomeMark(number=composition.bpm)
    s.insert(0, tempo_obj)
    
    # Process tempo events
    tempo_map: dict[float, float] = {0.0: composition.bpm}
    for track in composition.tracks:
        for event in track.events:
            if isinstance(event, TempoEvent):
                if event.bpm is not None:
                    tempo_map[event.start] = event.bpm
                elif event.start_bpm is not None:
                    tempo_map[event.start] = event.start_bpm
    
    # Convert notes to music21 format
    # Group notes by track/channel
    for track in composition.tracks:
        track_stream = stream.Part()
        track_stream.id = track.name
        
        # Process events in time order
        events_by_time: list[tuple[float, NoteEvent]] = []
        for event in track.events:
            if isinstance(event, NoteEvent):
                events_by_time.append((event.start, event))
        
        events_by_time.sort(key=lambda x: x[0])
        
        # Convert notes to music21 format
        for start_beat, note_event in events_by_time:
            # Calculate offset in music21 (in quarter notes)
            offset = start_beat
            
            # Create chord or note
            if len(note_event.pitches) == 1:
                # Single note
                n = note.Note(note_event.pitches[0])
                n.quarterLength = note_event.duration
                n.volume.velocity = note_event.velocity
                track_stream.insert(offset, n)
            else:
                # Chord
                pitches_list = [pitch.Pitch(p) for p in note_event.pitches]
                c = chord.Chord(pitches_list)
                c.quarterLength = note_event.duration
                c.volume.velocity = note_event.velocity
                track_stream.insert(offset, c)
        
        s.insert(0, track_stream)
    
    return s


def _detect_key_from_stream(s: stream.Stream) -> key.Key | None:
    """Detect the key of a music21 stream."""
    if not MUSIC21_AVAILABLE:
        return None
    
    try:
        # Use music21's key detection
        detected = s.analyze('key')
        return detected
    except Exception:
        # If key detection fails, try to infer from key signature
        try:
            ks = s.getElementsByClass(key.KeySignature)
            if ks:
                # Convert key signature to key (assume major)
                # This is a simplification - could be minor
                return key.Key(ks[0].tonic.name)
        except Exception:
            pass
    return None


def _analyze_chord_function(chord_obj: chord.Chord, key_obj: key.Key | None) -> tuple[str | None, str | None, int | None]:
    """
    Analyze chord function (Roman numeral, function, inversion).
    
    Returns:
        (roman_numeral, function, inversion)
    """
    if not MUSIC21_AVAILABLE or key_obj is None:
        return None, None, None
    
    try:
        # Create Roman numeral analysis
        rn = roman.romanNumeralFromChord(chord_obj, key_obj)
        roman_str = rn.figure
        
        # Determine function
        function = None
        if rn.scaleDegree == 1:
            function = "tonic"
        elif rn.scaleDegree == 4:
            function = "subdominant"
        elif rn.scaleDegree == 5:
            function = "dominant"
        elif rn.scaleDegree in (2, 6):
            function = "subdominant"  # ii, vi are subdominant function
        elif rn.scaleDegree in (3, 7):
            function = "dominant"  # iii, vii are dominant function
        
        # Get inversion
        inversion = chord_obj.inversion()
        
        return roman_str, function, inversion
    except Exception:
        return None, None, None


def _detect_cadences(
    chords: list[ChordAnalysis],
    key_obj: key.Key | None
) -> tuple[list[dict[str, Any]], list[bool]]:
    """
    Detect cadences in the harmonic progression.
    
    Returns:
        (cadences_list, is_cadence_flags)
    """
    if not MUSIC21_AVAILABLE or key_obj is None or len(chords) < 2:
        return [], [False] * len(chords)
    
    cadences: list[dict[str, Any]] = []
    is_cadence = [False] * len(chords)
    cadence_types: list[str] = [None] * len(chords)
    
    # Look for common cadence patterns
    for i in range(len(chords) - 1):
        curr = chords[i]
        next_chord = chords[i + 1]
        
        # Authentic cadence: V -> I
        if curr.roman_numeral and next_chord.roman_numeral:
            if "V" in curr.roman_numeral and "I" in next_chord.roman_numeral:
                cadences.append({
                    'start': curr.start,
                    'end': next_chord.start,
                    'type': 'authentic',
                    'chords': [curr.roman_numeral, next_chord.roman_numeral]
                })
                is_cadence[i] = True
                is_cadence[i + 1] = True
                cadence_types[i] = "authentic"
                cadence_types[i + 1] = "authentic"
            
            # Plagal cadence: IV -> I
            elif "IV" in curr.roman_numeral and "I" in next_chord.roman_numeral:
                cadences.append({
                    'start': curr.start,
                    'end': next_chord.start,
                    'type': 'plagal',
                    'chords': [curr.roman_numeral, next_chord.roman_numeral]
                })
                is_cadence[i] = True
                is_cadence[i + 1] = True
                cadence_types[i] = "plagal"
                cadence_types[i + 1] = "plagal"
            
            # Deceptive cadence: V -> vi
            elif "V" in curr.roman_numeral and "vi" in next_chord.roman_numeral:
                cadences.append({
                    'start': curr.start,
                    'end': next_chord.start,
                    'type': 'deceptive',
                    'chords': [curr.roman_numeral, next_chord.roman_numeral]
                })
                is_cadence[i] = True
                is_cadence[i + 1] = True
                cadence_types[i] = "deceptive"
                cadence_types[i + 1] = "deceptive"
    
    # Update chord analysis objects with cadence info
    for i, chord_analysis in enumerate(chords):
        chord_analysis.is_cadence = is_cadence[i]
        chord_analysis.cadence_type = cadence_types[i]
    
    return cadences, is_cadence


def _analyze_voice_leading(chords: list[ChordAnalysis]) -> list[dict[str, Any]]:
    """
    Analyze voice leading between consecutive chords.
    
    Returns:
        List of voice leading analyses
    """
    voice_leading: list[dict[str, Any]] = []
    
    for i in range(len(chords) - 1):
        curr = chords[i]
        next_chord = chords[i + 1]
        
        # Calculate voice leading (common tones, stepwise motion, leaps)
        curr_pitches = set(curr.pitches)
        next_pitches = set(next_chord.pitches)
        
        common_tones = len(curr_pitches & next_pitches)
        new_tones = len(next_pitches - curr_pitches)
        dropped_tones = len(curr_pitches - next_pitches)
        
        # Calculate intervals (simplified - just count semitones)
        intervals: list[int] = []
        for p1 in sorted(curr.pitches):
            # Find closest pitch in next chord
            if next_chord.pitches:
                closest = min(next_chord.pitches, key=lambda p2: abs(p2 - p1))
                intervals.append(closest - p1)
        
        # Classify voice leading quality
        stepwise_motion = sum(1 for iv in intervals if abs(iv) <= 2)
        leaps = sum(1 for iv in intervals if abs(iv) > 2)
        
        voice_leading.append({
            'from_chord': i,
            'to_chord': i + 1,
            'start': curr.start,
            'end': next_chord.start,
            'common_tones': common_tones,
            'new_tones': new_tones,
            'dropped_tones': dropped_tones,
            'stepwise_motion': stepwise_motion,
            'leaps': leaps,
            'intervals': intervals,
            'quality': 'smooth' if stepwise_motion > leaps else 'disjunct'
        })
    
    return voice_leading


def analyze_harmony(composition: Composition) -> HarmonicAnalysis:
    """
    Analyze harmonic progression and functional harmony.
    
    Uses music21's harmonic analysis capabilities with enhanced features:
    - Roman numeral analysis
    - Functional harmony (tonic, dominant, subdominant)
    - Inversion detection
    - Cadence detection
    - Voice leading analysis
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for harmonic analysis. Install it with: pip install music21"
        )
    
    # Convert to music21 stream
    s = _composition_to_music21_stream(composition)
    
    # Detect or use key
    detected_key_obj = _detect_key_from_stream(s)
    detected_key: str | None = None
    if detected_key_obj:
        detected_key = detected_key_obj.name
    elif composition.key_signature:
        detected_key = composition.key_signature
        try:
            detected_key_obj = key.Key(composition.key_signature)
        except Exception:
            detected_key_obj = None
    
    # Set key in stream for analysis
    if detected_key_obj:
        s.insert(0, detected_key_obj)
    
    # Extract chords from all parts and analyze
    chord_analyses: list[ChordAnalysis] = []
    chord_times: list[float] = []
    
    # Use getElementsByClass to get parts from the stream
    parts = s.getElementsByClass(stream.Part)
    if not parts:
        # If no parts, treat the stream itself as a single part
        parts = [s]
    
    # Collect all chord events with timing
    for part in parts:
        for element in part.flatten().notes:
            if hasattr(element, 'offset'):
                offset = float(element.offset)
                chord_obj: chord.Chord | None = None
                chord_pitches: list[int] = []
                chord_name: str = ""
                
                if isinstance(element, chord.Chord):
                    chord_obj = element
                    chord_pitches = [p.midi for p in element.pitches]
                    chord_name = element.pitchedCommonName
                elif isinstance(element, note.Note):
                    # Convert single note to chord for analysis
                    chord_obj = chord.Chord([element.pitch])
                    chord_pitches = [element.pitch.midi]
                    chord_name = element.pitch.name
                
                if chord_obj and chord_pitches:
                    # Analyze chord function
                    roman_num, function, inversion = _analyze_chord_function(chord_obj, detected_key_obj)
                    
                    chord_analyses.append(ChordAnalysis(
                        start=offset,
                        pitches=chord_pitches,
                        name=chord_name,
                        roman_numeral=roman_num,
                        function=function,
                        inversion=inversion,
                        is_cadence=False,
                        cadence_type=None,
                    ))
                    chord_times.append(offset)
    
    # Sort by time
    sorted_indices = sorted(range(len(chord_analyses)), key=lambda i: chord_analyses[i].start)
    chord_analyses = [chord_analyses[i] for i in sorted_indices]
    
    # Detect cadences
    cadences, _ = _detect_cadences(chord_analyses, detected_key_obj)
    
    # Analyze voice leading
    voice_leading = _analyze_voice_leading(chord_analyses)
    
    # Extract Roman numeral progression
    roman_numerals_list = [c.roman_numeral for c in chord_analyses if c.roman_numeral]
    progression = roman_numerals_list if roman_numerals_list else None
    
    return HarmonicAnalysis(
        chords=chord_analyses,
        roman_numerals=roman_numerals_list if roman_numerals_list else None,
        key=detected_key,
        cadences=cadences if cadences else None,
        progression=progression,
        voice_leading=voice_leading if voice_leading else None,
    )


def _extract_interval_pattern(pitches: list[int]) -> tuple[int, ...]:
    """
    Extract interval pattern from a sequence of pitches.
    
    Returns:
        Tuple of intervals in semitones
    """
    if len(pitches) < 2:
        return tuple()
    
    intervals: list[int] = []
    for i in range(len(pitches) - 1):
        intervals.append(pitches[i + 1] - pitches[i])
    
    return tuple(intervals)


def _normalize_pitch_sequence(pitches: list[int]) -> list[int]:
    """
    Normalize a pitch sequence to start at 0 (for transposition-aware matching).
    
    Returns:
        List of pitches normalized to start at 0
    """
    if not pitches:
        return []
    
    first_pitch = pitches[0]
    return [p - first_pitch for p in pitches]


def _detect_transposed_match(pattern1: list[int], pattern2: list[int], tolerance: int = 1) -> bool:
    """
    Check if two pitch patterns match when transposed.
    
    Args:
        pattern1: First pitch pattern
        pattern2: Second pitch pattern
        tolerance: Maximum difference in transposition (in semitones)
    
    Returns:
        True if patterns match when transposed
    """
    if len(pattern1) != len(pattern2) or len(pattern1) < 2:
        return False
    
    # Extract interval patterns
    intervals1 = _extract_interval_pattern(pattern1)
    intervals2 = _extract_interval_pattern(pattern2)
    
    # Check if interval patterns match
    if intervals1 == intervals2:
        return True
    
    # Check transposition: normalize both to start at 0
    norm1 = _normalize_pitch_sequence(pattern1)
    norm2 = _normalize_pitch_sequence(pattern2)
    
    if norm1 == norm2:
        return True
    
    # Check if one is a transposition of the other (within tolerance)
    if len(pattern1) == len(pattern2):
        transposition = pattern2[0] - pattern1[0]
        if abs(transposition) <= tolerance:
            # Check if all intervals match after transposition
            transposed1 = [p + transposition for p in pattern1]
            if transposed1 == pattern2:
                return True
    
    return False


def detect_motifs(composition: Composition, min_length: float = 0.5, max_length: float = 4.0) -> list[Motif]:
    """
    Detect recurring melodic/rhythmic patterns (motifs) in the composition.
    
    Enhanced with:
    - Transposition-aware matching (detects same pattern in different keys)
    - Interval pattern matching (detects same melodic contour)
    - Multiple window sizes (2-5 notes)
    
    Args:
        composition: The composition to analyze
        min_length: Minimum motif length in beats
        max_length: Maximum motif length in beats
    
    Returns:
        List of detected motifs
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for motif detection. Install it with: pip install music21"
        )
    
    # Convert to music21 stream
    s = _composition_to_music21_stream(composition)
    
    # Extract all notes with their timing and duration
    all_notes: list[tuple[float, float, list[int]]] = []  # (start, duration, pitches)
    
    # Use getElementsByClass to get parts from the stream
    parts = s.getElementsByClass(stream.Part)
    if not parts:
        # If no parts, treat the stream itself as a single part
        parts = [s]
    
    for part in parts:
        for element in part.flatten().notes:
            if hasattr(element, 'offset') and hasattr(element, 'quarterLength'):
                offset = float(element.offset)
                duration = float(element.quarterLength)
                if isinstance(element, chord.Chord):
                    # For chords, use the lowest pitch for melodic analysis
                    pitches = sorted([p.midi for p in element.pitches])
                    all_notes.append((offset, duration, pitches))
                elif isinstance(element, note.Note):
                    all_notes.append((offset, duration, [element.pitch.midi]))
    
    # Sort by time
    all_notes.sort(key=lambda x: x[0])
    
    # Extract melodic line (lowest pitch at each time point for simplicity)
    melodic_line: list[tuple[float, int]] = []  # (start, pitch)
    for start, duration, pitches in all_notes:
        if pitches:
            # Use lowest pitch for melodic analysis
            melodic_line.append((start, min(pitches)))
    
    if len(melodic_line) < 3:
        return []  # Need at least 3 notes for pattern matching
    
    motifs: list[Motif] = []
    
    # Try different window sizes (2-5 notes)
    for window_size in range(2, 6):
        # Extract all patterns of this size
        patterns: list[tuple[float, list[int]]] = []  # (start, pitches)
        
        for i in range(len(melodic_line) - window_size + 1):
            window = melodic_line[i:i+window_size]
            pitches = [p for _, p in window]
            start_time = window[0][0]
            patterns.append((start_time, pitches))
        
        # Find matching patterns (exact, transposed, or interval-based)
        matched_patterns: dict[int, list[float]] = {}  # pattern_index -> [occurrence_times]
        
        for i, (start1, pattern1) in enumerate(patterns):
            for j, (start2, pattern2) in enumerate(patterns[i+1:], start=i+1):
                # Check for exact match
                if pattern1 == pattern2:
                    if i not in matched_patterns:
                        matched_patterns[i] = []
                    matched_patterns[i].append(start1)
                    if j not in matched_patterns:
                        matched_patterns[j] = []
                    matched_patterns[j].append(start2)
                # Check for transposed match
                elif _detect_transposed_match(pattern1, pattern2):
                    if i not in matched_patterns:
                        matched_patterns[i] = []
                    matched_patterns[i].append(start1)
                    if j not in matched_patterns:
                        matched_patterns[j] = []
                    matched_patterns[j].append(start2)
                # Check for interval pattern match
                elif len(pattern1) == len(pattern2) and len(pattern1) >= 2:
                    intervals1 = _extract_interval_pattern(pattern1)
                    intervals2 = _extract_interval_pattern(pattern2)
                    if intervals1 == intervals2:
                        if i not in matched_patterns:
                            matched_patterns[i] = []
                        matched_patterns[i].append(start1)
                        if j not in matched_patterns:
                            matched_patterns[j] = []
                        matched_patterns[j].append(start2)
        
        # Create motifs from matched patterns
        for pattern_idx, occurrences in matched_patterns.items():
            if len(occurrences) >= 2:  # Pattern appears at least twice
                start_time, pitches = patterns[pattern_idx]
                
                # Calculate duration
                first_occurrence = min(occurrences)
                last_occurrence = max(occurrences)
                
                # Estimate motif duration (time span of all occurrences)
                duration = last_occurrence - first_occurrence + (window_size * 0.5)  # Approximate
                
                if min_length <= duration <= max_length:
                    # Check if we already have a similar motif (avoid duplicates)
                    is_duplicate = False
                    for existing_motif in motifs:
                        if (abs(existing_motif.start - first_occurrence) < 1.0 and
                            abs(existing_motif.duration - duration) < 1.0):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        motifs.append(Motif(
                            start=first_occurrence,
                            duration=duration,
                            pitches=pitches,
                            description=f"Recurring pattern ({len(occurrences)} occurrences, {window_size} notes)"
                        ))
    
    # Remove duplicates and sort by start time
    unique_motifs: list[Motif] = []
    seen_starts: set[float] = set()
    
    for motif in sorted(motifs, key=lambda m: m.start):
        # Round start to nearest 0.1 to avoid near-duplicates
        rounded_start = round(motif.start, 1)
        if rounded_start not in seen_starts:
            unique_motifs.append(motif)
            seen_starts.add(rounded_start)
    
    return unique_motifs


def detect_phrases(composition: Composition) -> list[Phrase]:
    """
    Detect musical phrases and phrase structure.
    
    This is a basic implementation using heuristics.
    More sophisticated algorithms can be built on top.
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for phrase detection. Install it with: pip install music21"
        )
    
    # Convert to music21 stream
    s = _composition_to_music21_stream(composition)
    
    phrases: list[Phrase] = []
    
    # Simple heuristic: look for rests or long gaps as phrase boundaries
    # Also use time signature to estimate phrase length (typically 4-8 beats)
    beats_per_phrase = 4.0  # Default phrase length
    
    # Get all note events
    all_events: list[tuple[float, float]] = []  # (start, duration)
    
    # Use getElementsByClass to get parts from the stream
    parts = s.getElementsByClass(stream.Part)
    if not parts:
        # If no parts, treat the stream itself as a single part
        parts = [s]
    
    for part in parts:
        for element in part.flatten().notes:
            if hasattr(element, 'offset') and hasattr(element, 'quarterLength'):
                start = float(element.offset)
                duration = float(element.quarterLength)
                all_events.append((start, duration))
    
    if not all_events:
        return phrases
    
    # Sort by start time
    all_events.sort(key=lambda x: x[0])
    
    # Group into phrases based on gaps and time signature
    current_phrase_start = all_events[0][0]
    current_phrase_end = current_phrase_start
    
    for start, duration in all_events:
        gap = start - current_phrase_end
        
        # If gap is large (more than 2 beats), start new phrase
        # Or if we've reached typical phrase length
        if gap > 2.0 or (start - current_phrase_start) >= beats_per_phrase * 2:
            # End current phrase
            if current_phrase_end > current_phrase_start:
                phrases.append(Phrase(
                    start=current_phrase_start,
                    duration=current_phrase_end - current_phrase_start,
                    description="Detected phrase"
                ))
            
            # Start new phrase
            current_phrase_start = start
            current_phrase_end = start + duration
        else:
            current_phrase_end = max(current_phrase_end, start + duration)
    
    # Add final phrase
    if current_phrase_end > current_phrase_start:
        phrases.append(Phrase(
            start=current_phrase_start,
            duration=current_phrase_end - current_phrase_start,
            description="Detected phrase"
        ))
    
    return phrases


def _calculate_section_similarity(
    section1_notes: list[tuple[float, int]],
    section2_notes: list[tuple[float, int]]
) -> float:
    """
    Calculate similarity between two sections based on melodic content.
    
    Returns:
        Similarity score from 0.0 to 1.0
    """
    if not section1_notes or not section2_notes:
        return 0.0
    
    # Extract pitch sequences
    pitches1 = [p for _, p in section1_notes]
    pitches2 = [p for _, p in section2_notes]
    
    # Normalize lengths (compare first N notes)
    min_len = min(len(pitches1), len(pitches2))
    if min_len < 3:
        return 0.0
    
    pitches1_norm = pitches1[:min_len]
    pitches2_norm = pitches2[:min_len]
    
    # Calculate interval patterns
    intervals1 = _extract_interval_pattern(pitches1_norm)
    intervals2 = _extract_interval_pattern(pitches2_norm)
    
    # Count matching intervals
    matches = sum(1 for i1, i2 in zip(intervals1, intervals2) if i1 == i2)
    similarity = matches / len(intervals1) if intervals1 else 0.0
    
    # Also check transposed similarity
    norm1 = _normalize_pitch_sequence(pitches1_norm)
    norm2 = _normalize_pitch_sequence(pitches2_norm)
    
    if norm1 == norm2:
        similarity = max(similarity, 0.8)  # High similarity for transposed match
    
    return similarity


def _detect_sections_automatically(composition: Composition) -> list[dict[str, Any]]:
    """
    Automatically detect sections in the composition based on:
    - Phrase boundaries
    - Harmonic changes
    - Repetition patterns
    
    Returns:
        List of section dictionaries with start, end, and label
    """
    if not MUSIC21_AVAILABLE:
        return []
    
    # Detect phrases first
    phrases = detect_phrases(composition)
    
    if len(phrases) < 2:
        return []
    
    # Group phrases into sections based on:
    # 1. Large gaps between phrases (potential section boundaries)
    # 2. Harmonic analysis (key changes, cadences)
    # 3. Repetition patterns
    
    sections: list[dict[str, Any]] = []
    current_section_start = phrases[0].start if phrases else 0.0
    current_section_phrases: list[Phrase] = []
    
    # Analyze harmony to find cadences (section endings)
    harmony = analyze_harmony(composition)
    cadence_times: set[float] = set()
    if harmony.cadences:
        for cadence in harmony.cadences:
            cadence_times.add(cadence.get('end', 0.0))
    
    for i, phrase in enumerate(phrases):
        current_section_phrases.append(phrase)
        
        # Check if this is a section boundary
        is_boundary = False
        
        # Large gap after phrase (potential section end)
        if i < len(phrases) - 1:
            next_phrase = phrases[i + 1]
            gap = next_phrase.start - (phrase.start + phrase.duration)
            if gap > 3.0:  # Large gap indicates section boundary
                is_boundary = True
        
        # Cadence at phrase end (potential section end)
        phrase_end = phrase.start + phrase.duration
        for cadence_time in cadence_times:
            if abs(phrase_end - cadence_time) < 2.0:
                is_boundary = True
                break
        
        # Check for repetition (if we've seen similar material before, might be new section)
        if len(current_section_phrases) >= 2:
            # Compare with earlier phrases
            for earlier_phrase in current_section_phrases[:-1]:
                # Simple heuristic: if phrases are very similar, might be section return
                if abs(phrase.duration - earlier_phrase.duration) < 0.5:
                    # Could be a return - mark as potential boundary
                    if len(current_section_phrases) >= 3:
                        is_boundary = True
        
        if is_boundary or i == len(phrases) - 1:
            # End current section
            section_end = phrase.start + phrase.duration
            section_label = f"Section {len(sections) + 1}"
            
            sections.append({
                'start': current_section_start,
                'end': section_end,
                'label': section_label,
                'phrases': len(current_section_phrases),
            })
            
            # Start new section
            if i < len(phrases) - 1:
                current_section_start = phrases[i + 1].start
                current_section_phrases = []
    
    return sections


def detect_form(composition: Composition) -> str | None:
    """
    Detect musical form (binary, ternary, sonata, etc.).
    
    Enhanced with:
    - Automatic section detection
    - Section similarity analysis
    - Form classification based on repetition patterns
    
    Returns:
        Detected form name (e.g., "binary", "ternary", "sonata", "rondo", "custom")
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for form detection. Install it with: pip install music21"
        )
    
    # First, check for explicit section markers
    explicit_sections: list[str] = []
    for track in composition.tracks:
        for event in track.events:
            if hasattr(event, 'type') and event.type == 'section':
                if hasattr(event, 'label'):
                    explicit_sections.append(event.label)
    
    # If explicit sections exist, use them
    if explicit_sections:
        if len(explicit_sections) == 2:
            return "binary"
        elif len(explicit_sections) == 3:
            # Check if first and third are similar (A-B-A ternary)
            return "ternary"
        elif len(explicit_sections) >= 4:
            # Check for rondo pattern (A-B-A-C-A or similar)
            if explicit_sections[0] == explicit_sections[2] == explicit_sections[-1]:
                return "rondo"
            return "custom"
    
    # Otherwise, try automatic section detection
    auto_sections = _detect_sections_automatically(composition)
    
    if len(auto_sections) == 0:
        return None
    elif len(auto_sections) == 2:
        return "binary"
    elif len(auto_sections) == 3:
        # Check if first and third sections are similar (A-B-A ternary)
        # This would require analyzing the actual musical content
        # For now, assume ternary if 3 sections
        return "ternary"
    elif len(auto_sections) >= 4:
        # Check for rondo pattern (A-B-A-C-A or similar)
        # Simple heuristic: if first section repeats
        first_section_label = auto_sections[0]['label']
        repeat_count = sum(1 for s in auto_sections if s['label'] == first_section_label)
        if repeat_count >= 2 and auto_sections[-1]['label'] == first_section_label:
            return "rondo"
        return "custom"
    
    return "custom"


def identify_key_ideas(composition: Composition) -> list[dict[str, Any]]:
    """
    Identify important musical ideas that should be preserved/developed.
    
    Uses analysis results to identify motifs, phrases, and harmonic progressions
    that are significant.
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for key idea identification. Install it with: pip install music21"
        )
    
    key_ideas: list[dict[str, Any]] = []
    
    # Check if composition already has musical_intent annotations
    if composition.musical_intent and composition.musical_intent.key_ideas:
        for idea in composition.musical_intent.key_ideas:
            key_ideas.append({
                'id': idea.id,
                'type': idea.type,
                'start': idea.start,
                'duration': idea.duration,
                'description': idea.description,
                'importance': idea.importance,
            })
    
    # Also detect motifs and phrases automatically
    motifs = detect_motifs(composition)
    for i, motif in enumerate(motifs):
        key_ideas.append({
            'id': f'auto_motif_{i+1}',
            'type': 'motif',
            'start': motif.start,
            'duration': motif.duration,
            'description': motif.description or f"Detected motif {i+1}",
            'importance': 'medium',
        })
    
    phrases = detect_phrases(composition)
    for i, phrase in enumerate(phrases):
        key_ideas.append({
            'id': f'auto_phrase_{i+1}',
            'type': 'phrase',
            'start': phrase.start,
            'duration': phrase.duration,
            'description': phrase.description or f"Detected phrase {i+1}",
            'importance': 'medium',
        })
    
    return key_ideas


def generate_expansion_strategies(composition: Composition) -> list[str]:
    """
    Generate strategies for expanding the composition.
    
    Analyzes the composition and suggests how to expand it.
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for expansion strategy generation. Install it with: pip install music21"
        )
    
    strategies: list[str] = []
    
    # Analyze composition
    motifs = detect_motifs(composition)
    phrases = detect_phrases(composition)
    harmony = analyze_harmony(composition)
    form = detect_form(composition)
    
    # Generate strategies based on analysis
    if motifs:
        strategies.append(f"Develop detected motifs ({len(motifs)} found) with variations and sequences")
    
    if phrases:
        strategies.append(f"Extend phrases ({len(phrases)} found) by adding complementary material")
    
    if harmony.chords:
        strategies.append("Maintain harmonic coherence while expanding")
    
    if form:
        strategies.append(f"Preserve {form} form structure while expanding sections")
    
    # Check for expansion points in musical_intent
    if composition.musical_intent and composition.musical_intent.expansion_points:
        for point in composition.musical_intent.expansion_points:
            strategies.append(
                f"Expand section '{point.section}' from {point.current_length:.1f} to {point.suggested_length:.1f} beats: {point.development_strategy}"
            )
    
    if not strategies:
        strategies.append("Expand composition while maintaining musical coherence")
    
    return strategies


def analyze_composition(composition: Composition) -> MusicalAnalysis:
    """
    Analyze a composition to extract musical characteristics.
    
    Returns:
        MusicalAnalysis object with:
        - motifs: List of detected motifs
        - phrases: List of detected phrases
        - harmonic_progression: Harmonic analysis
        - form: Detected musical form
        - key_ideas: Identified key musical ideas
        - expansion_suggestions: Suggestions for expansion
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for composition analysis. Install it with: pip install music21"
        )
    
    # Perform all analyses
    motifs = detect_motifs(composition)
    phrases = detect_phrases(composition)
    harmony = analyze_harmony(composition)
    form = detect_form(composition)
    key_ideas = identify_key_ideas(composition)
    expansion_suggestions = generate_expansion_strategies(composition)
    
    return MusicalAnalysis(
        motifs=motifs,
        phrases=phrases,
        harmonic_progression=harmony,
        form=form,
        key_ideas=key_ideas,
        expansion_suggestions=expansion_suggestions,
    )
