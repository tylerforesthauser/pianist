# Documentation Structure

This document outlines the planned documentation structure for Pianist. As functionality evolves, we'll flesh out these placeholders.

## Overview

Documentation is organized into:
- **Commands**: Individual command reference docs
- **Workflows**: End-to-end usage guides
- **Technical**: Deep dives, API references, technical details
- **Guides**: How-to guides for specific tasks
- **Reference**: Schema, configuration, etc.

## Directory Structure

```
docs/
├── commands/          # Individual command documentation
├── workflows/         # End-to-end workflow guides
├── technical/        # Technical deep dives
├── guides/           # How-to guides
├── reference/        # Reference materials
└── temp/             # Temporary/working docs (gitignored)
```

## Commands Documentation (`docs/commands/`)

Each command gets its own dedicated doc with:
- Purpose and use cases
- Syntax and options
- Examples
- Common patterns
- Tips and gotchas

### Command Docs (10 total)

1. **`generate.md`** - Generate new compositions
   - [ ] Purpose: Create new compositions from text descriptions
   - [ ] Options: --provider, --model, --render, etc.
   - [ ] Examples: Basic generation, with AI provider, without AI
   - [ ] Integration: How it works with AI_PROMPTING_GUIDE.md

2. **`import.md`** - Import MIDI to JSON
   - [ ] Purpose: Convert MIDI files to Pianist JSON format
   - [ ] Options: -i, -o
   - [ ] Examples: Basic import, handling multi-track files
   - [ ] Limitations: What gets preserved/lost in conversion

3. **`modify.md`** - Modify existing compositions
   - [ ] Purpose: Transpose, fix, or modify with AI
   - [ ] Options: --transpose, --provider, --instructions, etc.
   - [ ] Examples: Transposition, AI modification, prompt generation
   - [ ] Use cases: Iteration workflows

4. **`render.md`** - Render JSON to MIDI
   - [ ] Purpose: Convert JSON compositions to MIDI files
   - [ ] Options: -i, -o
   - [ ] Examples: Basic rendering, from stdin
   - [ ] Output format: MIDI file structure

5. **`analyze.md`** - Analyze compositions
   - [ ] Purpose: Analyze MIDI or JSON compositions
   - [ ] Options: -i, -f, --provider, etc.
   - [ ] Examples: MIDI analysis, JSON analysis, with AI generation
   - [ ] Analysis types: What gets analyzed (link to technical docs)
   - [ ] Link to: technical/analysis_technical_details.md

6. **`annotate.md`** - Mark musical intent
   - [ ] Purpose: Add key ideas, expansion points, etc.
   - [ ] Options: --key-idea, --expansion-point, --auto-detect
   - [ ] Examples: Manual annotation, auto-detection
   - [ ] Schema: MusicalIntent structure

7. **`expand.md`** - Expand incomplete compositions
   - [ ] Purpose: Grow short compositions into complete works
   - [ ] Options: --target-length, --provider, --preserve-motifs
   - [ ] Examples: Basic expansion, with AI, with annotations
   - [ ] Workflow: How it uses annotations

8. **`diff.md`** - Compare compositions
   - [ ] Purpose: Show differences between two compositions
   - [ ] Options: --format, --musical, --show-preserved
   - [ ] Examples: Text diff, JSON diff, markdown diff
   - [ ] Use cases: Version comparison, iteration tracking

9. **`fix.md`** - Fix composition issues
   - [ ] Purpose: Fix common issues (pedal patterns, etc.)
   - [ ] Options: --pedal, etc.
   - [ ] Examples: Fixing pedal patterns
   - [ ] Link to: guides/PEDAL_FIX_USAGE.md (existing)

10. **`reference.md`** - Manage reference database
   - [ ] Purpose: Add, list, search, and manage musical references
   - [ ] Options: add, list, search, get, delete, count
   - [ ] Examples: Adding references, searching by style/form
   - [ ] Integration: How it works with batch import scripts

## Workflows Documentation (`docs/workflows/`)

End-to-end guides for common use cases.

1. **`ai_human_collaboration.md`** - AI-Human collaboration patterns
   - [ ] Overview: Bidirectional workflows
   - [ ] AI → Human: Generate, refine in DAW
   - [ ] Human → AI: Export, expand with AI
   - [ ] Iteration cycles

2. **`expanding_incomplete_compositions.md`** - Expanding sketches
   - [ ] Use case: 90-second sketch → 5-minute piece
   - [ ] Workflow: Annotate → Expand → Refine
   - [ ] Best practices: What to annotate, how to guide expansion
   - [ ] Examples: Real-world expansion scenarios

3. **`midi_analysis_generation.md`** - MIDI analysis workflow
   - [ ] Use case: Analyze existing MIDI, generate new composition
   - [ ] Workflow: Import → Analyze → Generate
   - [ ] With/without AI provider
   - [ ] Examples: Style transfer, inspiration

4. **`composition_iteration.md`** - Iterative refinement
   - [ ] Use case: Refine compositions through multiple versions
   - [ ] Workflow: Generate → Modify → Diff → Refine
   - [ ] Version management: Using output directory structure
   - [ ] Examples: Transposition, style changes, expansion

