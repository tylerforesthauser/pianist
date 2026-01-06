# CLI Structure & Ergonomics Assessment

## Current CLI Commands

### 1. `render`
**Purpose:** Convert JSON → MIDI

**Current:**
```bash
pianist render -i composition.json -o out.mid
```

**Assessment:** ✅ Good - Core functionality, works well

---

### 2. `iterate`
**Purpose:** Import JSON/MIDI, modify, optionally use AI

**Current:**
```bash
# Import MIDI → JSON
pianist iterate -i existing.mid -o seed.json

# Modify with AI
pianist iterate -i seed.json --provider gemini --instructions "Make it more lyrical" -o updated.json

# Transpose
pianist iterate -i seed.json --transpose 2 -o transposed.json

# Generate prompt
pianist iterate -i seed.json -p prompt.txt --instructions "Expand to 5 minutes"
```

**Assessment:**
- ✅ **Good:** Handles both directions (MIDI→JSON, JSON→JSON)
- ✅ **Good:** Supports AI modification
- ⚠️ **Issue:** Name "iterate" is generic - doesn't convey "expansion" intent
- ⚠️ **Issue:** No specific support for expansion workflow
- ⚠️ **Issue:** No way to mark "great ideas" before iteration
- ⚠️ **Issue:** No validation of expansion quality
- ⚠️ **Issue:** Instructions are free-form text - no structured guidance

**Gap for Core Goal:**
- No way to mark musical intent before expansion
- No expansion-specific command
- No quality validation
- No change tracking

---

### 3. `analyze`
**Purpose:** Analyze MIDI, generate prompts or new compositions

**Current:**
```bash
# Analyze and generate prompt
pianist analyze -i existing.mid -f prompt -p prompt.txt

# Analyze and generate new composition with AI
pianist analyze -i existing.mid --provider gemini --instructions "Create new piece" -o new.json
```

**Assessment:**
- ✅ **Good:** Extracts musical characteristics
- ✅ **Good:** Can generate prompts or use AI
- ⚠️ **Issue:** Focuses on "new composition inspired by" not "expand existing"
- ⚠️ **Issue:** No analysis of incomplete compositions
- ⚠️ **Issue:** No identification of "great ideas"

**Gap for Core Goal:**
- Doesn't analyze incomplete compositions for expansion
- Doesn't identify key ideas to preserve/develop

---

### 4. `generate`
**Purpose:** Generate new composition from description

**Current:**
```bash
# Generate with AI
pianist generate --provider gemini "Title: Sketch..." -o composition.json

# Generate prompt template
pianist generate "Title: Sketch..." -o prompt.txt
```

**Assessment:**
- ✅ **Good:** Clear purpose
- ✅ **Good:** Works with or without AI
- ✅ **Good:** Supports the "create incomplete composition" part of workflow

**Gap for Core Goal:**
- None - this is for creating the starting point

---

### 5. `fix-pedal`
**Purpose:** Fix pedal patterns

**Assessment:**
- ✅ **Good:** Utility command, works well
- ✅ **Good:** Not related to core goal, but useful

---

## Assessment Against Core Goal

### Core Goal Workflow
**Target:** 90-second incomplete composition → AI expands to 5-minute complete composition

### Current Workflow (What's Possible Now)
```bash
# Step 1: Create incomplete composition
pianist generate --provider gemini "Title: Sketch, 90 beats..." -o sketch.json

# Step 2: Try to expand (using iterate)
pianist iterate -i sketch.json --provider gemini \
  --instructions "Expand this 90-beat sketch to a complete 5-minute composition (300 beats). Preserve the opening motif and develop it throughout." \
  -o expanded.json --render
```

### Issues with Current Workflow

1. **No Musical Intent Annotation**
   - ❌ Can't mark "great ideas" before expansion
   - ❌ Can't specify which motifs to preserve
   - ❌ Can't mark expansion points
   - ❌ Instructions are free-form text - AI may not understand

