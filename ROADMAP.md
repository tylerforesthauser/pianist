# Pianist Roadmap

## Overview

This roadmap outlines the path to achieving the core goal: **rock solid human-AI collaboration where AI can understand, expand, and develop human musical ideas.**

**Current Achievement:** 85%  
**Target:** 100%

**Recent Progress:**
- ✅ Schema extensions implemented (`MusicalIntent`, `KeyIdea`, `ExpansionPoint`)
- ✅ CLI commands implemented (`annotate`, `expand`, `diff`)
- ✅ Annotation tools implemented (`annotations.py`)
- ✅ Command structure refined (import, modify, fix, etc.)
- ✅ Musical analysis module implemented (basic motif, phrase, harmony, form detection)
- ✅ Analysis integrated with `analyze` command (supports JSON input)
- ✅ Analysis integrated with `expand` command (enhanced prompts)
- ✅ Auto-detection implemented (`annotate --auto-detect`)
- ✅ music21 integration complete
- ✅ Analysis tests implemented
- 🔄 Expansion strategy module (placeholder created, implementation needed)
- 🔄 Validation module (placeholder created, implementation needed)

---

## 🎯 Next Steps (Immediate Priorities)

### 1. Implement Basic Musical Analysis ⚡ **CRITICAL PATH** ✅ **COMPLETE**
**Why:** Everything else depends on this - expansion prompts, auto-detection, and expansion strategies all need analysis.

**Status:** ✅ **COMPLETE**
- ✅ music21 library integrated
- ✅ Basic motif detection implemented (sliding window approach)
- ✅ Basic phrase detection implemented (gap-based heuristics)
- ✅ Basic harmonic analysis implemented (chord extraction)
- ✅ Basic form detection implemented (section marker counting)
- ✅ Tests written and passing
- ✅ Integrated with `analyze` command (supports JSON input)

**Next Steps:**
- Enhance analysis algorithms (see Phase 2 tasks)
- Improve accuracy and reduce false positives
- Add more sophisticated pattern matching

### 2. Enhance `analyze` Command ✅ **COMPLETE**
**Why:** Currently only works with MIDI files. Need JSON input support for analyzing compositions in Pianist format.

**Status:** ✅ **COMPLETE**
- ✅ JSON input support added
- ✅ Musical analysis module integrated
- ✅ Analysis results output in structured JSON format
- ✅ Tests updated

**Next Steps:**
- Enhance expansion analysis output format
- Add more analysis types as they're implemented

### 3. Enhance Expansion Prompts ✅ **COMPLETE**
**Why:** Current expansion prompts are basic. Need to include analysis results to guide AI better.

**Status:** ✅ **COMPLETE**
- ✅ `expand` command runs analysis before expansion
- ✅ Detected motifs, phrases, harmony included in expansion prompts
- ✅ Expansion suggestions from analysis included
- ✅ Graceful fallback if analysis fails

**Next Steps:**
- Test with real compositions and refine based on results
- Enhance prompt formatting and detail level

### 4. Implement Basic Auto-Detection ✅ **COMPLETE**
**Why:** Manual annotation is working, but auto-detection would make workflow smoother.

**Status:** ✅ **COMPLETE**
- ✅ `annotate --auto-detect` implemented
- ✅ Uses analysis module to detect motifs and phrases
- ✅ Automatically adds detected ideas as KeyIdea annotations
- ✅ Prevents duplicate annotations
- ✅ Tests written and passing

**Next Steps:**
- Test accuracy with real compositions
- Refine detection algorithms to improve accuracy
- Add more sophisticated auto-detection (harmonic progressions, etc.)

---

## Feature Priorities

### 1. Musical Intent & Annotation (CRITICAL)

**Why:** Without a way to mark "great ideas" and creative direction, AI can't know what to preserve or how to expand.

**Features:**
- Schema extensions for musical intent annotations
- Mark key ideas (motifs, phrases, harmonic progressions)
- Mark expansion points and directions
- Creative direction markers (where/how to expand, what to preserve)
- CLI annotation tools

**Implementation:**
- Extend `Composition` schema with `musical_intent` field
- Add models: `KeyIdea`, `ExpansionPoint`, `MusicalIntent`
- CLI commands: `annotate`, `mark-motif`, `mark-expansion`
- Auto-detection tools (future)

---

### 2. Musical Intelligence & Analysis (CRITICAL)

**Why:** AI needs to understand musical structure, motifs, and harmony to expand intelligently.

