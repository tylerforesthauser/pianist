# Testing Musical Analysis Functionality

> **Technical Details**: For information on how each analysis feature works, its algorithms, and limitations, see [analysis_technical_details.md](./analysis_technical_details.md).

## Quick Start: Testing the Analyze Command

### 1. Basic Test with a Simple Composition

Create a test composition file:

```bash
cat > test_simple.json << 'EOF'
{
  "title": "Simple C Major Chord",
  "bpm": 120,
  "key_signature": "C",
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "name": "Piano",
      "events": [
        {
          "type": "note",
          "start": 0,
          "duration": 1,
          "pitches": [60, 64, 67],
          "velocity": 80
        },
        {
          "type": "note",
          "start": 1,
          "duration": 1,
          "pitches": [62, 65, 69],
          "velocity": 80
        }
      ]
    }
  ]
}
EOF
```

Render to MIDI and run analysis:
```bash
# Render to MIDI for aural comparison
pianist render -i test_simple.json -o test_simple.mid

# Run analysis
pianist analyze -i test_simple.json -o analysis_simple.json
cat analysis_simple.json

# Listen to the MIDI file to compare with analysis
# macOS: open test_simple.mid
# Linux: timidity test_simple.mid
```

### 2. Test with a Composition Containing Motifs

Create a composition with repeating patterns:

```bash
cat > test_motif.json << 'EOF'
{
  "title": "Composition with Repeating Motif",
  "bpm": 120,
  "key_signature": "C",
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "name": "Piano",
      "events": [
        {"type": "note", "start": 0, "duration": 0.5, "pitches": [60], "velocity": 80},
        {"type": "note", "start": 0.5, "duration": 0.5, "pitches": [64], "velocity": 80},
        {"type": "note", "start": 1, "duration": 0.5, "pitches": [67], "velocity": 80},
        {"type": "note", "start": 4, "duration": 0.5, "pitches": [60], "velocity": 80},
        {"type": "note", "start": 4.5, "duration": 0.5, "pitches": [64], "velocity": 80},
        {"type": "note", "start": 5, "duration": 0.5, "pitches": [67], "velocity": 80}
      ]
    }
  ]
}
EOF

# Render to MIDI
pianist render -i test_motif.json -o test_motif.mid

# Analyze
pianist analyze -i test_motif.json -o analysis_motif.json

# Listen and compare: does the detected motif match what you hear?
```

### 3. Test with Phrase Boundaries

Create a composition with clear phrase boundaries (gaps):

```bash
cat > test_phrases.json << 'EOF'
{
  "title": "Composition with Clear Phrases",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "name": "Piano",
      "events": [
        {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80},
        {"type": "note", "start": 1, "duration": 1, "pitches": [62], "velocity": 80},
        {"type": "note", "start": 2, "duration": 1, "pitches": [64], "velocity": 80},
        {"type": "note", "start": 3, "duration": 1, "pitches": [65], "velocity": 80},
        {"type": "note", "start": 6, "duration": 1, "pitches": [67], "velocity": 80},
        {"type": "note", "start": 7, "duration": 1, "pitches": [69], "velocity": 80},
        {"type": "note", "start": 8, "duration": 1, "pitches": [71], "velocity": 80}
      ]
    }
  ]
}
EOF

# Render to MIDI
pianist render -i test_phrases.json -o test_phrases.mid

# Analyze
pianist analyze -i test_phrases.json -o analysis_phrases.json

# Listen: do the detected phrase boundaries match the musical phrasing?
```

### 4. Test with Form Detection (Ternary Form)

```bash
cat > test_form.json << 'EOF'
{
  "title": "Ternary Form Composition",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "name": "Piano",
      "events": [
        {"type": "section", "start": 0, "label": "A"},
        {"type": "note", "start": 0, "duration": 4, "pitches": [60, 64, 67], "velocity": 80},
        {"type": "section", "start": 4, "label": "B"},
        {"type": "note", "start": 4, "duration": 4, "pitches": [62, 65, 69], "velocity": 80},
        {"type": "section", "start": 8, "label": "A"},
        {"type": "note", "start": 8, "duration": 4, "pitches": [60, 64, 67], "velocity": 80}
      ]
    }
  ]
}
EOF

# Render to MIDI
pianist render -i test_form.json -o test_form.mid

# Analyze
pianist analyze -i test_form.json -o analysis_form.json

# Listen: does the detected form (ternary) match the musical structure?
```

