# CLI Design: Refined for Human-AI Collaboration

## Design Principles

1. **Clear Intent**: Commands should clearly express their purpose
2. **Workflow Support**: Commands should support the core expansion workflow
3. **Consistency**: Consistent flag patterns across commands
4. **Progressive Enhancement**: Commands work without AI, better with AI
5. **Discoverability**: Help text and examples guide users

---

## Command Structure

### Core Workflow Commands

#### 1. `generate` - Create New Composition
**Status:** ✅ Exists, keep as-is

**Purpose:** Generate a new composition from description

**Current:**
```bash
pianist generate --provider gemini "Title: Sketch..." -o composition.json
pianist generate "Title: Sketch..." -o prompt.txt  # Generate prompt template
```

**Assessment:** ✅ Good - No changes needed

---

#### 2. `annotate` - Mark Musical Intent (NEW)
**Status:** ❌ Missing - Critical for core goal

**Purpose:** Mark key ideas, expansion points, and creative direction

**Design:**
```bash
# Manual annotation
pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening ascending motif" --importance high \
  --mark-phrase "0-16" "Opening phrase" --importance high \
  --mark-expansion "section A" --target-length 120 \
  --preserve "motif_1,phrase_A" \
  -o sketch_annotated.json

# Auto-detect and annotate
pianist annotate -i sketch.json --auto-detect -o sketch_annotated.json

# Interactive annotation (future)
pianist annotate -i sketch.json --interactive -o sketch_annotated.json

# Show current annotations
pianist annotate -i sketch.json --show
```

**Flags:**
- `-i, --input`: Input composition JSON (required)
- `-o, --output`: Output annotated JSON (optional, defaults to overwrite)
- `--mark-motif START-DURATION DESCRIPTION`: Mark a motif
  - `--importance {high,medium,low}`: Importance level
  - `--development-direction TEXT`: How to develop
- `--mark-phrase START-DURATION DESCRIPTION`: Mark a phrase
- `--mark-harmonic-progression START-DURATION DESCRIPTION`: Mark harmonic progression
- `--mark-expansion SECTION`: Mark expansion point
  - `--target-length BEATS`: Target length for expansion
  - `--development-strategy TEXT`: How to expand
- `--preserve IDS`: Comma-separated list of idea IDs to preserve
- `--auto-detect`: Automatically detect and annotate key ideas
- `--show`: Show current annotations without modifying
- `--overwrite`: Overwrite input file (default if no -o)

**Implementation Notes:**
- Uses schema extensions (MusicalIntent, KeyIdea, ExpansionPoint)
- Can work incrementally (add annotations to existing)
- Auto-detect uses analysis module

---

#### 3. `expand` - Expand Incomplete Composition (NEW)
**Status:** ❌ Missing - Critical for core goal

**Purpose:** Expand incomplete compositions intelligently

**Design:**
```bash
# Basic expansion (no AI, just analysis and strategy)
pianist expand -i sketch_annotated.json --target-length 300 -o expanded.json

# Expansion with AI
pianist expand -i sketch_annotated.json \
  --target-length 300 \
  --provider gemini \
  --preserve-motifs \
  --develop-sections \
  -o expanded.json --render

# Expansion with specific preservation
pianist expand -i sketch_annotated.json \
  --target-length 300 \
  --preserve "motif_1,phrase_A" \
  --expand-section "A" \
  --provider gemini \
  -o expanded.json

# Expansion with validation
pianist expand -i sketch_annotated.json \
  --target-length 300 \
  --provider gemini \
  --validate \
  -o expanded.json
```

**Flags:**
- `-i, --input`: Input composition JSON (required)
- `-o, --output`: Output expanded JSON (optional, prints to stdout)
- `--target-length BEATS`: Target length in beats (required)
- `--provider {gemini}`: AI provider to use (optional)
- `--model MODEL`: Model name (default: gemini-flash-latest)
- `--preserve-motifs`: Preserve all marked motifs
- `--preserve IDS`: Comma-separated list of idea IDs to preserve
- `--expand-section SECTION`: Expand specific section
- `--develop-sections`: Develop all sections intelligently
- `--validate`: Validate expansion quality before returning
- `--render`: Also render to MIDI
- `-m, --midi`: MIDI output path (auto-generated if --render used)
- `-r, --raw`: Save raw AI response
- `--verbose`: Show expansion progress
- `--overwrite`: Overwrite existing files

**Workflow:**
1. Analyze input composition (detect motifs, phrases, harmony, form)
2. Read musical intent annotations if present
3. Generate expansion strategy
4. Find relevant musical references
5. Generate enhanced prompt
6. Call AI (if provider specified)
7. Validate result (if --validate)
8. Return expanded composition

**Implementation Notes:**
- Integrates with analysis module
- Integrates with reference database (Phase 2)
- Integrates with validation module
- Can work without AI (just analysis and strategy)

---