**Features:**
- Motif detection (recurring melodic/rhythmic patterns)
- Phrase analysis (musical phrases and structure)
- Harmonic analysis (chord progressions, functional harmony)
- Form detection (binary, ternary, sonata, etc.)
- Expansion strategy generation

**Implementation:**
- New module: `src/pianist/musical_analysis.py`
- Use music21 or similar for analysis
- Custom algorithms for pattern detection
- Integration with composition schema

---

### 3. Musical Reference Database (HIGH)

**Why:** AI needs examples of how motifs are developed, phrases expanded, transitions created.

**Features:**
- Example collections (motif development, phrase expansion, transitions, forms)
- Style-specific references (Baroque, Classical, Romantic, Modern)
- Technique examples (sequence, inversion, augmentation, diminution)
- Search and relevance ranking

**Implementation:**
- Database: SQLite or similar
- Storage: JSON compositions + metadata
- Search: Find relevant examples by pattern
- Integration: Include in AI prompts

---

### 4. Enhanced AI Expansion (CRITICAL)

**Why:** Need a reliable way for AI to expand incomplete compositions intelligently.

**Features:**
- `pianist expand` command
- Expansion workflow (analyze → strategy → references → prompt → validate)
- Enhanced prompt generation (include analysis, strategy, references)
- Target length specification
- Preservation requirements

**Implementation:**
- New command in CLI
- Integration with analysis module
- Integration with reference database
- Enhanced prompt templates

---

### 5. Quality Validation (HIGH)

**Why:** Need to ensure expansion is musically sound and preserves original intent.

**Features:**
- Motif preservation checking
- Development quality assessment
- Harmonic coherence validation
- Form consistency checking
- Style consistency validation
- Quality metrics and scoring

**Implementation:**
- Validation module: `src/pianist/validation.py`
- Quality metrics calculation
- Feedback generation
- Iterative refinement support

---

### 6. Collaboration Tools (MEDIUM)

**Why:** Help humans understand what AI changed and provide feedback.

**Features:**
- Change tracking (what was added vs. preserved)
- Diff visualization (musical diff, not just text)
- Feedback mechanisms (mark sections, guide direction)
- Iteration support

**Implementation:**
- Change detection algorithms
- Diff visualization tools
- Feedback command integration
- History tracking

---

## Implementation Roadmap

### Phase 1: Foundation
**Goal: Enable musical intent annotation and basic analysis**

**Status:** 🟢 **85% COMPLETE** - Core infrastructure done, basic analysis and auto-detection implemented

**Tasks:**
1. **Schema Extensions** ✅ **COMPLETE**
   - [x] Extend `Composition` schema with `musical_intent` field
   - [x] Add `KeyIdea`, `ExpansionPoint`, `MusicalIntent` models
   - [x] Update validation
   - [x] Update serialization

2. **Basic Analysis** ✅ **COMPLETE** (basic implementation)
   - [x] Implement motif detection
   - [x] Implement phrase detection
   - [x] Implement basic harmonic analysis
   - [x] Implement form detection

3. **CLI Improvements** ✅ **COMPLETE**
   - [x] Add `annotate` command for marking musical intent
   - [x] Add `expand` command for expansion workflow
   - [x] Add `diff` command for change tracking
   - [x] Enhance `analyze` to support JSON input and expansion analysis
   - [x] Improve command ergonomics and help text

4. **Annotation Tools** ✅ **COMPLETE**
   - [x] CLI annotation commands (`annotate`)
   - [x] Manual annotation support
   - [x] Auto-detection (basic) ✅ **COMPLETE**
   - [x] Documentation (basic)

5. **Enhanced Prompts** ✅ **COMPLETE** (basic integration)
   - [x] Include analysis in prompts ✅ **COMPLETE**
   - [x] Include expansion strategies ✅ **COMPLETE** (basic)
   - [x] Test with simple expansions (basic testing done)
   - [ ] Refine based on results (ongoing)

**Success Criteria:**
- [x] Schema supports musical intent annotations ✅ **COMPLETE**
- [x] Basic analysis works (motif, phrase, harmony) ✅ **COMPLETE**
- [x] `annotate` command works ✅ **COMPLETE**
- [x] `expand` command works ✅ **COMPLETE** (basic implementation)
- [x] `diff` command works ✅ **COMPLETE**
- [x] `analyze` supports JSON input ✅ **COMPLETE**
- [x] Simple expansions work (32 beats → 64 beats) ✅ **COMPLETE** (with analysis integration)
- [x] Enhanced prompts improve AI output ✅ **COMPLETE** (analysis integrated into expansion prompts)

