# Musical Analysis: Technical Details

This document explains how each analysis feature works, its limitations, and what users should expect from the results.

## Overview

The musical analysis system uses **music21** to convert compositions into a format suitable for analysis, then applies various algorithms to detect musical patterns and structures. The analysis is designed to be a **starting point** for understanding compositions, not a definitive musical analysis.

## Motif Detection

### How It Works

The enhanced motif detection algorithm uses a **multi-window, transposition-aware approach**:

1. **Multi-Window Extraction**: The system tries multiple window sizes (2-5 notes) to catch motifs of different lengths
2. **Melodic Line Extraction**: Extracts the melodic line (lowest pitch at each time point for simplicity)
3. **Pattern Matching**: For each window size, extracts all patterns and compares them using:
   - **Exact matching**: Same pitches in same order
   - **Transposition-aware matching**: Same interval pattern, different starting pitch
   - **Interval pattern matching**: Same melodic contour (intervals between notes)
4. **Motif Creation**: Patterns that appear at least twice (exact, transposed, or interval-matched) are considered motifs

**Algorithm Details:**
```python
# Try different window sizes (2-5 notes)
for window_size in range(2, 6):
    patterns = extract_patterns(melodic_line, window_size)
    
    # Find matching patterns
    for pattern1, pattern2 in all_pairs(patterns):
        if exact_match(pattern1, pattern2) or \
           transposed_match(pattern1, pattern2) or \
           interval_match(pattern1, pattern2):
            # Create motif
```

**Transposition Detection:**
- Normalizes pitch sequences to start at 0 (removes key differences)
- Compares interval patterns (e.g., C-D-E and G-A-B both have intervals [2, 2])
- Detects patterns that are the same when transposed

### Limitations

1. **Melodic Line Only**: Currently analyzes the lowest pitch at each time point:
   - May miss motifs in upper voices
   - Doesn't handle polyphonic textures well
   - Chords are simplified to their lowest note

2. **No Rhythmic Analysis**: Still ignores:
   - Rhythmic patterns (timing between notes)
   - Duration of notes
   - Syncopation

3. **No Inversion/Retrograde**: Does not detect:
   - Inverted motifs (intervals reversed)
   - Retrograde motifs (pattern played backwards)
   - Rhythmic variations

4. **False Positives**: May still detect random coincidences:
   - Similar interval patterns by chance
   - Very short compositions may produce many false matches

### What to Expect

- **Good at detecting**: 
  - Repeating melodic patterns (exact matches)
  - Transposed patterns (same pattern in different keys)
  - Patterns with same interval structure
- **May miss**: 
  - Rhythmic motifs
  - Inverted or retrograde motifs
  - Complex polyphonic patterns
- **May produce false positives**: Random interval coincidences

### Parameters

- `min_length`: Minimum motif duration in beats (default: 0.5)
- `max_length`: Maximum motif duration in beats (default: 4.0)
- `window_sizes`: Multiple window sizes tested (2, 3, 4, 5 notes)

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

Enhanced harmonic analysis provides comprehensive chord and functional harmony information:

1. **Conversion to music21**: Compositions are converted to music21 Stream format
2. **Key Detection**: Automatically detects key using music21's key analysis, or uses composition's `key_signature`
3. **Chord Extraction**: For each note/chord event, extracts:
   - Pitches (MIDI note numbers)
   - Timing (offset in beats)
   - Chord name (using music21's `pitchedCommonName`)
4. **Roman Numeral Analysis**: Uses music21's `roman.romanNumeralFromChord` to determine:
   - Roman numeral (I, ii, V, etc.)
   - Function (tonic, dominant, subdominant)
   - Inversion (0 = root position, 1 = first inversion, etc.)
5. **Cadence Detection**: Identifies common cadence patterns:
   - Authentic cadence (V → I)
   - Plagal cadence (IV → I)
   - Deceptive cadence (V → vi)
6. **Voice Leading Analysis**: Analyzes how chords connect:
   - Common tones between consecutive chords
   - Stepwise motion vs. leaps
   - Voice leading quality (smooth vs. disjunct)

**Algorithm Details:**
```python
# Detect key
detected_key = stream.analyze('key') or composition.key_signature

# Analyze each chord
for chord in chords:
    # Roman numeral analysis
    rn = roman.romanNumeralFromChord(chord, key)
    roman_numeral = rn.figure
    function = determine_function(rn.scaleDegree)  # tonic/dominant/subdominant
    inversion = chord.inversion()
    
    # Store as ChordAnalysis object
    chord_analysis = ChordAnalysis(
        start=offset,
        pitches=chord_pitches,
        name=chord_name,
        roman_numeral=roman_numeral,
        function=function,
        inversion=inversion,
    )

# Detect cadences
for i in range(len(chords) - 1):
    if chords[i].roman_numeral == "V" and chords[i+1].roman_numeral == "I":
        # Authentic cadence detected
        mark_cadence(chords[i], chords[i+1], "authentic")

# Analyze voice leading
for i in range(len(chords) - 1):
    common_tones = count_common_pitches(chords[i], chords[i+1])
    stepwise_motion = count_stepwise_moves(chords[i], chords[i+1])
    voice_leading.append({
        'common_tones': common_tones,
        'stepwise_motion': stepwise_motion,
        'quality': 'smooth' if stepwise_motion > leaps else 'disjunct'
    })
```

### Limitations

1. **Key Detection Accuracy**: Automatic key detection may not always be correct:
   - Works best with clear tonal centers
   - May struggle with modal or atonal music
   - Requires sufficient musical material

2. **Roman Numeral Analysis**: Depends on accurate key detection:
   - May produce incorrect analysis if key is wrong
   - Doesn't handle modulations well
   - May miss chromatic chords or non-functional harmony

3. **Cadence Detection**: Simple pattern matching:
   - Only detects common cadence types (authentic, plagal, deceptive)
   - May miss more complex cadences
   - Requires Roman numeral analysis to work

4. **Voice Leading**: Simplified analysis:
   - Doesn't track individual voices
   - May not accurately represent complex textures
   - Treats chords as pitch sets, not voice-leading lines

### What to Expect

- **Good at**: 
  - Identifying chord names and basic harmony
  - Roman numeral analysis when key is clear
  - Detecting common cadence patterns
  - Basic voice leading analysis
- **Limited in**: 
  - Complex or ambiguous harmony
  - Music without clear tonal center
  - Polyphonic voice leading
- **Requires**: Key signature or clear tonal center for best results

### Output Structure

Each chord analysis includes:
- `start`: Timing in beats
- `pitches`: List of MIDI note numbers
- `name`: Chord name (e.g., "C-major triad")
- `roman_numeral`: Roman numeral (e.g., "I", "V", "ii")
- `function`: Functional harmony (e.g., "tonic", "dominant", "subdominant")
- `inversion`: Inversion number (0 = root position)
- `is_cadence`: Whether this chord is part of a cadence
- `cadence_type`: Type of cadence if applicable

The harmonic analysis also includes:
- `roman_numerals`: List of all Roman numerals in the progression
- `progression`: Harmonic progression as Roman numerals
- `cadences`: List of detected cadences with timing and type
- `voice_leading`: Voice leading analysis between consecutive chords

## Form Detection

### How It Works

Enhanced form detection uses both explicit section markers and automatic detection:

1. **Explicit Section Markers**: First checks for `SectionEvent` objects in the composition
2. **Automatic Section Detection**: If no explicit markers, automatically detects sections based on:
   - **Phrase boundaries**: Large gaps between phrases (>3 beats)
   - **Cadences**: Harmonic cadences (authentic, plagal, deceptive) often mark section endings
   - **Repetition patterns**: Similar phrases may indicate section returns
3. **Form Classification**: Analyzes section count and patterns:
   - 2 sections → "binary"
   - 3 sections → "ternary" (may check if first and third are similar for A-B-A)
   - 4+ sections → Checks for rondo pattern (A-B-A-C-A) or returns "custom"

**Algorithm Details:**
```python
# First, check for explicit sections
explicit_sections = find_section_events(composition)
if explicit_sections:
    return classify_form_from_sections(explicit_sections)

# Otherwise, detect sections automatically
phrases = detect_phrases(composition)
harmony = analyze_harmony(composition)
cadences = harmony.cadences

sections = []
current_section_start = phrases[0].start

for phrase in phrases:
    is_boundary = False
    
    # Large gap indicates section boundary
    if gap_after_phrase > 3.0:
        is_boundary = True
    
    # Cadence at phrase end indicates section boundary
    if cadence_near(phrase.end):
        is_boundary = True
    
    # Repetition may indicate section return
    if similar_to_earlier_phrase(phrase):
        is_boundary = True
    
    if is_boundary:
        sections.append({
            'start': current_section_start,
            'end': phrase.end,
            'label': f"Section {len(sections) + 1}"
        })
        current_section_start = next_phrase.start

# Classify form
if len(sections) == 2:
    return "binary"
elif len(sections) == 3:
    return "ternary"
elif len(sections) >= 4:
    if is_rondo_pattern(sections):
        return "rondo"
    return "custom"
```

### Limitations

1. **Automatic Detection Heuristics**: Relies on simple heuristics:
   - May miss subtle section boundaries
   - May create false boundaries in dense textures
   - Doesn't analyze musical similarity deeply

2. **Form Classification**: Simple pattern matching:
   - Doesn't verify that sections actually repeat (A-B-A vs A-B-C)
   - May misclassify complex forms
   - Doesn't detect sonata form or other sophisticated structures

3. **No Musical Similarity Analysis**: Doesn't deeply analyze:
   - Melodic similarity between sections
   - Harmonic relationships
   - Thematic development

4. **Phrase-Dependent**: Automatic detection depends on phrase detection:
   - If phrase detection fails, form detection may fail
   - Works best with clear phrase boundaries

### What to Expect

- **Good at**: 
  - Detecting form from explicit section markers
  - Basic automatic section detection in clear compositions
  - Classifying simple forms (binary, ternary, rondo)
- **May miss**: 
  - Subtle section boundaries
  - Complex forms (sonata, etc.)
  - Sections that don't have clear phrase/cadence boundaries
- **Works best with**: Explicit section markers or compositions with clear phrase structure

### Supported Forms

- **Binary**: Two sections (A-B)
- **Ternary**: Three sections, typically A-B-A
- **Rondo**: Multiple sections with recurring A section (A-B-A-C-A)
- **Custom**: Any other form or pattern

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