#### 4. `render` - Convert to MIDI
**Status:** ✅ Exists, keep as-is

**Purpose:** Convert JSON → MIDI

**Current:**
```bash
pianist render -i composition.json -o out.mid
```

**Assessment:** ✅ Good - No changes needed

---

### Analysis & Understanding Commands

#### 5. `analyze` - Analyze Composition
**Status:** ✅ Exists, needs enhancement

**Purpose:** Analyze composition to extract musical characteristics

**Current:**
```bash
# Analyze MIDI
pianist analyze -i existing.mid -f json -o analysis.json

# Analyze and generate prompt
pianist analyze -i existing.mid -f prompt -p prompt.txt

# Analyze and generate new composition
pianist analyze -i existing.mid --provider gemini --instructions "..." -o new.json
```

**Enhancements Needed:**
```bash
# NEW: Analyze JSON composition (not just MIDI)
pianist analyze -i sketch.json -f json -o analysis.json

# NEW: Analyze for expansion
pianist analyze -i sketch.json --for-expansion -o expansion_strategy.json

# NEW: Analyze and auto-annotate
pianist analyze -i sketch.json --annotate-intent -o sketch_annotated.json

# NEW: Analyze incomplete composition
pianist analyze -i sketch.json --incomplete -o analysis.json
```

**New Flags:**
- `--for-expansion`: Analyze specifically for expansion (identify key ideas, expansion points)
- `--annotate-intent`: Automatically annotate musical intent based on analysis
- `--incomplete`: Treat as incomplete composition (different analysis focus)

**Implementation Notes:**
- Currently only works on MIDI files
- Need to support JSON input
- Need expansion-specific analysis
- Need auto-annotation integration

---

#### 6. `diff` - Show Changes (NEW)
**Status:** ❌ Missing - High priority

**Purpose:** Show what changed between compositions

**Design:**
```bash
# Basic diff (text)
pianist diff sketch.json expanded.json

# Musical diff (shows musical changes)
pianist diff sketch.json expanded.json --musical

# Show what was preserved vs added
pianist diff sketch.json expanded.json --show-preserved

# Show motif development
pianist diff sketch.json expanded.json --show-motifs

# Diff with annotations
pianist diff sketch.json expanded.json --annotated

# Output to file
pianist diff sketch.json expanded.json -o diff.txt
```

**Flags:**
- `INPUT1`: First composition (required)
- `INPUT2`: Second composition (required)
- `-o, --output`: Output file (optional, prints to stdout)
- `--musical`: Show musical diff (not just text)
- `--show-preserved`: Highlight what was preserved
- `--show-added`: Highlight what was added
- `--show-motifs`: Show how motifs were developed
- `--annotated`: Include annotation differences
- `--format {text,json,markdown}`: Output format

**Output Format:**
- Text: Human-readable diff
- JSON: Structured diff data
- Markdown: Formatted diff report

**Implementation Notes:**
- Compare two Composition objects
- Detect added/removed/modified events
- Track motif development
- Show preservation accuracy
- Musical diff shows note-level changes

---

### Utility Commands

#### 7. `iterate` - General Modification
**Status:** ✅ Exists, clarify purpose

**Purpose:** General modification of compositions (transpose, fix, modify with AI)

**Current:**
```bash
# Import MIDI → JSON
pianist iterate -i existing.mid -o seed.json

# Modify with AI
pianist iterate -i seed.json --provider gemini --instructions "Make it faster" -o updated.json

# Transpose
pianist iterate -i seed.json --transpose 2 -o transposed.json

# Generate prompt
pianist iterate -i seed.json -p prompt.txt --instructions "..."
```

**Clarification:**
- Keep for general modification workflows
- Not specifically for expansion (use `expand` for that)
- Update help text to clarify

**Updated Help Text:**
```
pianist iterate - Import JSON/MIDI and modify (transpose, fix, or modify with AI).
                   For expanding incomplete compositions, use 'pianist expand'.
```

**Assessment:** ✅ Keep, but clarify purpose

---

#### 8. `fix-pedal` - Fix Pedal Patterns
**Status:** ✅ Exists, keep as-is

**Purpose:** Fix incorrect sustain pedal patterns

**Assessment:** ✅ Good - No changes needed

---

## Command Relationships

### Workflow: Create → Annotate → Expand → Review

```bash
# Step 1: Create incomplete composition
pianist generate --provider gemini "90 beats..." -o sketch.json

# Step 2: Annotate (mark great ideas)
pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening motif" --importance high \
  --mark-expansion "A" --target-length 120 \
  -o sketch_annotated.json

# Step 3: Expand
pianist expand -i sketch_annotated.json \
  --target-length 300 \
  --preserve-motifs \
  --provider gemini \
  -o expanded.json --render

# Step 4: Review changes
pianist diff sketch_annotated.json expanded.json --musical

# Step 5: Refine if needed
pianist expand -i expanded.json \
  --refine-section "B" \
  --provider gemini \
  -o expanded_v2.json
```

