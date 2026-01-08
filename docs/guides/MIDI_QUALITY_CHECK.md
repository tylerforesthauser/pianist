# MIDI Quality Check Guide

This guide explains how to use the quality check tool to verify MIDI files before importing them into the reference database.

## Overview

The `check_midi_quality.py` script analyzes MIDI files for:
- **Technical quality**: File structure, note density, velocity, timing
- **Musical quality**: Motif detection, phrase structure, harmonic coherence
- **Structure quality**: Bar count, track organization
- **AI assessment**: Musical coherence and suitability evaluation (when using `--ai` flag)

## Quick Start

**Important:** Make sure your virtual environment is activated before running the quality check script:
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### Check a Single File

```bash
python3 scripts/check_midi_quality.py file.mid --verbose
```

### Check Multiple Files

```bash
python3 scripts/check_midi_quality.py --dir references/ --verbose
```

### With AI Assessment

```bash
# Using Gemini (cloud)
   python3 scripts/check_midi_quality.py file.mid --ai --provider openrouter

# Using Ollama (local, no API key needed)
python3 scripts/check_midi_quality.py file.mid --ai --provider ollama
```

## Quality Metrics

### Overall Score (0-100%)

The tool calculates an overall quality score based on three categories:

- **Technical Score** (40% weight): File structure, note density, velocity distribution
- **Musical Score** (40% weight): Motif/phrase detection, harmonic analysis
- **Structure Score** (20% weight): Bar count, track organization

**Scoring Formula:**
- Each category starts at 1.0 (100%)
- **Technical**: -0.3 per error, -0.1 per warning
- **Musical**: -0.2 per error, -0.05 per warning
- **Structure**: -0.25 per error, -0.1 per warning
- **Overall**: Weighted average (40% technical + 40% musical + 20% structure)
- **Note**: "info" severity issues don't affect scores - they're informational only

**Example:**
- File with 1 technical error: Technical = 0.7, Musical = 1.0, Structure = 1.0
- Overall = (0.7 × 0.4) + (1.0 × 0.4) + (1.0 × 0.2) = 0.28 + 0.4 + 0.2 = **0.88 (88%)**

### Score Interpretation

- **80-100% (✅)**: Excellent quality, ready for import
- **60-79% (⚠️)**: Good quality, minor issues may exist
- **Below 60% (❌)**: Quality concerns, review before importing

## What Gets Checked

### Technical Quality Checks

1. **File Length**
   - ⚠️ Warning if < 4 beats (very short)
   - ℹ️ Info if > 2000 beats (very long)

2. **Track Structure**
   - ❌ Error if no tracks found
   - ❌ Error if track has no notes

3. **Note Density**
   - ⚠️ Warning if < 0.5 notes/bar (very sparse)
   - ⚠️ Warning if > 50 notes/bar (very dense)

4. **Velocity**
   - ⚠️ Warning if median velocity < 20 (very quiet)
   - ℹ️ Info if median velocity > 120 (very loud)

5. **Pitch Range**
   - ⚠️ Warning if < 12 semitones (very narrow)
   - ℹ️ Info if > 60 semitones (very wide)

6. **Tempo/Time Signature**
   - ℹ️ Info if many tempo changes (> 5)
   - ℹ️ Info if multiple time signatures

### Musical Quality Checks

1. **Motif Detection**
   - ⚠️ Warning if no motifs detected
   - ℹ️ Info if only 1 motif detected

2. **Phrase Detection**
   - ⚠️ Warning if no phrases detected

3. **Harmonic Analysis**
   - ⚠️ Warning if no chords detected
   - ℹ️ Info if key not detected

4. **Form Detection**
   - ℹ️ Info if form not detected

### Structure Quality Checks

1. **Bar Count**
   - ❌ Error if < 1 bar
   - ⚠️ Warning if < 4 bars

2. **Track Count**
   - ℹ️ Info if multiple tracks (may need piano track extraction)

## Usage Examples

### Basic Quality Check

```bash
# Check a single file
python3 scripts/check_midi_quality.py bach_invention_1.mid

# Output:
# ============================================================
# Quality Check: bach_invention_1.mid
# ============================================================
# 
# ✅ Overall Score: 85.00%
#    Technical: 90.00%
#    Musical:  85.00%
#    Structure: 80.00%
# 
# Summary:
#   duration_beats: 64.0
#   duration_seconds: 32.0
#   tracks: 1
#   motifs: 3
#   phrases: 4
#   chords: 12
#   key: C major
#   form: binary
# 
# ✅ No issues found!
```

### Verbose Output

```bash
python3 scripts/check_midi_quality.py file.mid --verbose

# Shows detailed information for each issue:
#   ⚠️ [technical] Very low note density (0.3 notes/bar)
#       track: Piano
#       density: 0.3
```

### Check Directory with Minimum Score

