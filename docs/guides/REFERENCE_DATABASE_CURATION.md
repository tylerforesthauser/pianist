# Reference Database Curation Guide

This guide explains how to curate and populate the reference database with musical examples that will guide AI expansion.

## Overview

The reference database stores example compositions demonstrating:
- **Motif development** (sequence, inversion, augmentation, diminution)
- **Phrase expansion** (extending phrases, developing melodic lines)
- **Transitions** (smooth section transitions, modulations)
- **Form structures** (binary, ternary, sonata, rondo, theme & variations)
- **Style examples** (Baroque, Classical, Romantic, Modern)

**Target:** 100+ high-quality reference examples

## Current Status

- ✅ Database infrastructure complete
- ✅ Batch import tools available
- ⚠️ Only 3 initial examples (need 100+)

## Sources for Reference Files

> **📋 See [REFERENCE_CURATION_LIST.md](REFERENCE_CURATION_LIST.md) for a comprehensive curated list of recommended public domain works organized by technique, form, and style.**

### 1. Public Domain MIDI Collections

**Recommended sources:**
- **IMSLP (International Music Score Library Project)**: Public domain scores, some have MIDI files
- **MuseScore Community**: Many public domain arrangements available as MIDI
- **Classical MIDI Archives**: Various public domain MIDI collections
- **Free Music Archive**: Some classical/public domain works

**Legal considerations:**
- Only use works in the public domain (composer died 70+ years ago in most jurisdictions)
- Verify copyright status before use
- Prefer works with clear licensing

### 2. Generated Examples

Create small, focused examples demonstrating specific techniques:
- Use `pianist generate` to create examples
- Focus on clear demonstrations of techniques
- Keep examples concise (16-64 beats typically)

### 3. User Contributions

- Your own compositions
- Compositions created specifically for the database
- Examples from collaborators

### 4. Existing Pianist Compositions

- Use compositions already in your project
- Extract interesting sections that demonstrate techniques
- Reuse motifs/phrases from existing work

## Curation Criteria

### Quality Standards

1. **Musical Coherence**
   - Examples should be musically sound
   - Clear demonstration of the intended technique
   - No obvious errors or artifacts

2. **Clarity of Purpose**
   - Each example should clearly demonstrate one or more techniques
   - Description should explain what the example shows
   - Avoid overly complex examples that obscure the technique

3. **Appropriate Length**
   - Motif examples: 4-16 beats
   - Phrase examples: 8-32 beats
   - Form examples: 32-128 beats
   - Transition examples: 4-16 beats

4. **Metadata Completeness**
   - Style, form, and techniques should be accurately tagged
   - Descriptions should be clear and informative
   - IDs should be unique and descriptive

### Coverage Goals

**By Style:**
- Baroque: 15-20 examples
- Classical: 20-25 examples
- Romantic: 20-25 examples
- Modern/Contemporary: 15-20 examples
- Other: 10-15 examples

**By Form:**
- Binary: 10-15 examples
- Ternary: 15-20 examples
- Sonata: 10-15 examples
- Rondo: 10-15 examples
- Theme & Variations: 10-15 examples
- Other: 20-30 examples

**By Technique:**
- Sequence: 15-20 examples
- Inversion: 10-15 examples
- Augmentation: 10-15 examples
- Diminution: 10-15 examples
- Phrase extension: 15-20 examples
- Transition: 15-20 examples
- Motif development: 20-25 examples
- Other: 20-30 examples

## Workflow

### Step 1: Gather Files

1. **Create a references directory:**
   ```bash
   mkdir -p references/
   ```

2. **Organize files:**
   - Place MIDI or JSON files in the directory
   - Use descriptive filenames (e.g., `bach_invention_sequence.mid`)

3. **Quality Check Files** (recommended):
   
   **Note:** Make sure your virtual environment is activated (`source .venv/bin/activate`)
   
   ```bash
   # Check single file
   python3 scripts/check_midi_quality.py file.mid --verbose
   
   # Check all files in directory
   python3 scripts/check_midi_quality.py --dir references/ --verbose
   
   # Check with AI assessment
   python3 scripts/check_midi_quality.py file.mid --ai --provider gemini
   
   # Set minimum quality score threshold
   python3 scripts/check_midi_quality.py --dir references/ --min-score 0.7
   ```
   
   The quality check tool analyzes:
   - **Technical quality**: Note density, velocity, pitch range, timing
   - **Musical quality**: Motifs, phrases, harmony, form detection
   - **Structure quality**: Bar count, track structure
   - **AI assessment** (optional): Musical coherence and suitability
   
   See [`MIDI_QUALITY_CHECK.md`](MIDI_QUALITY_CHECK.md) for detailed information.

4. **Prepare metadata CSV** (optional but recommended):
   ```bash
   # Create metadata.csv with columns:
   # filename,id,title,description,style,form,techniques
   ```

### Step 2: Prepare Metadata

Create a CSV file (`metadata.csv`) with the following columns:

```csv
filename,id,title,description,style,form,techniques
bach_invention_sequence.mid,bach_invention_sequence,"Bach Invention Sequence","Demonstrates sequential development of a motif in Baroque style",Baroque,binary,"sequence,motif_development"
mozart_phrase_extension.json,mozart_phrase_ext,"Mozart Phrase Extension","Shows how to extend a 4-beat phrase to 8 beats",Classical,ternary,"phrase_extension,melodic_continuation"
```

**Column descriptions:**
- `filename`: Name of the file (required)
- `id`: Reference ID (optional, auto-generated if not provided)
- `title`: Title (optional, uses composition title if not provided)
- `description`: Description of what the example demonstrates (required)
- `style`: Musical style (Baroque, Classical, Romantic, Modern, etc.)
- `form`: Musical form (binary, ternary, sonata, rondo, etc.)
- `techniques`: Comma-separated list of techniques

### Step 3: Import Files

**Option A: Batch import with metadata CSV**
```bash
python3 scripts/batch_import_references.py \
  --dir references/ \
  --metadata metadata.csv \
  --verbose
```

**Option B: Batch import without metadata (auto-detect from filenames)**
```bash
python3 scripts/batch_import_references.py \
  --dir references/ \
  --verbose
```

**Option C: Single file import**
```bash
python3 scripts/batch_import_references.py \
  --file references/example.json \
  --style Classical \
  --form ternary \
  --techniques sequence,inversion \
  --description "Example of sequential and inverted motif development"
```

**Option D: Using CLI directly**
```bash
# For JSON files
./pianist reference add -i example.json \
  --style Classical \
  --form ternary \
  --techniques sequence,inversion \
  --description "Example description"

# For MIDI files (convert first)
./pianist import -i example.mid -o example.json
./pianist reference add -i example.json \
  --style Classical \
  --form ternary \
  --techniques sequence,inversion
```

### Step 4: Verify Import

```bash
# List all references
./pianist reference list

# Count references
./pianist reference count

# Search for specific references
./pianist reference search --style Classical --technique sequence
```

### Step 5: Test Integration

The reference database is automatically used by the `expand` command:

```bash
# Expand a composition (references will be automatically included)
./pianist expand -i sketch.json --target-length 300 --provider gemini
```

## Batch Import Script

The `scripts/batch_import_references.py` script provides:

- **Directory import**: Import all files from a directory
- **Metadata CSV support**: Load metadata from CSV file
- **MIDI support**: Automatically converts MIDI to JSON
- **Dry run mode**: Preview what would be imported
- **Verbose output**: See detailed import progress
- **Error handling**: Continues on errors, reports failures

**Usage examples:**

```bash
# Dry run to preview
python3 scripts/batch_import_references.py --dir references/ --dry-run

# Import with metadata
python3 scripts/batch_import_references.py \
  --dir references/ \
  --metadata metadata.csv \
  --verbose

# Import only JSON files
python3 scripts/batch_import_references.py \
  --dir references/ \
  --pattern "*.json" \
  --metadata metadata.csv
```

## Metadata Template

Create a `metadata.csv` file with this structure:

```csv
filename,id,title,description,style,form,techniques
example1.mid,example_1,"Example 1","Description of example 1",Classical,ternary,"sequence,motif_development"
example2.json,example_2,"Example 2","Description of example 2",Romantic,binary,"phrase_extension"
```

## Tips

1. **Start Small**: Begin with 20-30 high-quality examples covering key techniques
2. **Focus on Clarity**: Each example should clearly demonstrate its technique
3. **Diverse Coverage**: Aim for variety in styles, forms, and techniques
4. **Regular Updates**: Add examples as you discover or create them
5. **Test Integration**: Verify that references are being used effectively in expansion

## Troubleshooting

### Import Errors

**"Unsupported file type"**
- Ensure files are `.json`, `.mid`, or `.midi`
- Check file extensions

**"Error parsing composition"**
- Verify JSON files are valid Pianist format
- Check MIDI files are not corrupted
- Try importing with `--verbose` to see detailed errors

### Metadata Issues

**Missing metadata**
- Files without metadata will use auto-generated IDs and composition titles
- Add descriptions manually later using the CLI

**CSV parsing errors**
- Ensure CSV uses UTF-8 encoding
- Check column names match exactly
- Verify no special characters break CSV parsing

## Next Steps

1. **Gather initial batch** (20-30 examples)
2. **Create metadata CSV** for your files
3. **Run batch import** with `--dry-run` first
4. **Import and verify** references are in database
5. **Test expansion** to see references in action
6. **Iterate** - add more examples over time

## See Also

- [`REFERENCE_CURATION_LIST.md`](REFERENCE_CURATION_LIST.md) - **Curated list of recommended public domain works**
- [`MIDI_QUALITY_CHECK.md`](MIDI_QUALITY_CHECK.md) - **MIDI quality checking guide**
- [`../commands/reference.md`](../commands/reference.md) - Reference command documentation
- [`../../scripts/batch_import_references.py`](../../scripts/batch_import_references.py) - Batch import script
- [`../../scripts/check_midi_quality.py`](../../scripts/check_midi_quality.py) - Quality check script
- [`../../scripts/add_initial_references.py`](../../scripts/add_initial_references.py) - Initial examples script

