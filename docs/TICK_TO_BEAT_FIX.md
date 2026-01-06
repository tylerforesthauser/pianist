# Fix: Tick-to-Beat Unit Conversion Issue

## Problem

When using `pianist analyze --gemini`, the generated MIDI files were extremely long with notes placed far apart on the timeline. 

### Root Cause

Gemini was outputting `start` and `duration` values in **ticks** instead of **beats**, despite the system prompt clearly stating that these values should be in beats.

For example:
- Gemini output: `"start": 1920` (intended as 1920 ticks = 4 beats at ppq=480)
- System expected: `"start": 4` (4 beats)
- Renderer behavior: Treated 1920 as beats → `1920 * 480 = 921,600 ticks` (massive error!)

This caused compositions to be rendered with timing values that were 480x too large, resulting in MIDI files that were hundreds of hours long.

### Example

A composition with max start of 178,560 "beats" (actually ticks) would render as:
- 178,560 beats × 480 ticks/beat = 85,708,800 ticks
- At 65 bpm: (178,560 × 60) / 65 ≈ 164,824 seconds ≈ 45.8 hours!

## Solution

Added automatic detection and conversion in `src/pianist/parser.py`:

1. **Detection heuristic**: If any `start` or `duration` value is:
   - Greater than 1000 (suspiciously large for beats)
   - A multiple of `ppq` (within rounding tolerance)
   
   Then assume all timing values are in ticks.

2. **Conversion**: Divide all `start` and `duration` values by `ppq` to convert ticks to beats.

### Implementation

The fix is in `_normalize_timing_units()` function, which is called automatically during parsing in `parse_composition_from_text()`.

### Testing

Added tests in `tests/test_parser.py`:
- `test_parser_converts_ticks_to_beats()`: Verifies tick values are correctly converted
- `test_parser_does_not_convert_legitimate_beats()`: Ensures legitimate beat values are not affected

## Impact

- **Before**: MIDI files rendered with 480x incorrect timing, creating extremely long files
- **After**: Timing values are automatically corrected, producing correctly-timed MIDI files

## Future Improvements

Consider making the system prompt even more explicit about units, or adding validation warnings when suspicious values are detected but not converted.