**Expected Achievement: 75%** ✅ **EXCEEDED - 85% ACHIEVED**

---

### Phase 2: Intelligence Layer
**Goal: Build musical intelligence and reference database**

**Tasks:**
1. **Advanced Analysis**
   - Advanced harmonic analysis
   - Advanced form detection
   - Development strategy generation
   - Quality analysis

2. **Reference Database**
   - Database structure design
   - Example curation (100+ examples)
   - Search functionality
   - Integration with prompts

3. **Expansion Command Enhancement**
   - Enhance `pianist expand` command
   - Full expansion workflow
   - Strategy generation
   - Reference integration
   - Quality validation integration

4. **Validation**
   - Quality validation implementation
   - Preservation checking
   - Coherence checking
   - Metrics calculation

**Success Criteria:**
- [ ] Advanced analysis works
- [ ] Reference database exists (100+ examples)
- [ ] Expansion command works
- [ ] Complex expansions work (90s → 5min)
- [ ] Quality validation works

**Expected Achievement: 90%**

---

### Phase 3: Refinement
**Goal: Improve quality and reliability**

**Tasks:**
1. **Quality Improvement**
   - Refine analysis accuracy
   - Improve strategies
   - Enhance prompts
   - Better validation

2. **Collaboration Tools**
   - Enhance `diff` command with musical diff
   - Change tracking
   - Diff visualization improvements
   - Feedback mechanisms
   - Iteration support

3. **Testing & Refinement**
   - Test with real compositions
   - Gather feedback
   - Refine based on results
   - Improve documentation

**Success Criteria:**
- [ ] Quality is high (90%+)
- [ ] Collaboration tools work
- [ ] Results are satisfying (4.5+ satisfaction)
- [ ] Documentation is complete

**Expected Achievement: 100%**

---

## Technical Approach

### Schema Extensions

```python
class MusicalIntent(BaseModel):
    key_ideas: List[KeyIdea]
    expansion_points: List[ExpansionPoint]
    preserve: List[str]
    development_direction: str | None = None

class KeyIdea(BaseModel):
    id: str
    type: Literal["motif", "phrase", "harmonic_progression", "rhythmic_pattern"]
    start: float
    duration: float
    description: str
    importance: Literal["high", "medium", "low"]
    development_direction: str | None = None

class ExpansionPoint(BaseModel):
    section: str
    current_length: float
    suggested_length: float
    development_strategy: str
    preserve: List[str]
```

### Musical Analysis Module

```python
def analyze_composition(composition: Composition) -> MusicalAnalysis:
    return MusicalAnalysis(
        motifs=detect_motifs(composition),
        phrases=detect_phrases(composition),
        harmonic_progression=analyze_harmony(composition),
        form=detect_form(composition),
        key_ideas=identify_key_ideas(composition),
        expansion_suggestions=generate_expansion_strategies(composition)
    )
```

### Enhanced Prompt Generation

```python
def enhanced_expansion_prompt(
    comp: Composition,
    analysis: MusicalAnalysis,
    strategy: ExpansionStrategy,
    references: List[MusicalReference],
    instructions: str
) -> str:
    """Generate prompt with musical analysis and guidance"""
    # Include:
    # - Original composition JSON
    # - Musical analysis results
    # - Expansion strategy
    # - Musical references
    # - Music theory guidance
    # - Development techniques
    # - Preservation requirements
```

### Expansion Workflow

1. Analyze input composition (detect motifs, phrases, harmony, form)
2. Generate expansion strategy
3. Find relevant musical references
4. Generate enhanced prompt with analysis and references
5. Call AI with enhanced prompt
6. Validate expansion quality
7. Return result (or iterate if quality insufficient)

---

## Technical Dependencies

### Required Libraries
- **Music Theory**: music21, librosa (for analysis)
- **Pattern Detection**: Custom algorithms or existing libraries
- **Harmonic Analysis**: music21, custom algorithms
- **Form Detection**: Custom algorithms
- **Reference Database**: SQLite or similar for storage

### New Modules Needed
- `src/pianist/musical_analysis.py` - Analysis functions
- `src/pianist/reference_db.py` - Reference database
- `src/pianist/expansion_strategy.py` - Strategy generation
- `src/pianist/validation.py` - Quality validation
- `src/pianist/annotations.py` - Intent annotation tools

