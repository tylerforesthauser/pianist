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
    from music21 import converter, analysis, stream, pitch, note, chord, meter, tempo, key
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False

from .schema import Composition, NoteEvent, TempoEvent


@dataclass
class HarmonicAnalysis:
    """Results of harmonic analysis."""
    chords: list[dict[str, Any]]  # List of chord analyses with timing
    roman_numerals: list[str] | None = None  # Roman numeral analysis if available
    key: str | None = None  # Detected key


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


def analyze_harmony(composition: Composition) -> HarmonicAnalysis:
    """
    Analyze harmonic progression and functional harmony.
    
    Uses music21's harmonic analysis capabilities.
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for harmonic analysis. Install it with: pip install music21"
        )
    
    # Convert to music21 stream
    s = _composition_to_music21_stream(composition)
    
    # Perform harmonic analysis
    # Get chords from the stream
    chords_list: list[dict[str, Any]] = []
    
    # Extract chords from all parts
    # Use getElementsByClass to get parts from the stream
    parts = s.getElementsByClass(stream.Part)
    if not parts:
        # If no parts, treat the stream itself as a single part
        parts = [s]
    
    for part in parts:
        for element in part.flatten().notes:
            if hasattr(element, 'offset'):
                offset = float(element.offset)
                if isinstance(element, chord.Chord):
                    chord_pitches = [p.midi for p in element.pitches]
                    chord_name = element.pitchedCommonName
                    chords_list.append({
                        'start': offset,
                        'pitches': chord_pitches,
                        'name': chord_name,
                    })
                elif isinstance(element, note.Note):
                    chords_list.append({
                        'start': offset,
                        'pitches': [element.pitch.midi],
                        'name': element.pitch.name,
                    })
    
    # Try to get Roman numeral analysis if possible
    roman_numerals: list[str] | None = None
    detected_key: str | None = None
    
    try:
        # Attempt Roman numeral analysis
        # This requires a key to be established
        if composition.key_signature:
            # Set key for analysis
            s.keySignature = key.KeySignature(composition.key_signature)
            # Try to get analysis
            # Note: Full Roman numeral analysis may require more setup
            detected_key = composition.key_signature
    except Exception:
        # If analysis fails, continue without Roman numerals
        pass
    
    return HarmonicAnalysis(
        chords=chords_list,
        roman_numerals=roman_numerals,
        key=detected_key or composition.key_signature,
    )


def detect_motifs(composition: Composition, min_length: float = 0.5, max_length: float = 4.0) -> list[Motif]:
    """
    Detect recurring melodic/rhythmic patterns (motifs) in the composition.
    
    This is a basic implementation. More sophisticated algorithms can be built on top.
    
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
    
    # Extract all notes with their timing
    all_notes: list[tuple[float, list[int]]] = []
    
    # Use getElementsByClass to get parts from the stream
    parts = s.getElementsByClass(stream.Part)
    if not parts:
        # If no parts, treat the stream itself as a single part
        parts = [s]
    
    for part in parts:
        for element in part.flatten().notes:
            if hasattr(element, 'offset'):
                offset = float(element.offset)
                if isinstance(element, chord.Chord):
                    pitches = sorted([p.midi for p in element.pitches])
                    all_notes.append((offset, pitches))
                elif isinstance(element, note.Note):
                    all_notes.append((offset, [element.pitch.midi]))
    
    # Sort by time
    all_notes.sort(key=lambda x: x[0])
    
    # Simple pattern matching: look for repeated pitch sequences
    motifs: list[Motif] = []
    motif_length = min_length
    
    # For now, implement a simple approach:
    # Look for short sequences (2-4 notes) that repeat
    # This is a placeholder - more sophisticated algorithms needed
    
    # Group notes into small windows and look for repeats
    window_size = 3  # Look for 3-note patterns
    patterns: dict[tuple[int, ...], list[float]] = {}
    
    for i in range(len(all_notes) - window_size + 1):
        window = all_notes[i:i+window_size]
        # Extract pitch pattern (ignoring timing for now)
        pitch_pattern = tuple(sorted(set(p for _, pitches in window for p in pitches)))
        
        if len(pitch_pattern) > 0:
            if pitch_pattern not in patterns:
                patterns[pitch_pattern] = []
            patterns[pitch_pattern].append(window[0][0])  # Start time
    
    # Find patterns that appear multiple times
    for pattern, occurrences in patterns.items():
        if len(occurrences) >= 2:  # Pattern appears at least twice
            # Calculate duration (approximate)
            start = min(occurrences)
            end = max(occurrences) + motif_length
            duration = end - start
            
            if min_length <= duration <= max_length:
                motifs.append(Motif(
                    start=start,
                    duration=duration,
                    pitches=list(pattern),
                    description=f"Recurring pattern with {len(occurrences)} occurrences"
                ))
    
    return motifs


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


def detect_form(composition: Composition) -> str | None:
    """
    Detect musical form (binary, ternary, sonata, etc.).
    
    This is a basic implementation. More sophisticated analysis needed.
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for form detection. Install it with: pip install music21"
        )
    
    # For now, use simple heuristics based on sections
    # Look for section markers in the composition
    sections: list[str] = []
    
    for track in composition.tracks:
        for event in track.events:
            if hasattr(event, 'type') and event.type == 'section':
                if hasattr(event, 'label'):
                    sections.append(event.label)
    
    # Simple form detection based on sections
    if len(sections) == 0:
        return None
    elif len(sections) == 2:
        return "binary"
    elif len(sections) == 3:
        return "ternary"
    else:
        return "custom"
    
    # More sophisticated form detection would analyze:
    # - Repetition patterns
    # - Harmonic structure
    # - Melodic similarity
    # - Section lengths and relationships


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