## Aural Comparison Workflow

One of the most effective ways to evaluate analysis accuracy is to **listen to the music** while reviewing the analysis results.

### Quick Aural Test Workflow

1. **Render composition to MIDI:**
   ```bash
   pianist render -i composition.json -o composition.mid
   ```

2. **Run analysis:**
   ```bash
   pianist analyze -i composition.json -o analysis.json
   ```

3. **Listen to the MIDI file** while reviewing the analysis:
   - **macOS:** `open composition.mid` (opens in QuickTime or default MIDI player)
   - **Linux:** `timidity composition.mid` or use a DAW
   - **Windows:** Double-click the MIDI file or use a DAW

4. **Compare what you hear with what the analysis detected:**
   - Do the detected motifs actually sound like repeating patterns?
   - Do phrase boundaries align with natural musical breathing points?
   - Do the chord identifications match what you hear harmonically?
   - Does the form detection match the overall structure you perceive?

### Using the Automated Test Script

The included test script (`scripts/test_analysis_examples.sh`) automatically:
- Creates test compositions
- Renders them to MIDI
- Runs analysis on each
- Provides a summary

Run it with:
```bash
./scripts/test_analysis_examples.sh
```

This creates:
- `test_analysis_output/test*.json` - Original compositions
- `test_analysis_output/test*.mid` - MIDI files for listening
- `test_analysis_output/test*_analysis.json` - Analysis results

## Evaluating Accuracy and Effectiveness

### 1. Ground Truth Comparison

Create compositions with known characteristics and verify the analysis detects them correctly:

#### Test Case: Known Chord Progression
```json
{
  "title": "I-IV-V-I Progression",
  "bpm": 120,
  "key_signature": "C",
  "tracks": [{
    "events": [
      {"type": "note", "start": 0, "duration": 1, "pitches": [60, 64, 67], "velocity": 80},  // C major (I)
      {"type": "note", "start": 1, "duration": 1, "pitches": [53, 57, 60], "velocity": 80},  // F major (IV)
      {"type": "note", "start": 2, "duration": 1, "pitches": [55, 59, 62], "velocity": 80},  // G major (V)
      {"type": "note", "start": 3, "duration": 1, "pitches": [60, 64, 67], "velocity": 80}   // C major (I)
    ]
  }]
}
```

**Expected Results:**
- Harmony analysis should identify 4 chords
- Chord names should be recognizable (C major, F major, G major, C major)

#### Test Case: Clear Motif
```json
{
  "title": "Obvious Repeating Motif",
  "bpm": 120,
  "tracks": [{
    "events": [
      // Motif appears 3 times
      {"type": "note", "start": 0, "duration": 0.25, "pitches": [60], "velocity": 80},
      {"type": "note", "start": 0.25, "duration": 0.25, "pitches": [64], "velocity": 80},
      {"type": "note", "start": 0.5, "duration": 0.25, "pitches": [67], "velocity": 80},
      
      {"type": "note", "start": 4, "duration": 0.25, "pitches": [60], "velocity": 80},
      {"type": "note", "start": 4.25, "duration": 0.25, "pitches": [64], "velocity": 80},
      {"type": "note", "start": 4.5, "duration": 0.25, "pitches": [67], "velocity": 80},
      
      {"type": "note", "start": 8, "duration": 0.25, "pitches": [60], "velocity": 80},
      {"type": "note", "start": 8.25, "duration": 0.25, "pitches": [64], "velocity": 80},
      {"type": "note", "start": 8.5, "duration": 0.25, "pitches": [67], "velocity": 80}
    ]
  }]
}
```

**Expected Results:**
- Should detect at least 1 motif
- Motif should include pitches [60, 64, 67]
- Should note 3 occurrences

### 2. Edge Case Testing

#### Empty Composition
```json
{
  "title": "Empty",
  "bpm": 120,
  "tracks": [{"name": "Piano", "events": []}]
}
```

