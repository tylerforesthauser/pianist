# Command Structure Design: Clear Intent & Future Growth

## Design Principles

1. **Self-Documenting Names**: Command names should clearly indicate their purpose
2. **Single Responsibility**: Each command has one clear purpose
3. **Composable**: Commands can be chained in workflows
4. **Extensible**: Room for growth without breaking patterns
5. **Consistent Patterns**: Similar commands follow similar patterns

---

## Proposed Command Structure

### Core Workflow Commands (Composition Lifecycle)

#### 1. `generate` - Create New Composition
**Purpose:** Generate a new composition from description

**Status:** ✅ Keep as-is

**Usage:**
```bash
pianist generate --provider gemini "Title: Sketch..." -o composition.json
pianist generate "Title: Sketch..." -o prompt.txt  # Generate prompt template
```

**Future Growth:**
- Could add `--from-template` for template-based generation
- Could add `--style` for style-specific generation
- Could add `--seed` for seeded generation

---

#### 2. `import` - Import External Format (RENAME from `iterate` for MIDI import)
**Purpose:** Import compositions from external formats (MIDI, MusicXML, etc.)

**Current:** `iterate -i file.mid` does this, but name is unclear

**Proposed:**
```bash
# Import MIDI → JSON
pianist import -i existing.mid -o composition.json

# Import MusicXML (future)
pianist import -i existing.mxml -o composition.json

# Import with options
pianist import -i existing.mid --normalize -o composition.json
```

**Why Rename:**
- `import` clearly indicates bringing external format into Pianist format
- More intuitive than `iterate` for this use case
- Leaves room for other import formats

**Future Growth:**
- Support MusicXML, ABC, other formats
- Import options (normalize, merge tracks, etc.)

---

#### 3. `annotate` - Mark Musical Intent (NEW)
**Purpose:** Mark key ideas, expansion points, and creative direction

**Usage:**
```bash
# Manual annotation
pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening motif" --importance high \
  --mark-expansion "A" --target-length 120 \
  -o annotated.json

# Auto-detect
pianist annotate -i sketch.json --auto-detect -o annotated.json

# Show annotations
pianist annotate -i sketch.json --show
```

**Future Growth:**
- Interactive annotation mode
- Batch annotation
- Annotation templates
- Import/export annotations

---

#### 4. `expand` - Expand Incomplete Composition (NEW)
**Purpose:** Expand incomplete compositions to complete works

**Usage:**
```bash
# Basic expansion
pianist expand -i sketch.json --target-length 300 -o expanded.json

# With AI
pianist expand -i sketch.json --target-length 300 --provider gemini -o expanded.json

# With validation
pianist expand -i sketch.json --target-length 300 --provider gemini --validate -o expanded.json
```

**Future Growth:**
- Multiple expansion strategies
- Section-specific expansion
- Style-aware expansion
- Multi-step expansion

---

#### 5. `modify` - Modify Composition (RENAME from `iterate` for modification)
**Purpose:** Modify existing compositions (transpose, fix, refine with AI)

**Current:** `iterate` does this, but name is unclear

**Proposed:**
```bash
# Modify with AI
pianist modify -i composition.json --provider gemini --instructions "Make it faster" -o updated.json

# Transpose
pianist modify -i composition.json --transpose 2 -o transposed.json

# Generate modification prompt
pianist modify -i composition.json -p prompt.txt --instructions "..."
```

**Why Rename:**
- `modify` clearly indicates changing existing composition
- More specific than `iterate`
- Distinguishes from `expand` (which is expansion-specific)

**Future Growth:**
- More modification options (tempo, key, etc.)
- Batch modifications
- Modification presets

---

#### 6. `render` - Convert to MIDI
**Purpose:** Convert JSON → MIDI

**Status:** ✅ Keep as-is

**Usage:**
```bash
pianist render -i composition.json -o out.mid
```

**Future Growth:**
- Render to other formats (MusicXML, audio, etc.)
- Render options (instruments, tempo, etc.)

---

### Analysis & Understanding Commands

#### 7. `analyze` - Analyze Composition
**Purpose:** Analyze composition to extract musical characteristics

**Status:** ✅ Keep name, enhance functionality

**Current:**
```bash
pianist analyze -i existing.mid -f json -o analysis.json
```