```bash
# Only show files that pass 70% threshold
python3 scripts/check_midi_quality.py --dir references/ --min-score 0.7

# Output includes summary:
# ============================================================
# Summary: 10 files checked
# ============================================================
# ✅ Passed (score >= 70%): 8
# ❌ Failed (score < 70%): 2
# 
# Average score (passed): 82.50%
# 
# Failed files:
#   poor_quality.mid: 45.00%
#   corrupted.mid: 30.00%
```

### With AI Assessment

```bash
   python3 scripts/check_midi_quality.py file.mid --ai --provider openrouter

# Adds AI assessment section:
# 🤖 AI Assessment:
#   This is a well-structured piece with clear motivic development.
#   The harmonic progression is coherent and the form is well-defined.
#   Would make an excellent reference example for sequential development.
```

### Export Results as JSON

```bash
python3 scripts/check_midi_quality.py --dir references/ --json results.json

# Creates results.json with structured data:
# {
#   "files_checked": 10,
#   "reports": [
#     {
#       "file": "bach_invention_1.mid",
#       "overall_score": 0.85,
#       "scores": {
#         "technical": 0.9,
#         "musical": 0.85,
#         "structure": 0.8
#       },
#       "issue_count": 0,
#       "issues": [],
#       "summary": {...}
#     },
#     ...
#   ]
# }
```

## Common Issues and Solutions

### Issue: "No motifs detected"

**Cause**: File may be too short, or pattern detection failed.

**Solution**: 
- Check if file is complete
- Verify it's a piano piece (not multi-instrument)
- May still be usable if it demonstrates other techniques

### Issue: "Very low note density"

**Cause**: Sparse texture, may be incomplete or have timing issues.

**Solution**:
- Verify file is complete
- Check if it's meant to be sparse (some styles are)
- May indicate missing notes

### Issue: "No tracks found" or "Track has no notes"

**Cause**: Corrupted or empty MIDI file.

**Solution**:
- File is likely unusable
- Try re-downloading or finding alternative source

### Issue: "Multiple tracks"

**Cause**: MIDI file contains multiple instruments.

**Solution**:
- Extract piano track if needed
- Use `pianist import` to convert, then manually edit JSON
- May still be usable if piano track is clear

### Issue: "Musical analysis failed"

**Cause**: music21 library issue or file format problem.

**Solution**:
- Ensure music21 is installed: `pip install music21`
- Check if file can be opened in other MIDI software
- May indicate format issues

## Integration with Import Workflow

### Recommended Workflow

1. **Gather files** in `references/` directory
2. **Quality check** all files:
   ```bash
   python3 scripts/check_midi_quality.py --dir references/ --min-score 0.7 --json quality_report.json
   ```
3. **Review results** and remove low-quality files
4. **Prepare metadata** CSV for remaining files
5. **Batch import** using `batch_import_references.py`

### Filtering Low-Quality Files

```bash
# Check and save results
python3 scripts/check_midi_quality.py --dir references/ --json quality.json

# Review quality.json to identify files to remove
# Then import only high-quality files
python3 scripts/batch_import_references.py --dir references/ --metadata metadata.csv
```

## Command-Line Options

### Input Options

- `file`: Single MIDI file to check
- `--dir`: Directory containing MIDI files
- `--pattern`: Glob pattern for files (default: `*.mid`)

### Quality Options

- `--min-score`: Minimum overall score to pass (0-1, default: 0.0)
- `--verbose`, `-v`: Print detailed information for each issue

### AI Options

- `--ai`: Use AI to assess musical quality
- `--provider`: AI provider: `openrouter` (cloud, default), `gemini` (cloud), or `ollama` (local). Default: `openrouter`
- `--model`: Model name. Default: `gemini-flash-latest` (Gemini) or `gpt-oss:20b` (Ollama)

### Output Options

- `--json`: Save results as JSON to file

## Tips

1. **Check before importing**: Always quality check files before batch importing
2. **Use minimum score**: Set `--min-score 0.7` to filter out low-quality files
3. **AI for edge cases**: Use `--ai` when unsure about musical quality
4. **Export results**: Use `--json` to track quality over time
5. **Review warnings**: Not all warnings are critical - use judgment

## Examples

### Example 1: Quick Check

```bash
python3 scripts/check_midi_quality.py bach_invention_1.mid
```

### Example 2: Comprehensive Check

```bash
python3 scripts/check_midi_quality.py \
  --dir references/ \
  --verbose \
  --ai \
  --min-score 0.75 \
  --json quality_report.json
```

### Example 3: Filter and Import

```bash
# Step 1: Check quality
python3 scripts/check_midi_quality.py --dir references/ --json quality.json

# Step 2: Review quality.json, remove low-quality files

# Step 3: Import remaining files
python3 scripts/batch_import_references.py --dir references/ --metadata metadata.csv
```

## See Also

- [`REFERENCE_DATABASE_CURATION.md`](REFERENCE_DATABASE_CURATION.md) - Main curation guide
- [`../../scripts/check_midi_quality.py`](../../scripts/check_midi_quality.py) - Quality check script
- [`../commands/analyze.md`](../commands/analyze.md) - Analysis command documentation

