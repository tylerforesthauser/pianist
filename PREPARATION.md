# Project Preparation: Beginning the Roadmap

This document outlines the steps needed to prepare the project for implementing the roadmap outlined in [ROADMAP.md](ROADMAP.md).

## Current State

**Achievement:** 60% of core goal

**What's Working:**
- ✅ JSON schema provides shared musical vocabulary
- ✅ Bidirectional conversion (JSON ↔ MIDI) works
- ✅ Basic iteration commands exist
- ✅ AI integration (Gemini) works

**What's Missing (Critical Gaps):**
- 🔴 Musical intent annotation (no way to mark "great ideas")
- 🔴 Musical intelligence (AI lacks music theory knowledge)
- 🔴 Expansion strategies (no intelligent expansion)
- 🔴 Quality validation (no validation of expansion)

## Phase 1 Preparation

### 1. Research & Design

#### 1.1 Schema Extensions Design
**Tasks:**
- [ ] Review current `Composition` schema in `src/pianist/schema.py`
- [ ] Design `MusicalIntent` model structure
- [ ] Design `KeyIdea` model (motif, phrase, harmonic progression, etc.)
- [ ] Design `ExpansionPoint` model (where/how to expand)
- [ ] Design backward compatibility strategy
- [ ] Document schema extensions

**Deliverables:**
- Schema design document (or section in ROADMAP.md)
- Example JSON with annotations
- Migration strategy for existing compositions

#### 1.2 Musical Analysis Research
**Tasks:**
- [ ] Research music theory libraries (music21, librosa, etc.)
- [ ] Evaluate motif detection algorithms
- [ ] Evaluate phrase detection approaches
- [ ] Evaluate harmonic analysis libraries
- [ ] Evaluate form detection methods
- [ ] Choose primary library/approach

**Deliverables:**
- Library evaluation document
- Decision on primary analysis library
- List of required dependencies

#### 1.3 Annotation Tools Design
**Tasks:**
- [ ] Design CLI annotation commands
- [ ] Design annotation workflow
- [ ] Design auto-detection approach (future)
- [ ] Design annotation file format

**Deliverables:**
- CLI command design
- Workflow documentation
- Example usage

### 2. Dependencies & Infrastructure

#### 2.1 Add Required Dependencies
**Tasks:**
- [ ] Add music theory library to `pyproject.toml` (e.g., music21)
- [ ] Add any pattern detection libraries if needed
- [ ] Update dependency versions
- [ ] Test dependency installation

**Files to Update:**
- `pyproject.toml`

#### 2.2 Create New Modules Structure
**Tasks:**
- [ ] Create `src/pianist/musical_analysis.py` (placeholder)
- [ ] Create `src/pianist/annotations.py` (placeholder)
- [ ] Create `src/pianist/expansion_strategy.py` (placeholder)
- [ ] Create `src/pianist/validation.py` (placeholder)
- [ ] Add module docstrings and structure

**Files to Create:**
- `src/pianist/musical_analysis.py`
- `src/pianist/annotations.py`
- `src/pianist/expansion_strategy.py`
- `src/pianist/validation.py`

### 3. Testing Infrastructure

#### 3.1 Test Data Preparation
**Tasks:**
- [ ] Create test compositions with various structures
- [ ] Create incomplete compositions for expansion testing
- [ ] Create compositions with clear motifs/phrases
- [ ] Document test data structure

**Files to Create:**
- `tests/fixtures/incomplete_compositions/`
- `tests/fixtures/annotated_compositions/`
- Test data documentation

#### 3.2 Test Framework Setup
**Tasks:**
- [ ] Design test structure for new modules
- [ ] Create test fixtures for analysis
- [ ] Create test fixtures for annotations
- [ ] Create test fixtures for expansion

**Files to Create:**
- `tests/test_musical_analysis.py`
- `tests/test_annotations.py`
- `tests/test_expansion_strategy.py`
- `tests/test_validation.py`

### 4. Documentation Updates

#### 4.1 Update Existing Documentation
**Tasks:**
- [ ] Update README with new mission/goals (✅ Done)
- [ ] Update AI_PROMPTING_GUIDE.md if needed
- [ ] Update any API documentation
- [ ] Add examples of future workflows

#### 4.2 Create New Documentation
**Tasks:**
- [ ] Document schema extensions
- [ ] Document annotation workflow
- [ ] Document analysis capabilities
- [ ] Create examples of annotated compositions

## Implementation Order

### Step 1: Schema Extensions (Foundation)
**Priority: CRITICAL**

1. Design and implement `MusicalIntent` models
2. Extend `Composition` schema
3. Update validation
4. Update serialization
5. Write tests
6. Update documentation

**Estimated Complexity:** Medium
**Dependencies:** None

### Step 2: Basic Analysis (Foundation)
**Priority: CRITICAL**

1. Set up musical analysis module
2. Implement basic motif detection
3. Implement basic phrase detection
4. Implement basic harmonic analysis
5. Implement basic form detection
6. Write tests
7. Update documentation

**Estimated Complexity:** High
**Dependencies:** Music theory library

### Step 3: Annotation Tools (Foundation)
**Priority: HIGH**

1. Implement CLI annotation commands
2. Implement manual annotation support
3. Implement annotation serialization
4. Write tests
5. Update documentation

**Estimated Complexity:** Medium
**Dependencies:** Schema extensions

### Step 4: Enhanced Prompts (Foundation)
**Priority: HIGH**

1. Update prompt templates to include analysis
2. Update prompt templates to include annotations
3. Test with simple expansions
4. Refine based on results
5. Update documentation

**Estimated Complexity:** Low-Medium
**Dependencies:** Analysis module, annotations

## Getting Started Checklist

### Immediate Next Steps

- [ ] **Review and finalize schema design**
  - Review current schema in `src/pianist/schema.py`
  - Design `MusicalIntent` models
  - Create example JSON with annotations
  - Get feedback/approval

- [ ] **Research and choose analysis library**
  - Evaluate music21, librosa, and alternatives
  - Test basic functionality
  - Make decision
  - Add to dependencies

- [ ] **Set up new module structure**
  - Create placeholder modules
  - Add basic structure and docstrings
  - Set up imports

- [ ] **Prepare test infrastructure**
  - Create test data directories
  - Set up test fixtures
  - Create test file structure

### Before Starting Implementation

- [ ] Schema design is finalized
- [ ] Analysis library is chosen and added
- [ ] Module structure is created
- [ ] Test infrastructure is ready
- [ ] Team is aligned on approach

## Questions to Answer

Before beginning implementation, these questions should be answered:

1. **Schema Design:**
   - How should annotations be structured?
   - Should annotations be optional or required?
   - How to handle backward compatibility?

2. **Analysis Library:**
   - Which library provides best balance of features and ease of use?
   - What are the licensing considerations?
   - What are the performance implications?

3. **Annotation Workflow:**
   - Should annotations be manual, automatic, or both?
   - How should users mark "great ideas"?
   - What's the best UX for annotation?

4. **Testing Strategy:**
   - What test data is needed?
   - How to test analysis accuracy?
   - How to test expansion quality?

## Resources

- **Current Schema:** `src/pianist/schema.py`
- **Current Analysis:** `src/pianist/analyze.py` (MIDI analysis)
- **Current Iteration:** `src/pianist/iterate.py`
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Mission:** [MISSION.md](MISSION.md)

## Notes

- Start with schema extensions - everything else depends on this
- Analysis library choice is critical - research thoroughly
- Test infrastructure should be set up early
- Keep backward compatibility in mind
- Document decisions as you go