**Enhanced:**
```bash
# Analyze MIDI
pianist analyze -i existing.mid -f json -o analysis.json

# Analyze JSON (NEW)
pianist analyze -i sketch.json -f json -o analysis.json

# Analyze for expansion (NEW)
pianist analyze -i sketch.json --for-expansion -o strategy.json

# Analyze and auto-annotate (NEW)
pianist analyze -i sketch.json --annotate -o annotated.json
```

**Future Growth:**
- More analysis types (harmonic, rhythmic, etc.)
- Comparative analysis
- Analysis export formats

---

#### 8. `diff` - Show Changes (NEW)
**Purpose:** Show what changed between compositions

**Usage:**
```bash
# Basic diff
pianist diff original.json modified.json

# Musical diff
pianist diff original.json modified.json --musical

# Show preservation
pianist diff original.json expanded.json --show-preserved
```

**Future Growth:**
- Diff formats (text, json, markdown, html)
- Diff filters (show only motifs, only harmony, etc.)
- Diff statistics

---

### Utility Commands

#### 9. `fix-pedal` - Fix Pedal Patterns
**Purpose:** Fix incorrect sustain pedal patterns

**Status:** ✅ Keep as-is (specific utility)

**Alternative Consideration:** Could be `modify --fix-pedal` but current name is clear

**Future Growth:**
- Fix other issues (timing, velocity, etc.)
- Or keep as specific utility commands

---

## Command Categories

### Composition Creation & Import
- `generate` - Create new
- `import` - Import external formats

### Composition Development
- `annotate` - Mark intent
- `expand` - Expand incomplete
- `modify` - Modify existing

### Analysis & Understanding
- `analyze` - Analyze composition
- `diff` - Show changes

### Output & Utilities
- `render` - Convert to MIDI
- `fix-pedal` - Fix pedal patterns

---

## Renaming Summary

### Current → Proposed

1. **`iterate` (MIDI import)** → **`import`**
   - Clearer intent: importing external format
   - More intuitive name
   - Room for other import formats

2. **`iterate` (modification)** → **`modify`**
   - Clearer intent: modifying existing composition
   - Distinguishes from `expand`
   - More specific than "iterate"

**Decision:** Split `iterate` into two commands:
- `import` - For importing external formats (MIDI → JSON)
- `modify` - For modifying compositions (transpose, AI modification, etc.)

---

## Complete Command List

### Current Commands (Keep)
- ✅ `generate` - Generate new composition
- ✅ `render` - Convert to MIDI
- ✅ `analyze` - Analyze composition (enhance)

### Commands to Rename
- 🔄 `iterate` (MIDI import) → `import`
- 🔄 `iterate` (modification) → `modify`
- 🔄 `fix-pedal` → `fix` (with `--pedal` flag)

### New Commands
- ➕ `annotate` - Mark musical intent
- ➕ `expand` - Expand incomplete composition
- ➕ `diff` - Show changes
- ➕ `fix` - Fix composition issues (replaces `fix-pedal`)

---

## Command Naming Rationale

### `generate`
- ✅ Clear: generates new composition
- ✅ Intuitive: common verb
- ✅ Extensible: can add generation types

### `import`
- ✅ Clear: imports external format
- ✅ Intuitive: standard term
- ✅ Extensible: can add import formats

### `annotate`
- ✅ Clear: adds annotations
- ✅ Intuitive: common term
- ✅ Extensible: can add annotation types

### `expand`
- ✅ Clear: expands incomplete composition
- ✅ Intuitive: common verb
- ✅ Extensible: can add expansion strategies

### `modify`
- ✅ Clear: modifies existing composition
- ✅ Intuitive: common verb
- ✅ Extensible: can add modification types

### `analyze`
- ✅ Clear: analyzes composition
- ✅ Intuitive: common term
- ✅ Extensible: can add analysis types

### `diff`
- ✅ Clear: shows differences
- ✅ Intuitive: standard term (like git diff)
- ✅ Extensible: can add diff formats/types

### `render`
- ✅ Clear: renders to output format
- ✅ Intuitive: common term
- ✅ Extensible: can add output formats

### `fix`
- ✅ Clear: fixes composition issues
- ✅ Extensible: can add more fix types via flags
- ✅ Consistent: follows pattern of other commands

