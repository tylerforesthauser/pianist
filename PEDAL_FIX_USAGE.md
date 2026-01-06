# Fixing Sustain Pedal Patterns in Existing Compositions

## Overview

The `fix_pedal_patterns` function and CLI command can automatically fix incorrect sustain pedal patterns in existing composition JSON files. This is useful for compositions that were generated before the documentation improvements.

## What Gets Fixed

The fix function converts problematic patterns:

1. **Press-Release Pairs**: 
   - `duration=0, value=127` (press) followed by `duration=0, value=0` (release)
   - → Merged into single `duration>0` event

2. **Orphaned Presses**:
   - `duration=0, value=127` without matching release
   - → Extended to next pedal event or reasonable default (4-8 beats)

3. **Already Correct**:
   - Events with `duration>0` are kept as-is

## Usage

### CLI Command

```bash
# Fix a single file (overwrites input)
./pianist fix-pedal --in "output/Nocturne in Eb Major.json"

# Fix and save to new file
./pianist fix-pedal --in "output/Nocturne in Eb Major.json" --out "output/Nocturne in Eb Major (fixed).json"

# Fix and also render to MIDI
./pianist fix-pedal --in "output/Nocturne in Eb Major.json" --out "output/Nocturne in Eb Major (fixed).json" --render --out-midi "output/Nocturne in Eb Major (fixed).mid"
```

### Python API

```python
from pianist.parser import parse_composition_from_text
from pianist.pedal_fix import fix_pedal_patterns
from pianist.iterate import composition_to_canonical_json

# Load composition
with open("composition.json", "r") as f:
    comp = parse_composition_from_text(f.read())

# Fix pedal patterns
fixed = fix_pedal_patterns(comp)

# Save fixed composition
fixed_json = composition_to_canonical_json(fixed)
with open("composition_fixed.json", "w") as f:
    f.write(fixed_json)
```

### Batch Processing

For batch processing multiple files, you can create a simple script using the Python API:

```python
from pathlib import Path
from pianist.parser import parse_composition_from_text
from pianist.pedal_fix import fix_pedal_patterns
from pianist.iterate import composition_to_canonical_json

output_dir = Path("output")
for json_file in output_dir.glob("*.json"):
    comp = parse_composition_from_text(json_file.read_text())
    fixed = fix_pedal_patterns(comp)
    fixed_json = composition_to_canonical_json(fixed)
    json_file.write_text(fixed_json)
```

## Fix Algorithm

The fix uses these rules:

1. **Find press-release pairs**: Look for `duration=0, value=127` followed by `duration=0, value=0`
   - Calculate duration as `release.start - press.start`
   - Merge into single event with `duration>0`

2. **Handle orphaned presses**: If `duration=0, value=127` has no matching release:
   - If next pedal exists: extend to `next_pedal.start - 0.1` (small gap)
   - Otherwise: extend to end of composition (max 8 beats) or default 4 beats

3. **Preserve correct patterns**: Events with `duration>0` are unchanged

4. **Sort events**: All events are re-sorted by start time after fixing

## Examples

### Before Fix

```json
{
  "type": "pedal",
  "start": 0,
  "duration": 0,
  "value": 127
},
{
  "type": "pedal",
  "start": 4,
  "duration": 0,
  "value": 0
}
```

### After Fix

```json
{
  "type": "pedal",
  "start": 0,
  "duration": 4,
  "value": 127
}
```

## Limitations

- The fix uses reasonable defaults but may not match the original musical intent
- Overlapping pedals are handled by extending to the next pedal with a small gap
- Very complex pedal patterns may need manual review
- The fix preserves section/phrase annotations when merging events

## Verification

After fixing, verify the results:

1. Check the JSON file for `duration>0` on pedal events
2. Render to MIDI and listen for proper sustain pedal behavior
3. Compare before/after MIDI files to ensure pedaling is preserved

## Integration with Render Pipeline

You can integrate the fix into your render pipeline:

```python
from pianist.parser import parse_composition_from_text
from pianist.pedal_fix import fix_pedal_patterns
from pianist.renderers.mido_renderer import render_midi_mido

# Load and fix
comp = parse_composition_from_text(json_text)
fixed = fix_pedal_patterns(comp)

# Render
render_midi_mido(fixed, "output.mid")
```

This ensures all compositions have correct pedal patterns before rendering.
