#!/bin/bash
# Test script for musical analysis functionality
# This script creates example compositions and runs analysis on them

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/tests/analysis"

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_DIR"

echo "Creating test compositions..."

# Test 1: Simple chord progression
cat > "$OUTPUT_DIR/test1_simple.json" << 'EOF'
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

# Test 2: Repeating motif
cat > "$OUTPUT_DIR/test2_motif.json" << 'EOF'
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

# Test 3: Clear phrase boundaries
cat > "$OUTPUT_DIR/test3_phrases.json" << 'EOF'
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

# Test 4: Ternary form
cat > "$OUTPUT_DIR/test4_form.json" << 'EOF'
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

# Test 5: I-IV-V-I progression
cat > "$OUTPUT_DIR/test5_progression.json" << 'EOF'
{
  "title": "I-IV-V-I Chord Progression",
  "bpm": 120,
  "key_signature": "C",
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "name": "Piano",
      "events": [
        {"type": "note", "start": 0, "duration": 1, "pitches": [60, 64, 67], "velocity": 80},
        {"type": "note", "start": 1, "duration": 1, "pitches": [53, 57, 60], "velocity": 80},
        {"type": "note", "start": 2, "duration": 1, "pitches": [55, 59, 62], "velocity": 80},
        {"type": "note", "start": 3, "duration": 1, "pitches": [60, 64, 67], "velocity": 80}
      ]
    }
  ]
}
EOF

echo "Running analysis and rendering MIDI files..."

# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Process only the original test files (not analysis results)
for test_file in "$OUTPUT_DIR"/test[0-9]_*.json; do
    if [ -f "$test_file" ] && [[ ! "$test_file" =~ _analysis\.json$ ]]; then
        test_name=$(basename "$test_file" .json)
        echo ""
        echo "========================================="
        echo "Processing: $test_name"
        echo "========================================="
        
        # Render to MIDI first (for aural comparison)
        echo "Rendering MIDI..."
        pianist render -i "$test_file" -o "$OUTPUT_DIR/${test_name}.mid" 2>&1 || {
            echo "WARNING: MIDI rendering failed for $test_name (continuing with analysis)"
        }
        
        if [ -f "$OUTPUT_DIR/${test_name}.mid" ]; then
            echo "MIDI rendered: ${test_name}.mid"
        fi
        
        # Run analysis
        echo "Running analysis..."
        pianist analyze -i "$test_file" -o "$OUTPUT_DIR/${test_name}_analysis.json" 2>&1 || {
            echo "ERROR: Analysis failed for $test_name"
            continue
        }
        
        echo "Analysis complete. Results saved to: ${test_name}_analysis.json"
        echo ""
        echo "Summary:"
        python3 << PYTHON
import json
try:
    with open("$OUTPUT_DIR/${test_name}_analysis.json") as f:
        data = json.load(f)
    analysis = data.get('analysis', {})
    print(f"  Motifs detected: {len(analysis.get('motifs', []))}")
    print(f"  Phrases detected: {len(analysis.get('phrases', []))}")
    print(f"  Chords detected: {len(analysis.get('harmony', {}).get('chords', []))}")
    print(f"  Form: {analysis.get('form', 'None')}")
    print(f"  Expansion suggestions: {len(analysis.get('expansion_suggestions', []))}")
except Exception as e:
    print(f"  Error reading results: {e}")
PYTHON
    fi
done

echo ""
echo "========================================="
echo "All tests complete!"
echo "Results saved in: $OUTPUT_DIR"
echo "========================================="
echo ""
echo "Generated files:"
echo "  - JSON compositions: test*.json"
echo "  - MIDI files (for aural comparison): test*.mid"
echo "  - Analysis results: test*_analysis.json"
echo ""
echo "To view detailed analysis results:"
echo "  cat $OUTPUT_DIR/test*_analysis.json | jq '.'"
echo ""
echo "To listen to MIDI files:"
echo "  - macOS: open $OUTPUT_DIR/*.mid"
echo "  - Linux: timidity $OUTPUT_DIR/*.mid"
echo "  - Or use any DAW/sequencer to import the MIDI files"
echo ""
echo "Aural Comparison Tips:"
echo "  1. Listen to each MIDI file while reviewing its analysis"
echo "  2. Check if detected motifs match what you hear"
echo "  3. Verify phrase boundaries align with musical phrasing"
echo "  4. Confirm chord identifications sound correct"
echo "  5. Assess if form detection matches the musical structure"