2. **No Expansion-Specific Command**
   - ⚠️ `iterate` is generic - could mean modify, transpose, expand, etc.
   - ⚠️ No clear "expand" intent
   - ⚠️ No expansion-specific options (target length, preserve list, etc.)

3. **No Quality Validation**
   - ❌ No way to check if expansion preserved original ideas
   - ❌ No way to validate expansion quality
   - ❌ No feedback on what changed

4. **No Change Tracking**
   - ❌ Can't see what AI changed
   - ❌ Can't understand how motifs were developed
   - ❌ No diff visualization

5. **No Analysis of Incomplete Compositions**
   - ❌ `analyze` works on MIDI files, not JSON
   - ❌ No analysis of incomplete compositions to identify "great ideas"
   - ❌ No automatic detection of motifs/phrases

---

## Recommended CLI Improvements

### 1. Add `expand` Command (CRITICAL)

**Purpose:** Specifically for expanding incomplete compositions

**Proposed:**
```bash
# Basic expansion
pianist expand -i sketch.json --target-length 300 -o expanded.json

# With AI provider
pianist expand -i sketch.json --target-length 300 \
  --provider gemini \
  --preserve-motifs \
  --develop-sections \
  -o expanded.json --render

# With specific preservation
pianist expand -i sketch.json --target-length 300 \
  --preserve "motif_1,phrase_A" \
  --expand-section "A" \
  -o expanded.json
```

**Why:**
- Clear intent: "expand" not "iterate"
- Expansion-specific options
- Better ergonomics for the core workflow

---

### 2. Add `annotate` Command (CRITICAL)

**Purpose:** Mark musical intent (key ideas, expansion points)

**Proposed:**
```bash
# Manual annotation
pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening ascending motif" --importance high \
  --mark-expansion "section A" --target-length 120 \
  -o sketch_annotated.json

# Auto-detect and annotate
pianist annotate -i sketch.json --auto-detect -o sketch_annotated.json

# Interactive annotation
pianist annotate -i sketch.json --interactive -o sketch_annotated.json
```

**Why:**
- Enables marking "great ideas"
- Enables specifying expansion points
- Foundation for intelligent expansion

---

### 3. Enhance `analyze` Command

**Purpose:** Analyze compositions (including incomplete JSON compositions)

**Proposed:**
```bash
# Analyze JSON composition (not just MIDI)
pianist analyze -i sketch.json -f json -o analysis.json

# Analyze and auto-annotate
pianist analyze -i sketch.json --annotate-intent -o sketch_annotated.json

# Analyze for expansion
pianist analyze -i sketch.json --for-expansion -o expansion_strategy.json
```

**Why:**
- Currently only works on MIDI files
- Need to analyze incomplete JSON compositions
- Need to identify "great ideas" automatically

---

### 4. Add `diff` Command (HIGH Priority)

**Purpose:** Show what changed between compositions

**Proposed:**
```bash
# Show changes
pianist diff sketch.json expanded.json

# Show musical diff (not just text)
pianist diff sketch.json expanded.json --musical

# Show what was preserved vs added
pianist diff sketch.json expanded.json --show-preserved
```

**Why:**
- Essential for understanding AI changes
- Helps validate expansion quality
- Enables feedback and refinement

---

### 5. Enhance `iterate` Command

**Keep for:** General modification workflows (transpose, fix, modify)

**Consider renaming to:** `modify` or keep as `iterate` but clarify it's for general modification

**Proposed:**
```bash
# Keep for general modifications
pianist iterate -i comp.json --transpose 2 -o transposed.json
pianist iterate -i comp.json --provider gemini --instructions "Make it faster" -o updated.json
```

---

## Proposed Command Structure

### Core Workflow Commands
1. **`generate`** - Create new composition (✅ exists)
2. **`annotate`** - Mark musical intent (❌ missing)
3. **`expand`** - Expand incomplete composition (❌ missing)
4. **`render`** - Convert to MIDI (✅ exists)

