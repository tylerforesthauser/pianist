# Enhanced MIDI File Identification

This document proposes enhanced methods for identifying MIDI files beyond filename parsing, especially for modern works and generically named files.

---

## Current Limitations

The current system relies primarily on:
1. **Filename parsing** - Extracts composer/title from filename patterns
2. **AI identification** - Uses AI to identify well-known compositions
3. **Fallback generation** - Creates descriptive names from musical analysis

**Problems with generic filenames:**
- Files like `output4_unknown.mid` can't be identified from filename
- AI identification works best for well-known classical works
- Modern/contemporary works may not be in AI training data
- No way to provide manual metadata

---

## Proposed Solutions

### Solution 1: Metadata Files (Recommended)

Create companion JSON files alongside MIDI files with explicit metadata.

#### Format: `filename.mid.json`

```json
{
  "composer": "Scott Joplin",
  "title": "Maple Leaf Rag",
  "catalog_number": null,
  "opus": null,
  "style": "Ragtime",
  "form": "ragtime",
  "techniques": ["syncopation", "stride_bass"],
  "description": "Classic ragtime piece demonstrating syncopation and stride piano technique",
  "year": 1899,
  "source": "Public domain",
  "notes": "Essential example of ragtime form"
}
```

#### Implementation

The review script would:
1. Check for `filename.mid.json` before processing
2. Use metadata from JSON file if available
3. Fall back to filename parsing if no JSON file
4. Still run quality checks and musical analysis

#### Benefits
- ✅ Explicit control over metadata
- ✅ Works for any composer/work (not limited to known works)
- ✅ Can include additional fields (year, source, notes)
- ✅ No need to rename files
- ✅ Easy to edit/correct

#### Example Usage

```
references/
  ├── maple_leaf_rag.mid
  ├── maple_leaf_rag.mid.json
  ├── unknown_modern.mid
  ├── unknown_modern.mid.json
  └── ...
```

### Solution 2: Directory-Based Organization

Organize files in directories by composer or category.

#### Structure

```
references/
  ├── J.S. Bach/
  │   ├── Invention No. 1 BWV 772.mid
  │   └── Prelude in C major BWV 846.mid
  ├── Chopin/
  │   ├── Prelude Op. 28 No. 7.mid
  │   └── Nocturne Op. 9 No. 2.mid
  ├── Scott Joplin/
  │   ├── Maple Leaf Rag.mid
  │   └── The Entertainer.mid
  ├── Original/
  │   ├── Modern Composition 1.mid
  │   └── Experimental Piece.mid
  └── Unknown/
      ├── Elegiac Prelude.mid
      └── Traditional Folk Song.mid
```

#### Implementation

The review script would:
1. Extract composer from directory name
2. Use filename as title (or extract from filename)
3. Combine directory + filename for full identification

#### Benefits
- ✅ Natural organization
- ✅ Easy to browse
- ✅ Composer obvious from location
- ✅ Can have subdirectories (e.g., `Chopin/Preludes/`)

#### Drawbacks
- ❌ Requires file organization
- ❌ Less flexible than metadata files

### Solution 3: Enhanced AI Identification

Improve AI identification to handle modern works better.

#### Current AI Prompt

The current `identify_composition_with_ai()` function focuses on well-known classical works.

#### Proposed Enhancements

1. **Expand composer database in prompt:**
   - Include modern composers (Joplin, Gershwin, Bartók, etc.)
   - Include jazz/ragtime composers
   - Include contemporary composers

2. **Musical style analysis:**
   - Analyze musical characteristics (syncopation, jazz harmony, etc.)
   - Suggest composer/style even if exact work unknown
   - Example: "This appears to be a ragtime piece, possibly by Scott Joplin or similar composer"

3. **Partial identification:**
   - If exact work unknown, identify style/period
   - Example: "Modern composition in ragtime style" instead of generic description

#### Implementation

Update the AI prompt in `identify_composition_with_ai()` to:
- Include modern/jazz composers in examples
- Ask for style identification even if work unknown
- Provide musical characteristics for style matching

#### Benefits
- ✅ Works with existing system
- ✅ No file organization needed
- ✅ Can identify style even if work unknown

#### Drawbacks
- ❌ Requires API calls (cost/time)
- ❌ May not identify obscure works
- ❌ Less reliable than explicit metadata

### Solution 4: Batch Metadata CSV

Create a single CSV file with metadata for all files.

#### Format: `metadata.csv`

```csv
filename,composer,title,catalog_number,opus,style,form,techniques,description,year,source
maple_leaf_rag.mid,Scott Joplin,Maple Leaf Rag,,,Ragtime,ragtime,"syncopation,stride_bass",Classic ragtime piece,1899,Public domain
unknown_modern.mid,Unknown,Modern Composition in E-flat minor,,,Modern,through_composed,"extended_tonality",Experimental modern piece,2020,Original
chopin_prelude_7.mid,Chopin,Prelude in A major,Op. 28 No. 7,Op. 28 No. 7,Romantic,ternary,"phrase_extension",Lyrical prelude,1839,Public domain
```

#### Implementation

The review script would:
1. Load `metadata.csv` at startup
2. Look up filename in CSV
3. Use CSV metadata if found
4. Fall back to filename parsing if not in CSV

#### Benefits
- ✅ Single file for all metadata
- ✅ Easy to edit in spreadsheet
- ✅ Can be version controlled
- ✅ Works with existing `batch_import_references.py`

#### Drawbacks
- ❌ Need to keep CSV in sync with files
- ❌ Less convenient than per-file JSON

---

## Recommended Approach: Hybrid Solution

Combine multiple methods for maximum flexibility:

### Priority Order

