# MIDI File Identification Implementation

This document describes the enhanced identification system implemented for MIDI files, addressing issues with generically named files and modern works.

---

## Overview

The identification system now uses a **priority-based approach** with multiple fallback methods:

1. **Metadata JSON files** (highest priority) - Explicit metadata in `filename.mid.json`
2. **Directory structure** - Extract composer from parent directory name
3. **Filename parsing** - Extract composer/title from filename patterns
4. **AI identification** - Two-stage approach:
   - **Filename-based AI parsing** - Parse/enhance filenames with structure
   - **Content-based AI identification** - Identify compositions from musical content
5. **Analysis-based generation** - Generate descriptive names from musical analysis

---

## Implementation Details

### 1. Metadata JSON Support

**Location:** `scripts/review_and_categorize_midi.py`

**Functions:**
- `load_metadata_json(file_path: Path)` - Loads companion JSON file if it exists

**Usage:**
- Create `filename.mid.json` alongside your MIDI file
- JSON file contains explicit metadata (composer, title, style, etc.)
- Takes highest priority - overrides all other identification methods

**Example:**
```json
{
  "composer": "Scott Joplin",
  "title": "Maple Leaf Rag",
  "style": "Ragtime",
  "form": "ragtime",
  "techniques": ["syncopation", "stride_bass"],
  "description": "Classic ragtime piece demonstrating syncopation"
}
```

### 2. Directory-Based Extraction

**Location:** `scripts/review_and_categorize_midi.py`

**Functions:**
- `extract_composer_from_directory(file_path: Path)` - Extracts composer from parent directory

**Usage:**
- Organize files in directories by composer: `references/Scott Joplin/maple_leaf_rag.mid`
- Script automatically detects composer from directory name
- Works with known composer patterns (see `COMPOSER_DEFINITIONS`)

**Examples:**
- `references/J.S. Bach/invention_1.mid` → Composer: "J.S. Bach"
- `references/Chopin/prelude_7.mid` → Composer: "Chopin"
- `references/Original/modern_piece.mid` → No composer (marked as original)

### 3. Helper Script

**Location:** `scripts/generate_metadata_json.py`

**Purpose:** Generate metadata JSON files easily

**Usage:**

```bash
# Interactive mode (prompts for information)
python scripts/generate_metadata_json.py file.mid

# Non-interactive mode
python scripts/generate_metadata_json.py file.mid \
    --composer "Scott Joplin" \
    --title "Maple Leaf Rag" \
    --style "Ragtime" \
    --form "ragtime" \
    --techniques "syncopation,stride_bass"

# Update existing JSON
python scripts/generate_metadata_json.py file.mid --update

# Show template/example
python scripts/generate_metadata_json.py --template
```

---

## Priority Order

The identification system checks sources in this order:

1. **Metadata JSON** (`filename.mid.json`)
   - If found, uses metadata from JSON file
   - Highest priority - overrides everything else

2. **Directory structure**
   - Extracts composer from parent directory name
   - Merges with filename parsing results

3. **Filename parsing**
   - Extracts composer/title from filename patterns
   - Uses unified identification module (`pianist.midi_identification`)
   - Supports both classical and modern naming conventions

4. **AI identification** (two-stage approach)
   - **Stage 1: Filename-based AI parsing**
     - Used when filename has structure but needs parsing/enhancement
     - Examples: "what-was-i-made-for--billie-eilish", "chopin-prelude-op28-no7"
     - AI parses the filename to extract artist/composer and title
   - **Stage 2: Content-based AI identification**
     - Used when filename is generic/unclear (e.g., "output4_unknown.mid")
     - AI analyzes musical content to identify well-known compositions
     - Works for both classical and modern works
   - System automatically chooses the appropriate stage based on filename quality

5. **Analysis-based generation**
   - Generates descriptive names from musical analysis
   - Fallback for unknown works

---

## Usage Examples

### Example 1: Generic Filename with Metadata JSON

**File:** `output4_unknown.mid`

**Solution:** Create `output4_unknown.mid.json`:

```json
{
  "composer": "Scott Joplin",
  "title": "Maple Leaf Rag",
  "style": "Ragtime",
  "form": "ragtime",
  "techniques": ["syncopation", "stride_bass"],
  "description": "Classic ragtime piece"
}
```

**Result:** Script uses metadata from JSON, ignoring generic filename.

### Example 2: Directory Organization

**File:** `references/Scott Joplin/maple_leaf.mid`

**Result:** Script extracts "Scott Joplin" from directory name, even if filename is generic.

### Example 3: Well-Named File

**File:** `Chopin - Prelude in A major Op. 28 No. 7.mid`

**Result:** Script extracts composer and title from filename (existing behavior).

### Example 4: Filename with Structure (Filename-based AI)

**File:** `what-was-i-made-for--billie-eilish.mid`

**Result:** 
- Filename has structure but needs parsing
- Uses filename-based AI parsing to extract: "Billie Eilish: What Was I Made For?"

### Example 5: Generic Filename (Content-based AI)

**File:** `output4_unknown.mid` (no JSON, no directory structure)

**Result:** 
- Filename is generic/unclear
- Uses content-based AI identification to analyze musical content
- Attempts to identify if it's a well-known composition
- Falls back to descriptive name if not identified

