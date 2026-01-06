# Musical Analysis: Technical Details

This document explains how each analysis feature works, its limitations, and what users should expect from the results.

## Overview

The musical analysis system uses **music21** to convert compositions into a format suitable for analysis, then applies various algorithms to detect musical patterns and structures. The analysis is designed to be a **starting point** for understanding compositions, not a definitive musical analysis.

## Motif Detection

### How It Works

The current motif detection algorithm uses a **sliding window approach**:

1. **Window Extraction**: The system groups notes into small windows (default: 3 notes)
2. **Pattern Extraction**: For each window, it extracts the set of pitches (ignoring timing and order)
3. **Pattern Matching**: It looks for pitch sets that appear multiple times in the composition
4. **Motif Creation**: Patterns that appear at least twice are considered motifs

**Algorithm Details:**
```python
window_size = 3  # Look for 3-note patterns
patterns: dict[tuple[int, ...], list[float]] = {}

for i in range(len(all_notes) - window_size + 1):
    window = all_notes[i:i+window_size]
    # Extract pitch pattern (sorted set of all pitches in window)
    pitch_pattern = tuple(sorted(set(p for _, pitches in window for p in pitches)))
    
    if pitch_pattern not in patterns:
        patterns[pitch_pattern] = []
    patterns[pitch_pattern].append(window[0][0])  # Start time

# Find patterns that appear multiple times
for pattern, occurrences in patterns.items():
    if len(occurrences) >= 2:  # Pattern appears at least twice
        # Create motif
```

### Limitations

1. **Pitch-Only Matching**: Currently ignores:
   - Rhythmic patterns (timing between notes)
   - Note order within the window
   - Duration of notes
   - Octave differences (C4 and C5 are treated the same)

2. **Fixed Window Size**: Uses a fixed 3-note window, which may miss:
   - Longer motifs (4+ notes)
   - Shorter motifs (2 notes)
   - Motifs with varying lengths

3. **Simple Pattern Matching**: Does not account for:
   - Transposed motifs (same pattern in different keys)
   - Inverted or retrograde motifs
   - Rhythmic variations of the same melodic pattern

4. **False Positives**: May detect random coincidences as motifs if:
   - The same pitch set happens to appear multiple times by chance
   - The composition is very short or repetitive

### What to Expect

- **Good at detecting**: Simple repeating pitch patterns (e.g., C-E-G appearing multiple times)
- **May miss**: 
  - Rhythmic motifs
  - Transposed or varied motifs
  - Complex melodic patterns
- **May produce false positives**: Random pitch coincidences in sparse compositions

### Parameters

- `min_length`: Minimum motif duration in beats (default: 0.5)
- `max_length`: Maximum motif duration in beats (default: 4.0)
- `window_size`: Number of notes in pattern window (hardcoded: 3)

## Phrase Detection

### How It Works

The phrase detection uses **gap-based heuristics**:

1. **Note Extraction**: Collects all notes from the composition with their timing
2. **Gap Detection**: Identifies gaps between notes (time between note end and next note start)
3. **Boundary Detection**: Large gaps (>2 beats) are considered phrase boundaries
4. **Length Estimation**: Also considers typical phrase length (4 beats) to split long phrases

**Algorithm Details:**
```python
beats_per_phrase = 4.0  # Default phrase length

for start, duration in all_events:
    gap = start - current_phrase_end
    
    # If gap is large (more than 2 beats), start new phrase
    # Or if we've reached typical phrase length
    if gap > 2.0 or (start - current_phrase_start) >= beats_per_phrase * 2:
        # End current phrase, start new one
```

### Limitations

1. **Gap-Based Only**: Relies solely on timing gaps, ignoring:
   - Harmonic cadences
   - Melodic contour
   - Musical context
   - Rests (not explicitly represented in our format)

2. **Fixed Thresholds**: Uses hardcoded values:
   - Gap threshold: 2.0 beats
   - Typical phrase length: 4.0 beats
   - These may not work for all musical styles

3. **No Musical Context**: Doesn't consider:
   - Key changes
   - Tempo changes
   - Harmonic progressions
   - Melodic resolution

4. **Single-Track Assumption**: Works best with single-voice compositions

### What to Expect

- **Good at detecting**: Clear phrase boundaries with obvious gaps (e.g., 3-beat rest between phrases)
- **May miss**: 
  - Subtle phrase boundaries
  - Phrase boundaries in dense textures
  - Musical phrases that overlap or connect smoothly
- **May produce false positives**: Long notes or sustained chords may be split incorrectly

### Parameters

- `beats_per_phrase`: Typical phrase length (hardcoded: 4.0 beats)
- Gap threshold: Minimum gap for phrase boundary (hardcoded: 2.0 beats)

## Harmonic Analysis

### How It Works

Harmonic analysis extracts chord information from the composition:

1. **Conversion to music21**: Compositions are converted to music21 Stream format
2. **Chord Extraction**: For each note/chord event, extracts:
   - Pitches (MIDI note numbers)
   - Timing (offset in beats)
   - Chord name (using music21's `pitchedCommonName`)
3. **Key Detection**: Uses the composition's `key_signature` field if provided

**Algorithm Details:**
```python
# Extract chords from all parts
for part in stream.parts:
    for element in part.flatten().notes:
        if isinstance(element, chord.Chord):
            chord_pitches = [p.midi for p in element.pitches]
            chord_name = element.pitchedCommonName
            chords_list.append({
                'start': offset,
                'pitches': chord_pitches,
                'name': chord_name,
            })
```

### Limitations

1. **No Roman Numeral Analysis**: Currently does not provide functional harmony analysis (I, IV, V, etc.)
   - Requires more sophisticated key detection and analysis
   - Would need to establish key context more reliably

2. **No Voice Leading**: Doesn't analyze:
   - How chords connect to each other
   - Voice leading patterns
   - Harmonic rhythm

3. **Simple Chord Naming**: Uses music21's basic chord naming, which:
   - May not always match common practice naming
   - Doesn't consider inversions in naming
   - May produce verbose names for complex chords

4. **No Harmonic Context**: Doesn't consider:
   - Chord function within a key
   - Harmonic progressions
   - Cadences

### What to Expect

- **Good at**: Identifying basic chord names from pitch sets (e.g., "C-major triad")
- **Limited in**: 
  - Functional harmony analysis
  - Complex chord naming
  - Harmonic progression analysis
- **Requires**: Key signature to be set in composition for best results

### Future Enhancements

- Roman numeral analysis (I, ii, V, etc.)
- Inversion detection
- Harmonic progression analysis
- Cadence detection

## Form Detection

### How It Works

Form detection is currently **very basic** and relies on section markers:

1. **Section Extraction**: Looks for `SectionEvent` objects in the composition
2. **Pattern Matching**: Counts sections and matches to common forms:
   - 2 sections → "binary"
   - 3 sections → "ternary"
   - Other → "custom"

**Algorithm Details:**
```python
sections: list[str] = []

for track in composition.tracks:
    for event in track.events:
        if event.type == 'section':
            sections.append(event.label)

if len(sections) == 2:
    return "binary"
elif len(sections) == 3:
    return "ternary"
else:
    return "custom"
```

### Limitations

1. **Requires Manual Marking**: Only works if sections are explicitly marked with `SectionEvent` objects
2. **No Automatic Detection**: Does not analyze:
   - Repetition patterns
   - Harmonic structure
   - Melodic similarity
   - Section relationships

3. **Very Simple**: Only counts sections, doesn't verify:
   - If sections actually repeat (A-B-A vs A-B-C)
   - Section lengths
   - Musical similarity between sections

### What to Expect

- **Only works if**: You manually add section markers to your composition
- **Will not detect**: Form automatically from musical content
- **Very limited**: Only identifies binary/ternary based on section count

### Future Enhancements

- Automatic section detection based on:
  - Repetition patterns
  - Harmonic analysis
  - Melodic similarity
  - Key changes
- Verification that sections actually repeat (A-B-A vs A-B-C)
- Detection of more complex forms (sonata, rondo, etc.)

## Key Idea Identification

### How It Works

Key idea identification combines:

1. **Manual Annotations**: Extracts `KeyIdea` objects from `musical_intent.key_ideas` if present
2. **Auto-Detection**: Adds automatically detected motifs and phrases as key ideas
3. **Metadata**: Preserves importance levels and descriptions from manual annotations

### Limitations

- Depends on quality of motif/phrase detection
- May duplicate information (same idea detected multiple ways)
- No prioritization or ranking of importance

## Expansion Strategy Generation

### How It Works

Generates suggestions based on:

1. **Detected Features**: Uses analysis results (motifs, phrases, harmony, form)
2. **Manual Annotations**: Incorporates `ExpansionPoint` objects from `musical_intent`
3. **Heuristics**: Simple rules like "develop detected motifs" or "extend phrases"

### Limitations

- Very generic suggestions
- No specific musical guidance
- Doesn't consider musical style or context
- No validation of suggestions

## General Limitations

### Analysis Scope

The current analysis focuses on **structural and harmonic** aspects. It does not analyze:

- **Rhythm**: Rhythmic patterns, meter, syncopation
- **Dynamics**: Volume changes, articulation
- **Timbre**: Instrumentation, texture
- **Melody**: Melodic contour, intervals, scales
- **Counterpoint**: Voice leading, polyphonic relationships

### Accuracy Expectations

Users should expect:

- **Basic accuracy** for simple, clear musical patterns
- **Variable results** for complex or ambiguous music
- **False positives and negatives** are possible
- **Manual verification recommended** for important analyses

### Performance

- Analysis is relatively fast for typical compositions (<1 second for most pieces)
- May be slower for very large compositions (1000+ notes)
- Memory usage scales with composition size

## Best Practices for Users

1. **Understand the Limitations**: Know what each analysis feature can and cannot do
2. **Verify Results**: Always verify analysis results against your musical knowledge
3. **Use Manual Annotations**: For important ideas, use `musical_intent` annotations
4. **Combine Approaches**: Use both automatic detection and manual marking
5. **Iterate**: Use analysis as a starting point, refine manually as needed

## Future Improvements

Planned enhancements (see ROADMAP.md):

- More sophisticated motif detection (rhythmic patterns, transposition)
- Automatic phrase detection using musical context
- Roman numeral harmonic analysis
- Automatic form detection
- Melodic analysis (contour, intervals)
- Rhythmic pattern detection
- Validation and quality metrics