### Schema Extensions
- Extend `Composition` schema with `musical_intent` field
- Add annotation models (`KeyIdea`, `ExpansionPoint`, etc.)
- Add analysis result models (`MusicalAnalysis`, `ExpansionStrategy`)

---

## Example Workflow

### Step 1: Human Creates Incomplete Composition
```bash
./pianist generate "Title: Sketch
Form: ternary
Length: ~90 beats
Key: C major
Tempo: 120" -o sketch.json --render
```

### Step 2: Annotate Musical Intent
```bash
# Option A: Manual annotation
./pianist annotate -i sketch.json \
  --mark-motif "0-4" "Opening ascending motif" --importance high \
  --mark-expansion "section A" --target-length 120 \
  -o sketch_annotated.json

# Option B: Automatic annotation (future)
./pianist analyze -i sketch.json --annotate-intent -o sketch_annotated.json
```

### Step 3: AI Expansion
```bash
./pianist expand -i sketch_annotated.json \
  --target-length 300 \
  --preserve-motifs \
  --develop-sections \
  --provider gemini \
  -o expanded.json --render
```

**What happens internally:**
1. Analyze composition (detect motifs, phrases, harmony, form)
2. Generate expansion strategy
3. Find relevant musical references
4. Generate enhanced prompt with analysis and references
5. Call AI with enhanced prompt
6. Validate expansion quality
7. Return result

### Step 4: Review & Iterate
```bash
# See what changed
./pianist diff sketch.json expanded.json

# Refine if needed
./pianist expand -i expanded.json \
  --refine-section "B" \
  --provider gemini \
  -o expanded_v2.json
```

---

## Open Questions

1. **How to detect "great ideas"?**
   - Pattern recognition?
   - Harmonic significance?
   - User annotation?
   - Combination?

2. **How to build reference database?**
   - Curate from existing repertoire?
   - Generate examples?
   - User contributions?
   - Combination?

3. **How to validate musical quality?**
   - Rule-based?
   - Statistical?
   - User feedback?
   - Combination?

4. **How to balance preservation vs. development?**
   - Strict preservation?
   - Flexible development?
   - User-configurable?

These questions will be answered during implementation.

---

## Success Metrics

### Phase 1
- [ ] Schema supports annotations
- [ ] Basic analysis works (80%+ accuracy)
- [ ] Annotation tools work
- [ ] Simple expansions work

### Phase 2
- [ ] Advanced analysis works
- [ ] Reference database exists (100+ examples)
- [ ] Expansion command works
- [ ] Complex expansions work (90s → 5min)
- [ ] Quality validation works

### Phase 3
- [ ] Expansion preserves ideas (90%+)
- [ ] Development is musically sound (90%+)
- [ ] Results are satisfying (4.5+ satisfaction)
- [ ] Collaboration tools work
- [ ] Documentation is complete

---

## Getting Started: Implementation Guide

This section provides practical steps for implementing the roadmap, consolidating preparation tasks and implementation guidance.

### Current State

**Achievement:** 85% of Phase 1 complete

**What's Working:**
- ✅ JSON schema provides shared musical vocabulary
- ✅ Bidirectional conversion (JSON ↔ MIDI) works
- ✅ Schema extensions implemented (`MusicalIntent`, `KeyIdea`, `ExpansionPoint`)
- ✅ CLI commands implemented (`annotate`, `expand`, `diff`)
- ✅ Annotation tools implemented (`annotations.py`)
- ✅ Command structure refined (import, modify, fix, etc.)

**What's Missing (Critical Gaps):**
- 🟡 Expansion strategy module (placeholder exists, needs implementation)
- 🟡 Validation module (placeholder exists, needs implementation)
- 🟡 Enhanced prompts with analysis integration

### Implementation Order

#### Step 1: Implement Basic Musical Analysis ⚡ **CRITICAL PATH** ✅ **COMPLETE**
**Priority:** CRITICAL  
**Status:** ✅ **COMPLETE**

**Completed:**
1. ✅ Research and choose analysis library (music21)
2. ✅ Implement basic functions in `src/pianist/musical_analysis.py`:
   - `detect_motifs(composition)` - Sliding window approach
   - `detect_phrases(composition)` - Gap-based heuristics
   - `analyze_harmony(composition)` - Chord extraction
   - `detect_form(composition)` - Section marker counting