1. **Metadata JSON file** (`filename.mid.json`) - Highest priority
   - Explicit, per-file metadata
   - Most flexible

2. **Directory structure** - Medium priority
   - Extract composer from directory name
   - Natural organization

3. **Metadata CSV** - Medium priority
   - Batch metadata for multiple files
   - Easy to edit

4. **Filename parsing** - Lower priority
   - Current system
   - Works for well-named files

5. **AI identification** - Fallback
   - For unknown works
   - Can identify style even if work unknown

### Implementation Plan

1. **Add metadata JSON support** to review script
2. **Add directory-based extraction** to review script
3. **Enhance metadata CSV support** (already exists in `batch_import_references.py`)
4. **Improve AI prompts** for modern works
5. **Create helper script** to generate metadata JSON from CSV or manual input

---

## Implementation Details

### Metadata JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "composer": {
      "type": "string",
      "description": "Composer name (use canonical form)"
    },
    "title": {
      "type": "string",
      "description": "Work title"
    },
    "catalog_number": {
      "type": ["string", "null"],
      "description": "Catalog number (BWV, K., etc.)"
    },
    "opus": {
      "type": ["string", "null"],
      "description": "Opus number"
    },
    "style": {
      "type": ["string", "null"],
      "enum": ["Baroque", "Classical", "Romantic", "Late Romantic", "Impressionist", "Modern", "Contemporary", "Jazz", "Ragtime", "Blues", "Folk", null],
      "description": "Musical style/period"
    },
    "form": {
      "type": ["string", "null"],
      "description": "Musical form (binary, ternary, sonata, etc.)"
    },
    "techniques": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of techniques demonstrated"
    },
    "description": {
      "type": "string",
      "description": "Description of the work"
    },
    "year": {
      "type": ["integer", "null"],
      "description": "Year of composition"
    },
    "source": {
      "type": ["string", "null"],
      "description": "Source of the MIDI file"
    },
    "notes": {
      "type": ["string", "null"],
      "description": "Additional notes"
    }
  },
  "required": ["composer", "title"]
}
```

### Directory Structure Detection

```python
def extract_composer_from_directory(file_path: Path) -> str | None:
    """
    Extract composer from directory structure.
    
    Examples:
    - references/J.S. Bach/file.mid -> "J.S. Bach"
    - references/Chopin/Preludes/file.mid -> "Chopin"
    - references/Original/file.mid -> None (marked as original)
    """
    parent_dir = file_path.parent.name
    
    # Check if parent is a known composer directory
    if parent_dir in COMPOSER_DIRECTORIES:
        return parent_dir
    
    # Check if parent matches composer patterns
    for pattern, composer in COMPOSER_PATTERNS.items():
        if pattern.lower() in parent_dir.lower():
            return composer
    
    # Check for special directories
    if parent_dir.lower() in ["original", "unknown", "traditional"]:
        return None  # Will be marked as original
    
    return None
```

### Metadata JSON Loading

```python
def load_metadata_json(file_path: Path) -> dict[str, Any] | None:
    """Load metadata from companion JSON file if it exists."""
    json_path = file_path.with_suffix(file_path.suffix + ".json")
    
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                return metadata
        except Exception as e:
            print(f"Warning: Could not load metadata from {json_path}: {e}", file=sys.stderr)
    
    return None
```

---

## Helper Script: Generate Metadata JSON

Create a script to help generate metadata JSON files:

```python
#!/usr/bin/env python3
"""
Generate metadata JSON file for a MIDI file.

Usage:
    python scripts/generate_metadata.py file.mid
    python scripts/generate_metadata.py file.mid --interactive
    python scripts/generate_metadata.py file.mid --composer "Scott Joplin" --title "Maple Leaf Rag"
"""

# Implementation would:
# 1. Check if metadata JSON already exists
# 2. Prompt for composer, title, etc. (if interactive)
# 3. Generate JSON file
# 4. Validate against schema
```

---

## Migration Strategy

### For Existing Generic Files

1. **Option A: Create metadata JSON files**
   ```bash
   # For each generic file, create companion JSON
   # unknown_modern.mid -> unknown_modern.mid.json
   ```

2. **Option B: Rename files** (see [MIDI_FILE_NAMING_CONVENTION.md](MIDI_FILE_NAMING_CONVENTION.md))
   ```bash
   # Rename generic files to follow convention
   output4_unknown.mid -> Original - Modern Composition in E-flat minor.mid
   ```

3. **Option C: Use metadata CSV**
   ```bash
   # Add entries to metadata.csv
   # Script will use CSV metadata during import
   ```

### Recommended Workflow

1. **For new files:** Use proper naming convention (see naming guide)
2. **For existing generic files:** Create metadata JSON files
3. **For batch imports:** Use metadata CSV
4. **For unknown works:** Use AI identification as fallback

---

## Benefits Summary

### Metadata JSON Files
- ✅ Explicit control
- ✅ Works for any work/composer
- ✅ No file renaming needed
- ✅ Easy to edit

### Directory Organization
- ✅ Natural organization
- ✅ Easy browsing
- ✅ Composer obvious

### Enhanced AI
- ✅ Works with existing system
- ✅ Can identify style even if work unknown
- ✅ No file changes needed

### Hybrid Approach
- ✅ Maximum flexibility
- ✅ Multiple fallback options
- ✅ Works for all use cases

---

## Next Steps

1. **Implement metadata JSON support** in review script
2. **Add directory-based extraction** to review script
3. **Enhance AI prompts** for modern works
4. **Create helper script** for generating metadata JSON
5. **Update documentation** with examples
6. **Migrate existing generic files** using chosen method

---

**Last Updated:** Initial creation  
**Next Review:** After implementation