5. **`manual_composition.md`** - Manual composition workflow
   - [ ] Use case: Create JSON manually, no AI
   - [ ] Workflow: Write JSON → Render → Refine
   - [ ] Schema reference: Link to reference/schema.md
   - [ ] Examples: Simple compositions, complex structures

## Technical Documentation (`docs/technical/`)

Deep dives into how things work.

1. **`analysis_technical_details.md`** ✅ (exists in technical/)
   - [x] How motif detection works
   - [x] How phrase detection works
   - [x] How harmonic analysis works
   - [x] Limitations and expectations
   - [x] Move from temp/ to technical/ ✅

2. **`schema_reference.md`** - Complete schema documentation
   - [ ] Composition structure
   - [ ] Event types (NoteEvent, PedalEvent, etc.)
   - [ ] MusicalIntent structure
   - [ ] Validation rules
   - [ ] Examples for each type

3. **`midi_conversion.md`** - MIDI conversion details
   - [ ] How JSON maps to MIDI
   - [ ] What gets preserved/lost
   - [ ] PPQ handling
   - [ ] Tempo changes
   - [ ] Multi-track handling

4. **`ai_integration.md`** - AI provider integration
   - [ ] How providers work
   - [ ] Prompt templates
   - [ ] Response parsing
   - [ ] Error handling
   - [ ] Caching

5. **`output_directory_structure.md`** - File organization
   - [ ] How output directories work
   - [ ] Base name derivation
   - [ ] Version management
   - [ ] Cross-command workflows

## Guides (`docs/guides/`)

How-to guides for specific tasks.

1. **`getting_started.md`** - Quick start guide
   - [ ] Installation
   - [ ] First composition
   - [ ] Basic workflows
   - [ ] Next steps

2. **`ai_prompting.md`** ✅ (exists as AI_PROMPTING_GUIDE.md)
   - [x] System prompts
   - [x] User prompts
   - [x] Examples
   - [ ] Move to guides/ or keep at root?

3. **`testing_analysis.md`** ✅ (exists in guides/)
   - [x] How to test analysis
   - [x] Aural comparison
   - [x] Evaluation strategies
   - [x] Move from temp/ to guides/ ✅

4. **`API_KEY_MANAGEMENT.md`** ✅ (exists in guides/)
   - [x] How to set up API keys
   - [x] Move to guides/ ✅

5. **`PEDAL_FIX_USAGE.md`** ✅ (exists in guides/)
   - [x] How to use pedal fix
   - [x] Move to guides/ ✅

## Reference Documentation (`docs/reference/`)

Quick reference materials.

1. **`command_reference.md`** - Quick command reference
   - [ ] All commands in one place
   - [ ] Common options
   - [ ] Quick examples

2. **`schema_quick_reference.md`** - Schema cheat sheet
   - [ ] Common patterns
   - [ ] Event type quick reference
   - [ ] Examples

3. **`file_formats.md`** - Supported formats
   - [ ] JSON format
   - [ ] MIDI format
   - [ ] Conversion details

## Root-Level Documentation

These stay at the root for discoverability:

- **`README.md`** ✅ - Main entry point, overview, quick start
- **`MISSION.md`** ✅ - Project mission and goals
- **`ROADMAP.md`** ✅ - Feature roadmap
- **`PLANNING.md`** ✅ - Planning document guide
- **`AI_PROMPTING_GUIDE.md`** ✅ - AI prompting (consider moving to guides/)

## Migration Plan

### Phase 1: Organize Existing Docs
- [x] Move `docs/temp/analysis_technical_details.md` → `docs/technical/` ✅ (already in technical/)
- [x] Move `docs/temp/testing_musical_analysis.md` → `docs/guides/` ✅ (consolidated into guides/testing_analysis.md)
- [x] Move `docs/PEDAL_FIX_USAGE.md` → `docs/guides/` ✅ (duplicate removed, guides/ version kept)
- [x] Move `docs/API_KEY_MANAGEMENT.md` → `docs/guides/` ✅ (duplicate removed, guides/ version kept)
- [x] Keep `docs/INTEGRATION_TESTING.md` in docs/ (testing-specific) ✅

### Phase 2: Create Command Placeholders
- [x] Create all 10 command docs with basic structure ✅
- [x] Add links from README.md ✅
- [ ] Document existing functionality (many are still placeholders)

### Phase 3: Create Workflow Placeholders
- [ ] Create all 5 workflow docs with outlines
- [ ] Add examples from existing README
- [ ] Link between related docs

### Phase 4: Flesh Out Documentation
- [ ] Complete command docs as features stabilize
- [ ] Complete workflow docs with real examples
- [ ] Add cross-references between docs

## Documentation Principles

1. **One doc per command** - Easy to find, easy to maintain
2. **Workflows over features** - Show how to accomplish goals
3. **Examples over explanations** - Show, don't just tell
4. **Link liberally** - Connect related concepts
5. **Keep temp/ for drafts** - Use docs/temp/ for work in progress
6. **Update with code** - Docs should evolve with features

## Maintenance

- Update command docs when commands change
- Update workflow docs when workflows change
- Keep technical docs in sync with implementation
- Review and consolidate temp/ docs regularly
- Remove outdated docs promptly