3. ✅ Write tests (all passing)
4. ✅ Integrate with `analyze` command (JSON input support added)

**Next Steps:**
- Enhance algorithms (see Phase 2)
- Improve accuracy and reduce false positives
- Add more sophisticated pattern matching

#### Step 2: Enhance `analyze` Command ✅ **COMPLETE**
**Priority:** HIGH  
**Status:** ✅ **COMPLETE**

**Completed:**
1. ✅ JSON input parsing added
2. ✅ Musical analysis module integrated
3. ✅ Analysis results output in structured JSON format
4. ✅ Tests updated

#### Step 3: Enhance Expansion Prompts
**Priority:** HIGH  
**Status:** Basic prompts exist, need analysis integration

**Tasks:**
1. Update `expand` command to run analysis before expansion
2. Include detected motifs, phrases, harmony in expansion prompts
3. Test with real compositions
4. Refine based on results

**Estimated Complexity:** Low-Medium  
**Dependencies:** Analysis module

#### Step 4: Implement Basic Auto-Detection
**Priority:** MEDIUM  
**Status:** Not started

**Tasks:**
1. Use analysis module to auto-detect key ideas
2. Implement `annotate --auto-detect` functionality
3. Test accuracy
4. Refine detection algorithms

**Estimated Complexity:** Medium  
**Dependencies:** Musical analysis module

### Dependencies & Infrastructure

#### Required Dependencies
- **Music Theory Library:** music21 (recommended) or alternative
- **Pattern Detection:** May need custom algorithms or additional libraries
- **Harmonic Analysis:** music21 provides this
- **Form Detection:** Custom algorithms or music21

**Action Items:**
- [x] Add music21 to `pyproject.toml` ✅ **COMPLETE**
- [x] Test dependency installation ✅ **COMPLETE**
- [x] Document dependencies ✅ **COMPLETE**

#### Module Structure
**Status:** Placeholder modules exist

- ✅ `src/pianist/musical_analysis.py` - ✅ **COMPLETE** (basic implementation)
- ✅ `src/pianist/annotations.py` - ✅ **COMPLETE**
- ✅ `src/pianist/expansion_strategy.py` - Placeholder exists, needs implementation
- ✅ `src/pianist/validation.py` - Placeholder exists, needs implementation

### Testing Infrastructure

#### Test Data Preparation
**Status:** Basic fixtures exist

- ✅ `tests/fixtures/incomplete_compositions/` - Directory exists
- ✅ `tests/fixtures/annotated_compositions/` - Directory exists
- [ ] Create test compositions with various structures
- [ ] Create compositions with clear motifs/phrases
- [ ] Document test data structure

#### Test Framework
**Status:** Test files exist

- ✅ `tests/test_musical_analysis.py` - ✅ **COMPLETE** (tests written and passing)
- ✅ `tests/test_annotations.py` - Not needed (annotations.py is complete)
- ✅ `tests/test_expansion_strategy.py` - Not yet created
- ✅ `tests/test_validation.py` - Not yet created

### Questions to Answer

Before beginning implementation, these questions should be answered:

1. **Analysis Library:**
   - Which library provides best balance of features and ease of use?
   - What are the licensing considerations?
   - What are the performance implications?
   - **Recommendation:** music21 (comprehensive, well-maintained, good documentation)

2. **Analysis Accuracy:**
   - How to test analysis accuracy?
   - What are acceptable accuracy thresholds?
   - How to handle edge cases?

3. **Integration:**
   - How to integrate analysis results into prompts?
   - What level of detail is needed?
   - How to handle analysis failures?

### Resources

- **Current Schema:** `src/pianist/schema.py`
- **Current Analysis:** `src/pianist/analyze.py` (MIDI analysis)
- **Current Iteration:** `src/pianist/iterate.py`
- **Musical Analysis Module:** `src/pianist/musical_analysis.py` (placeholder)
- **Mission:** [MISSION.md](MISSION.md)
- **Planning:** [PLANNING.md](PLANNING.md)

## Notes

- **Focus:** Build musical intelligence layer to enable AI to understand and expand human ideas
- **Priority:** Musical intent annotation ✅ **DONE**, musical intelligence 🔄 **IN PROGRESS**
- **Approach:** Phased implementation (foundation → intelligence → refinement)
- **Flexibility:** Roadmap will be revised based on learnings and feedback
- **Current Blocker:** Enhanced prompts with analysis integration
- **Start Here:** Enhance expansion prompts to include analysis results