---

## Workflow Examples with New Names

### Workflow 1: Create → Annotate → Expand → Review
```bash
# Step 1: Create
pianist generate --provider gemini "90 beats..." -o sketch.json

# Step 2: Annotate
pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening motif" --importance high \
  -o annotated.json

# Step 3: Expand
pianist expand -i annotated.json --target-length 300 --provider gemini -o expanded.json

# Step 4: Review
pianist diff annotated.json expanded.json --musical
```

### Workflow 2: Import → Modify → Render
```bash
# Step 1: Import
pianist import -i existing.mid -o composition.json

# Step 2: Modify
pianist modify -i composition.json --transpose 2 -o transposed.json

# Step 3: Render
pianist render -i transposed.json -o out.mid
```

### Workflow 3: Import → Analyze → Expand
```bash
# Step 1: Import
pianist import -i sketch.mid -o sketch.json

# Step 2: Analyze and auto-annotate
pianist analyze -i sketch.json --annotate -o annotated.json

# Step 3: Expand
pianist expand -i annotated.json --target-length 300 --provider gemini -o expanded.json
```

---

## Future Command Possibilities

### Potential Future Commands (Not Now)
- `export` - Export to other formats (MusicXML, audio, etc.)
- `merge` - Merge multiple compositions
- `split` - Split composition into sections
- `transpose` - Standalone transpose (or keep in `modify`)
- `validate` - Validate composition quality
- `compare` - Compare multiple compositions
- `template` - Work with composition templates

**Decision:** Don't add these now, but structure allows for them later.

---

## `fix` Command Design

### Purpose
Fix common composition issues (pedal patterns, timing, etc.)

### Design
```bash
# Fix pedal patterns
pianist fix -i composition.json --pedal -o fixed.json

# Fix multiple issues
pianist fix -i composition.json --pedal --timing -o fixed.json

# Fix all issues
pianist fix -i composition.json --all -o fixed.json

# Show what would be fixed
pianist fix -i composition.json --pedal --dry-run
```

### Flags
- `--pedal`: Fix sustain pedal patterns
- `--timing`: Fix timing issues (future)
- `--velocity`: Fix velocity issues (future)
- `--all`: Fix all available issues
- `--dry-run`: Show what would be fixed without modifying

### Future Growth
- Add more fix types via flags
- `--fix-timing`, `--fix-velocity`, `--fix-overlaps`, etc.
- Each fix type is independent and composable

---

## Implementation Plan

### Phase 1: Rename Existing Commands
1. Rename `iterate` (MIDI import) → `import`
2. Rename `iterate` (modification) → `modify`
3. Update all references
4. Update documentation

### Phase 2: Add New Commands
1. Implement `annotate` command
2. Implement `expand` command
3. Implement `diff` command

### Phase 3: Enhance Existing Commands
1. Enhance `analyze` to support JSON input
2. Add expansion-specific analysis
3. Improve help text and examples

---

## Backward Compatibility

**Decision:** Since user said not afraid of breaking changes, we can:
- Rename commands without aliases
- Update all documentation
- Update examples
- Clear migration path in release notes

**Migration:**
- Old: `pianist iterate -i file.mid` → New: `pianist import -i file.mid`
- Old: `pianist iterate -i file.json --transpose 2` → New: `pianist modify -i file.json --transpose 2`
- Old: `pianist iterate -i file.json --provider gemini` → New: `pianist modify -i file.json --provider gemini`

---

## Summary

### Final Command Set

**Composition Lifecycle:**
1. `generate` - Create new composition
2. `import` - Import external formats (MIDI, etc.)
3. `annotate` - Mark musical intent
4. `expand` - Expand incomplete composition
5. `modify` - Modify existing composition
6. `render` - Convert to MIDI

**Analysis & Understanding:**
7. `analyze` - Analyze composition
8. `diff` - Show changes

**Utilities:**
9. `fix-pedal` - Fix pedal patterns

### Renames
- `iterate` (MIDI import) → `import`
- `iterate` (modification) → `modify`

### New Commands
- `annotate`
- `expand`
- `diff`

This structure is:
- ✅ Clear and self-documenting
- ✅ Single responsibility per command
- ✅ Extensible for future growth
- ✅ Consistent naming patterns
- ✅ Supports core workflow