**Expected:** Should handle gracefully without errors

#### Single Note
```json
{
  "title": "Single Note",
  "bpm": 120,
  "tracks": [{
    "events": [
      {"type": "note", "start": 0, "duration": 1, "pitches": [60], "velocity": 80}
    ]
  }]
}
```

**Expected:** Should detect at least 1 phrase, may not detect motifs (too short)

#### Very Long Composition
Create a composition with 100+ notes and verify:
- Analysis completes in reasonable time
- Results are still meaningful
- No memory issues

### 3. Comparison with Manual Analysis

1. **Create a composition you understand musically**
2. **Manually analyze it:**
   - Identify motifs yourself
   - Mark phrase boundaries
   - Identify chord progressions
   - Determine form
3. **Run automated analysis**
4. **Compare results:**
   - Do detected motifs match your manual analysis?
   - Are phrase boundaries in the right places?
   - Are chord identifications correct?
   - Is the form detection accurate?

### 4. Testing with Real MIDI Files

Convert MIDI files to JSON and analyze:

```bash
# Import a MIDI file
pianist import -i your_song.mid -o song.json

# Analyze the imported composition
pianist analyze -i song.json -o song_analysis.json

# Review the analysis
cat song_analysis.json | jq '.analysis'
```

Compare with your musical knowledge of the piece.

### 5. Quantitative Metrics

Create a test suite that measures:

#### Precision and Recall for Motif Detection
- **True Positives:** Motifs correctly identified
- **False Positives:** Patterns incorrectly identified as motifs
- **False Negatives:** Real motifs that were missed

#### Phrase Boundary Accuracy
- Measure how close detected phrase boundaries are to actual boundaries
- Calculate percentage of correct boundary detections

#### Harmonic Analysis Accuracy
- Compare detected chord names with known chord names
- Measure accuracy of chord identification

### 6. Visual Inspection

For phrase and motif detection, you can visualize the results:

```python
# Create a simple visualization script
import json

with open('analysis.json') as f:
    analysis = json.load(f)

print("Detected Phrases:")
for phrase in analysis['analysis']['phrases']:
    print(f"  {phrase['start']:.2f} - {phrase['start'] + phrase['duration']:.2f} beats")

print("\nDetected Motifs:")
for motif in analysis['analysis']['motifs']:
    print(f"  Start: {motif['start']:.2f}, Duration: {motif['duration']:.2f}")
    print(f"  Pitches: {motif['pitches']}")
```

### 7. Stress Testing

Test with:
- **Very fast tempo** (200+ BPM)
- **Very slow tempo** (40 BPM)
- **Complex polyphony** (many simultaneous notes)
- **Sparse compositions** (long gaps between notes)
- **Dense compositions** (many notes in short time)

### 8. Regression Testing

Keep a set of "golden" test compositions with known expected results. Run analysis on them regularly to ensure:
- Results remain consistent
- New changes don't break existing functionality
- Accuracy doesn't degrade over time

## Suggested Test Workflow

1. **Start Simple:** Test with basic compositions you understand
2. **Build Complexity:** Gradually test more complex pieces
3. **Document Findings:** Keep notes on what works well and what doesn't
4. **Compare with Ground Truth:** Use compositions where you know the "correct" analysis
5. **Test Edge Cases:** Push the boundaries of what the system can handle
6. **Iterate:** Use findings to improve the analysis algorithms

## Common Issues to Watch For

1. **False Motif Detections:** Random note sequences that happen to repeat
2. **Missed Phrase Boundaries:** Long phrases that should be split
3. **Incorrect Chord Names:** Chords misidentified due to missing context
4. **Form Misclassification:** Complex forms classified as simple binary/ternary
5. **Timing Issues:** Offsets or durations calculated incorrectly

## Next Steps for Improvement

Based on your testing, you might want to:
- Tune motif detection parameters (min_length, max_length, window_size)
- Improve phrase detection heuristics (gap thresholds, phrase length estimates)
- Enhance harmonic analysis (better chord naming, Roman numeral analysis)
- Add more sophisticated form detection algorithms
- Implement validation against musical theory rules