### Analysis & Understanding Commands
5. **`analyze`** - Analyze composition (✅ exists, needs enhancement)
6. **`diff`** - Show changes (❌ missing)

### Utility Commands
7. **`iterate`** - General modification (✅ exists, may rename)
8. **`fix-pedal`** - Fix pedal patterns (✅ exists)

---

## Ergonomics Assessment

### Current Strengths
- ✅ Consistent flag patterns (`-i`, `-o`, `--provider`, `--render`)
- ✅ Good output directory organization
- ✅ File versioning prevents overwrites
- ✅ Works with or without AI providers
- ✅ Supports stdin/stdout for piping

### Current Weaknesses
- ⚠️ No clear "expansion" workflow
- ⚠️ No way to mark musical intent
- ⚠️ Generic "iterate" command doesn't convey expansion intent
- ⚠️ No change tracking or diff
- ⚠️ No quality validation
- ⚠️ Instructions are free-form (no structured guidance)

### Missing for Core Goal
- ❌ `expand` command
- ❌ `annotate` command
- ❌ `diff` command
- ❌ Analysis of incomplete JSON compositions
- ❌ Automatic detection of "great ideas"
- ❌ Expansion-specific options

---

## Recommendations

### High Priority Changes

1. **Add `expand` command**
   - Clear intent for expansion workflow
   - Expansion-specific options
   - Integration with analysis and validation

2. **Add `annotate` command**
   - Mark musical intent
   - Enable AI to understand "great ideas"
   - Support manual and auto-detection

3. **Enhance `analyze` command**
   - Support JSON input (not just MIDI)
   - Analyze incomplete compositions
   - Auto-detect key ideas

4. **Add `diff` command**
   - Show what changed
   - Musical diff visualization
   - Track preservation

### Medium Priority Changes

5. **Consider renaming `iterate`**
   - To `modify` for clarity?
   - Or keep but clarify it's for general modification

6. **Enhance expansion options**
   - `--target-length` for expansion
   - `--preserve-motifs` flag
   - `--expand-section` option
   - `--development-strategy` option

### Low Priority Changes

7. **Improve help text**
   - Better descriptions of expansion workflow
   - Examples in help text
   - Workflow documentation

---

## Example: Ideal Workflow

### Current (Works but awkward)
```bash
# Create sketch
pianist generate --provider gemini "90 beats..." -o sketch.json

# Try to expand (unclear intent, no structure)
pianist iterate -i sketch.json --provider gemini \
  --instructions "Expand to 300 beats, preserve opening motif" \
  -o expanded.json
```

### Proposed (Clear and structured)
```bash
# Step 1: Create sketch
pianist generate --provider gemini "90 beats..." -o sketch.json

# Step 2: Annotate (mark great ideas)
pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening motif" --importance high \
  --mark-expansion "A" --target-length 120 \
  -o sketch_annotated.json

# Step 3: Expand (clear intent, structured)
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

---

## Summary

### Current State: 60% aligned with core goal

**What Works:**
- ✅ Basic workflow exists (generate → iterate → render)
- ✅ AI integration works
- ✅ Good file management

**What's Missing:**
- ❌ No `expand` command (critical)
- ❌ No `annotate` command (critical)
- ❌ No `diff` command (high priority)
- ❌ No analysis of incomplete JSON (high priority)
- ❌ No expansion-specific options (high priority)

### Recommendation

**Add three new commands:**
1. `expand` - For expansion workflow
2. `annotate` - For marking musical intent
3. `diff` - For change tracking

**Enhance existing commands:**
1. `analyze` - Support JSON input, analyze incomplete compositions
2. `iterate` - Keep for general modification, clarify purpose

This will align the CLI with the core goal of enabling rock solid human-AI collaboration for expansion.