### Example 6: Modern Film Soundtrack

**File:** `Hans Zimmer - Interstellar (Main Theme).mid`

**Result:**
- Filename has clear structure
- Uses filename-based AI parsing to enhance formatting
- Extracts: "Hans Zimmer: Interstellar (Main Theme)"

---

## Migration Guide

### For Existing Generic Files

**Option 1: Create Metadata JSON Files (Recommended)**

```bash
# For each generic file, create companion JSON
python scripts/generate_metadata_json.py output4_unknown.mid
# Follow prompts to enter composer, title, etc.
```

**Option 2: Rename Files**

Follow the naming convention in [MIDI_FILE_NAMING_CONVENTION.md](MIDI_FILE_NAMING_CONVENTION.md):

```bash
# Rename generic files
mv output4_unknown.mid "Original - Modern Composition in E-flat minor.mid"
```

**Option 3: Organize in Directories**

```bash
# Move files to composer directories
mkdir -p references/Scott\ Joplin
mv maple_leaf_rag.mid references/Scott\ Joplin/
```

### For New Files

1. **Use proper naming convention** (see naming guide)
2. **Or create metadata JSON** using helper script
3. **Or organize in directories** by composer

---

## Benefits

### Metadata JSON Files
- ✅ Explicit control over metadata
- ✅ Works for any composer/work (not limited to known works)
- ✅ No need to rename files
- ✅ Easy to edit/correct
- ✅ Can include additional fields (year, source, notes)

### Directory Organization
- ✅ Natural organization
- ✅ Easy browsing
- ✅ Composer obvious from location
- ✅ Works with generic filenames

### Hybrid Approach
- ✅ Maximum flexibility
- ✅ Multiple fallback options
- ✅ Works for all use cases
- ✅ Backward compatible with existing files

---

## Testing

### Test Metadata JSON

```bash
# Create test file
echo '{"composer": "Test Composer", "title": "Test Piece"}' > test.mid.json

# Run review script
python scripts/review_and_categorize_midi.py --dir . --limit 1 --verbose
# Should use metadata from JSON file
```

### Test Directory Extraction

```bash
# Create directory structure
mkdir -p references/Test\ Composer
cp test.mid references/Test\ Composer/

# Run review script
python scripts/review_and_categorize_midi.py --dir references --limit 1 --verbose
# Should extract composer from directory name
```

### Test Helper Script

```bash
# Interactive mode
python scripts/generate_metadata_json.py test.mid

# Non-interactive mode
python scripts/generate_metadata_json.py test.mid \
    --composer "Test Composer" \
    --title "Test Piece"

# Verify JSON was created
cat test.mid.json
```

---

## Troubleshooting

### Metadata JSON Not Being Used

**Check:**
1. JSON file exists: `filename.mid.json` (exact match)
2. JSON is valid (use `python -m json.tool filename.mid.json` to validate)
3. JSON contains required fields: `composer` and `title`

### Directory Composer Not Detected

**Check:**
1. Directory name matches composer patterns (see `COMPOSER_DEFINITIONS`)
2. File is in a subdirectory (not root)
3. Directory name doesn't match special directories ("original", "unknown", etc.)

### Helper Script Errors

**Check:**
1. MIDI file exists
2. JSON file permissions (can write to directory)
3. Required fields provided (composer, title)

---

## AI Identification Details

### When to Use Filename-based vs Content-based

The system automatically determines which AI approach to use:

**Filename-based AI parsing is used when:**
- Filename has structure (contains separators, artist/composer patterns)
- Basic extraction found partial info (composer OR title, but not both complete)
- Filename is not generic (doesn't match patterns like "output4", "track1", etc.)

**Content-based AI identification is used when:**
- Filename is generic/unclear (matches patterns like "output4", "track1", "unknown")
- Filename-based parsing didn't work or wasn't applicable
- Need to identify composition from musical characteristics

### Supported Naming Formats

The system now supports both classical and modern naming conventions:

**Classical:**
- `J.S. Bach - Invention No. 1 BWV 772`
- `chopin-prelude-op28-no7`
- `j.s.-bach---invention-no.-1-bwv-772`

**Modern:**
- `Hans Zimmer - Interstellar (Main Theme)`
- `what-was-i-made-for--billie-eilish`
- `River Flows in You - Yiruma`

## Future Enhancements

Potential improvements:

1. **Batch metadata generation** - Generate JSON for multiple files at once
2. **Metadata validation** - Validate JSON against schema
3. **Auto-detection** - Attempt to auto-fill metadata from filename/analysis
4. **Template system** - Pre-defined templates for common composers/styles
5. **Integration with batch import** - Auto-generate JSON during import
6. **Enhanced modern work support** - Better recognition of film soundtracks, pop songs, etc.

---

## Related Documentation

- [MIDI_FILE_NAMING_CONVENTION.md](MIDI_FILE_NAMING_CONVENTION.md) - Standard naming format
- [ENHANCED_MIDI_IDENTIFICATION.md](ENHANCED_MIDI_IDENTIFICATION.md) - Design proposal
- [REFERENCE_DATABASE_CURATION.md](REFERENCE_DATABASE_CURATION.md) - Database curation guide

---

**Last Updated:** After implementation  
**Status:** ✅ Implemented and ready for testing

