# Pianist Roadmap

## Overview

This roadmap outlines the path to achieving the core goal: **rock solid human-AI collaboration where AI can understand, expand, and develop human musical ideas.**

**Current Achievement:** 60%  
**Target:** 100%

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

**Tasks:**
1. **Schema Extensions**
   - Extend `Composition` schema with `musical_intent` field
   - Add `KeyIdea`, `ExpansionPoint`, `MusicalIntent` models
   - Update validation
   - Update serialization

2. **Basic Analysis**
   - Implement motif detection
   - Implement phrase detection
   - Implement basic harmonic analysis
   - Implement form detection

3. **Annotation Tools**
   - CLI annotation commands
   - Manual annotation support
   - Auto-detection (basic)
   - Documentation

4. **Enhanced Prompts**
   - Include analysis in prompts
   - Include expansion strategies
   - Test with simple expansions
   - Refine based on results

**Success Criteria:**
- [ ] Schema supports musical intent annotations
- [ ] Basic analysis works (motif, phrase, harmony)
- [ ] `annotate` command works
- [ ] `expand` command works
- [ ] `diff` command works
- [ ] `analyze` supports JSON input
- [ ] Simple expansions work (32 beats → 64 beats)
- [ ] Enhanced prompts improve AI output

**Expected Achievement: 75%**

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

## Notes

- **Focus:** Build musical intelligence layer to enable AI to understand and expand human ideas
- **Priority:** Musical intent annotation and musical intelligence are critical
- **Approach:** Phased implementation (foundation → intelligence → refinement)
- **Flexibility:** Roadmap will be revised based on learnings and feedback

