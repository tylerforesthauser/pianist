# Musical Analysis Library Research

## Requirements

We need a Python library that can:
1. **Motif Detection**: Detect recurring melodic/rhythmic patterns
2. **Phrase Analysis**: Identify musical phrases and structure
3. **Harmonic Analysis**: Analyze chord progressions and functional harmony
4. **Form Detection**: Identify musical form (binary, ternary, sonata, etc.)
5. **Pattern Recognition**: Find and track musical patterns

## Candidate Libraries

### 1. music21

**Description:** Comprehensive toolkit for computer-aided musicology

**Capabilities:**
- ✅ Harmonic analysis (chord identification, Roman numeral analysis)
- ✅ Form analysis (built-in and custom)
- ✅ Pattern matching (search for patterns)
- ✅ MusicXML/MIDI import/export
- ✅ Note/pitch analysis
- ⚠️ Motif detection (possible but may need custom implementation)
- ⚠️ Phrase detection (possible but may need custom implementation)

**Pros:**
- Very comprehensive
- Well-documented
- Active development
- MIT license
- Can work with MIDI files
- Strong harmonic analysis

**Cons:**
- Large dependency footprint
- Can be complex for simple tasks
- May be overkill for some needs
- Learning curve

**Installation:**
```bash
pip install music21
```

**Example Usage:**
```python
from music21 import converter, analysis

# Load MIDI
score = converter.parse('composition.mid')

# Harmonic analysis
chord_analysis = analysis.chordalAnalysis.ChordalAnalysis(score)
```

**License:** MIT

**Status:** ✅ Strong candidate

---

### 2. librosa

**Description:** Audio and music analysis library

**Capabilities:**
- ✅ Audio feature extraction
- ✅ Tempo detection
- ✅ Onset detection
- ✅ Pitch tracking
- ⚠️ Harmonic analysis (limited)
- ❌ Motif detection (not primary focus)
- ❌ Phrase detection (not primary focus)
- ❌ Form detection (not primary focus)

**Pros:**
- Excellent for audio analysis
- Fast and efficient
- Well-documented
- BSD license

**Cons:**
- Focused on audio, not symbolic music
- Limited symbolic music analysis
- Not ideal for our use case

**Status:** ❌ Not ideal (audio-focused, not symbolic music)

---

### 3. mido (Already Used)

**Description:** MIDI file manipulation

**Capabilities:**
- ✅ MIDI file reading/writing
- ✅ Note extraction
- ⚠️ Basic analysis possible
- ❌ No built-in harmonic analysis
- ❌ No motif detection
- ❌ No phrase detection

**Status:** ✅ Already in use, but insufficient for analysis needs

---

### 4. Custom Implementation

**Description:** Build our own analysis algorithms

**Capabilities:**
- ✅ Full control
- ✅ Tailored to our needs
- ✅ No external dependencies
- ⚠️ Time-consuming to develop
- ⚠️ Need music theory expertise

**Status:** ⚠️ Possible, but music21 likely better starting point

---

## Recommendation

### Primary Choice: music21

**Rationale:**
1. **Comprehensive**: Covers harmonic analysis, form analysis, pattern matching
2. **MIDI Support**: Can work with MIDI files (our format)
3. **Well-Established**: Mature library with good documentation
4. **Extensible**: Can build custom analysis on top
5. **License**: MIT (compatible)

**What We'll Use It For:**
- Harmonic analysis (chord progressions, Roman numeral analysis)
- Form detection (identify sections, form types)
- Pattern matching (find recurring patterns)
- Foundation for motif/phrase detection (may need custom algorithms on top)

**What We'll Build Custom:**
- Motif detection algorithms (using music21 as foundation)
- Phrase detection algorithms (using music21 as foundation)
- Expansion strategy generation
- Quality validation

### Integration Strategy

1. **Use music21 for:**
   - Loading and parsing MIDI/JSON into music21 format
   - Harmonic analysis
   - Basic pattern matching
   - Form analysis

2. **Build custom on top:**
   - Motif detection (using music21's pattern matching)
   - Phrase detection (using music21's structure analysis)
   - Expansion strategy generation
   - Quality validation

## Implementation Plan

### Step 1: Add music21 Dependency
```toml
# pyproject.toml
dependencies = [
  # ... existing ...
  "music21>=9.0.0",
]
```

### Step 2: Create Analysis Module Structure
```python
# src/pianist/musical_analysis.py

from music21 import converter, analysis, stream

def analyze_composition(composition: Composition) -> MusicalAnalysis:
    # Convert Composition to music21 format
    # Run analysis
    # Return MusicalAnalysis object
    pass
```

### Step 3: Implement Basic Analysis
- Harmonic analysis
- Form detection
- Pattern matching

### Step 4: Build Custom Algorithms
- Motif detection
- Phrase detection
- Expansion strategy generation

## Testing Strategy

1. **Test with known compositions:**
   - Simple binary form
   - Ternary form
   - Clear motifs
   - Known harmonic progressions

2. **Validate accuracy:**
   - Compare analysis results with manual analysis
   - Test edge cases
   - Test with incomplete compositions

## Next Steps

1. ✅ Research libraries (this document)
2. [ ] Test music21 with sample compositions
3. [ ] Evaluate performance and accuracy
4. [ ] Make final decision
5. [ ] Add to dependencies
6. [ ] Create analysis module structure

## Questions to Answer

1. **Performance**: How does music21 perform with typical compositions?
2. **Accuracy**: How accurate is harmonic analysis?
3. **Integration**: How easy is it to convert our Composition format to music21?
4. **Customization**: How easy is it to build custom analysis on top?

## Resources

- music21 documentation: https://web.mit.edu/music21/doc/
- music21 GitHub: https://github.com/cuthbertLab/music21
- music21 examples: https://web.mit.edu/music21/doc/usersGuide/usersGuide_01_introduction.html