### Alternative: Auto-Annotate Workflow

```bash
# Step 1: Create incomplete composition
pianist generate --provider gemini "90 beats..." -o sketch.json

# Step 2: Auto-annotate
pianist analyze -i sketch.json --annotate-intent -o sketch_annotated.json

# Step 3: Expand
pianist expand -i sketch_annotated.json --target-length 300 --provider gemini -o expanded.json

# Step 4: Review
pianist diff sketch_annotated.json expanded.json --musical
```

---

## Flag Consistency

### Common Flags (All Commands)
- `-i, --input`: Input file
- `-o, --output`: Output file
- `--debug`: Full traceback on errors
- `--verbose, -v`: Show progress
- `--overwrite`: Overwrite existing files

### AI-Related Flags (Commands with AI)
- `--provider {gemini}`: AI provider
- `--model MODEL`: Model name
- `-r, --raw`: Save raw AI response
- `--instructions TEXT`: Instructions for AI

### Rendering Flags (Commands that can render)
- `--render`: Also render to MIDI
- `-m, --midi`: MIDI output path

---

## Implementation Priority

### Phase 1: Foundation
1. **`annotate` command** (CRITICAL)
   - Manual annotation
   - Basic auto-detection
   - Integration with schema extensions

2. **`expand` command** (CRITICAL)
   - Basic expansion workflow
   - Integration with analysis
   - AI provider support

3. **`diff` command** (HIGH)
   - Basic text diff
   - Musical diff (basic)

4. **Enhance `analyze`** (HIGH)
   - Support JSON input
   - Expansion-specific analysis
   - Auto-annotation

### Phase 2: Intelligence Layer
5. **Enhance `expand`**
   - Reference database integration
   - Quality validation
   - Advanced strategies

6. **Enhance `diff`**
   - Advanced musical diff
   - Motif development tracking
   - Preservation visualization

### Phase 3: Refinement
7. **Enhance all commands**
   - Better error messages
   - More examples
   - Performance improvements

---

## Error Handling

### Common Error Patterns
- File not found → Clear error with suggestion
- Invalid JSON → Show validation errors
- Missing required flags → Show usage
- AI provider errors → Actionable error messages

### Validation Errors
- Schema validation → Show which field failed
- Musical validation → Show musical issues
- Expansion validation → Show what failed to preserve

---

## Help Text Improvements

### Command-Level Help
- Clear purpose statement
- Common use cases
- Example workflows
- Related commands

### Flag-Level Help
- Clear description
- Default values
- Examples where helpful
- Dependencies (e.g., --render requires --provider for some commands)

---

## Examples in Help

Each command should include:
- Basic usage example
- Common workflow example
- Advanced example (if applicable)

Example:
```bash
$ pianist expand --help

Expand an incomplete composition to a complete work.

Basic usage:
  pianist expand -i sketch.json --target-length 300 -o expanded.json

With AI:
  pianist expand -i sketch.json --target-length 300 --provider gemini -o expanded.json

Full workflow:
  pianist expand -i sketch_annotated.json \
    --target-length 300 \
    --preserve-motifs \
    --develop-sections \
    --provider gemini \
    --validate \
    -o expanded.json --render
```

---

## Backward Compatibility

### Existing Commands
- ✅ `render` - No changes
- ✅ `generate` - No changes
- ✅ `fix-pedal` - No changes
- ⚠️ `iterate` - Keep, clarify purpose
- ⚠️ `analyze` - Enhance, maintain backward compatibility

### New Commands
- `annotate` - New, no compatibility concerns
- `expand` - New, no compatibility concerns
- `diff` - New, no compatibility concerns

---

## Testing Strategy

### Unit Tests
- Each command's argument parsing
- Flag combinations
- Error handling
- Output formats

### Integration Tests
- Full workflows
- Command chaining
- File I/O
- AI provider integration

### User Experience Tests
- Help text clarity
- Error message usefulness
- Workflow smoothness
- Discoverability

---

## Documentation

### Command Documentation
- Update README with new commands
- Add examples for each command
- Document workflows
- Update AI_PROMPTING_GUIDE if needed

### Help Text
- Comprehensive help for each command
- Examples in help text
- Related commands section

---

## Summary

### New Commands to Add
1. **`annotate`** - Mark musical intent (CRITICAL)
2. **`expand`** - Expand incomplete compositions (CRITICAL)
3. **`diff`** - Show changes (HIGH)

### Commands to Enhance
1. **`analyze`** - Support JSON, expansion analysis, auto-annotation (HIGH)
2. **`iterate`** - Clarify purpose (MEDIUM)

### Commands to Keep As-Is
1. **`generate`** - ✅ Good
2. **`render`** - ✅ Good
3. **`fix-pedal`** - ✅ Good

This design aligns the CLI with the core goal of enabling rock solid human-AI collaboration for composition expansion.

