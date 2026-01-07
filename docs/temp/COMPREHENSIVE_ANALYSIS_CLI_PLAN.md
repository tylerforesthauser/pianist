# Plan: Comprehensive Analysis CLI Command

## Executive Summary

**Enhance the existing `analyze` command** to provide comprehensive analysis of individual compositions (.mid or .json files), similar to what `review_and_categorize_midi.py` does for batch processing. 

**Key Decision**: Enhance `analyze` directly (no flag needed) because:
- Current MIDI analysis is quite basic (just statistics, no quality scores, no musical analysis)
- Current JSON analysis is better but still missing quality scores
- Users expect thorough analysis when they run `analyze`
- No backward compatibility concerns (user confirmed)

This will provide users with detailed quality assessment, musical analysis, and improvement suggestions for single files by default.

**Important Distinction**: This enhancement focuses on **user-focused analysis** (understanding and improving compositions), NOT **database curation analysis** (filtering and categorizing for database import). The two use cases share core analysis functions but have different outputs and purposes.

## Two Distinct Analysis Use Cases

### 1. Reference Database Curation Analysis
**Purpose**: Curate files for the reference database  
**Tool**: `review_and_categorize_midi.py` (batch processing)  
**Audience**: Database curators  
**Focus**: Quality filtering, categorization, metadata for storage

**Key Features:**
- ✅ Quality scores (technical, musical, structure) - **to filter unsuitable files**
- ✅ Duplicate detection - **to avoid duplicates in database**
- ✅ Suggested names/IDs - **for database organization**
- ✅ Style/form classification - **for database categorization**
- ✅ Is original flag - **to exclude originals from database**
- ✅ Suitability recommendations - **should this go in the database?**
- ✅ Similarity scores - **for duplicate grouping**

**Output**: CSV/JSON reports for batch import, normalization, and curation decisions

### 2. User-Focused Analysis
**Purpose**: Help users understand and work with their compositions  
**Tool**: `pianist analyze` command (single file)  
**Audience**: Composers, users working with their own compositions  
**Focus**: Musical insights, workflow integration, composition development

**Key Features:**
- ✅ Musical analysis (motifs, phrases, harmony, form) - **to understand the piece**
- ✅ Quality assessment - **to identify issues for improvement** (not filtering)
- ✅ Musical characteristics (key, tempo, structure) - **for understanding**
- ✅ Suggestions for improvement - **how to make it better**
- ✅ Expansion/modification guidance - **how to develop the piece**
- ✅ Prompt generation - **for AI workflows**
- ❌ Duplicate detection - **NOT needed** (user is analyzing their own work)
- ❌ Suggested names/IDs - **NOT needed** (user knows their composition)
- ❌ Suitability for database - **NOT needed** (not curating)

**Output**: JSON analysis, prompt templates, improvement suggestions

### Overlap and Differences

**Shared Analysis (Both Need):**
- Quality scores (technical, musical, structure) - but different focus
- Musical analysis (motifs, phrases, harmony, form) - same data, different presentation
- Technical metadata (duration, tempo, time/key signatures, tracks)

**Database-Specific (Curation Only):**
- Duplicate detection and similarity scores
- Suggested names, IDs, styles, descriptions
- Is original flag
- Suitability recommendations
- Similar files list

**User-Specific (Workflow Only):**
- Improvement suggestions (how to fix issues)
- Expansion/modification guidance
- Prompt generation for AI workflows
- Workflow integration (expand, modify, etc.)

## Value Proposition

### Current State
- **`pianist analyze`**: Provides musical analysis (motifs, phrases, harmony, form) focused on expansion/generation workflows, but missing quality assessment and improvement guidance
- **`review_and_categorize_midi.py`**: Comprehensive batch analysis for curation (quality scores, naming, metadata collection, duplicate detection)
- **Gap**: Users can't get quality assessment and improvement suggestions for their own compositions

### Benefits
1. **User Workflow**: Users can assess quality and get improvement suggestions for their compositions
2. **Composition Understanding**: Get detailed insights about any composition
3. **Workflow Integration**: Quality assessment feeds into expand/modify workflows
4. **Clear Separation**: Database curation analysis remains separate from user analysis
5. **Focused Output**: User analysis focuses on insights and improvement, not curation metadata

## Proposed Solution

### Direct Enhancement of `analyze` Command (Recommended)

**Current State:**
- For MIDI: Basic MIDI statistics (duration, tempo, tracks, pitch distributions) - quite minimal
- For JSON: Musical analysis (motifs, phrases, harmony, form) - more detailed but still missing quality scores
- **Missing**: Quality assessment, suggested metadata, recommendations

**Decision: Enhance `analyze` directly**

Since the current `analyze` command output is relatively basic (especially for MIDI files), we should enhance it directly to always provide comprehensive analysis. No flag needed - just make it better by default.

**Pros:**
- Simpler API (no flags to remember)
- Always get the best analysis
- Consistent behavior for MIDI and JSON
- No backward compatibility concerns (user said no need to maintain it)

**Cons:**
- Slightly slower (quality checking, music21 analysis) - but analysis should be thorough anyway
- Requires music21 for full analysis (but it's already a dependency for JSON analysis)

## Feature Specification

### Command Syntax

```bash
# Comprehensive analysis (enhanced default behavior)
pianist analyze -i composition.mid

# With output file
pianist analyze -i composition.mid -o analysis.json

# With AI-assisted naming (optional)
pianist analyze -i composition.mid --ai-naming

# For JSON files (also comprehensive)
pianist analyze -i composition.json -o analysis.json

# Still supports prompt generation (existing behavior)
pianist analyze -i composition.mid --format prompt
```

### Analysis Output (User-Focused)

The enhanced `analyze` command output includes:

#### 1. Quality Assessment
- **Overall quality score** (0.0-1.0)
- **Technical score** (MIDI quality, timing, structure)
- **Musical score** (musical coherence, voice leading)
- **Structure score** (form, balance, development)
- **Quality issues** (list of specific problems found)

#### 2. Technical Metadata
- Duration (beats, seconds, bars)
- Tempo (BPM)
- Time signature
- Key signature
- Number of tracks
- File size, format info

#### 3. Musical Analysis
- **Detected key** (from harmonic analysis)
- **Detected form** (binary, ternary, sonata, etc.)
- **Motif count** and details
- **Phrase count** and details
- **Chord count** and progression
- **Harmonic progression** (first 10 chords)
- **Cadences** detected

#### 4. Improvement Suggestions
- **Issues to fix** (specific problems found)
- **Suggestions for improvement** (how to enhance the composition)
- **Quality recommendations** (actionable advice)

**Note**: We do NOT include:
- Duplicate detection (not relevant for user's own work)
- Suggested names/IDs (user knows their composition)
- Suitability for database (not curating)
- Similar files list (not needed for single-file analysis)

#### 5. Optional: AI-Assisted Insights (with `--ai-naming`)
- **Suggested name** (AI-generated, for reference)
- **Suggested style** (Baroque, Classical, Romantic, Modern)
- **Suggested description** (AI-generated description)

### Output Formats

#### JSON Output (Default with `--comprehensive`)
```json
{
  "filename": "composition.mid",
  "filepath": "/path/to/composition.mid",
  "quality": {
    "overall_score": 0.85,
    "technical_score": 0.90,
    "musical_score": 0.80,
    "structure_score": 0.85,
    "issues": [
      "Pedal events with duration=0",
      "Sparse velocity variation"
    ]
  },
  "technical": {
    "duration_beats": 128.0,
    "duration_seconds": 45.2,
    "bars": 32.0,
    "tempo_bpm": 120.0,
    "time_signature": "4/4",
    "key_signature": "C major",
    "tracks": 1
  },
  "musical_analysis": {
    "detected_key": "C major",
    "detected_form": "ternary",
    "motif_count": 3,
    "phrase_count": 4,
    "chord_count": 32,
    "harmonic_progression": "I V vi IV I V I",
    "motifs": [...],
    "phrases": [...],
    "harmony": {...}
  },
  "improvement_suggestions": {
    "issues_to_fix": [
      {
        "issue": "Pedal events with duration=0",
        "severity": "low",
        "suggestion": "Review pedal timing - some events may be incorrectly encoded"
      },
      {
        "issue": "Sparse velocity variation",
        "severity": "medium",
        "suggestion": "Add more dynamic contrast for musical expression"
      }
    ],
    "improvements": [
      "Consider adding more harmonic variety in the middle section",
      "Motif development could be more varied"
    ],
    "quality_recommendations": [
      "Overall quality is good - composition is well-structured",
      "Technical execution is solid"
    ]
  },
  "ai_insights": {
    "suggested_name": "C major Ternary",
    "suggested_style": "Classical",
    "suggested_description": "Ternary form composition in C major with 3 motifs"
  }
}
```

#### Human-Readable Output (with `--format text`)
```
Composition Analysis: composition.mid
=====================================

Quality Assessment
------------------
Overall Score: 0.85 (Good)
  Technical:  0.90 (Excellent)
  Musical:    0.80 (Good)
  Structure:  0.85 (Good)

Issues Found: 2
  - Pedal events with duration=0
  - Sparse velocity variation

Technical Metadata
------------------
Duration: 128.0 beats (45.2 seconds, 32.0 bars)
Tempo: 120.0 BPM
Time Signature: 4/4
Key Signature: C major
Tracks: 1

Musical Analysis
----------------
Key: C major
Form: ternary
Motifs: 3 detected
Phrases: 4 detected
Chords: 32 detected
Harmonic Progression: I V vi IV I V I

Improvement Suggestions
-----------------------
Issues to Fix:
  - Pedal events with duration=0 (low severity)
    → Review pedal timing - some events may be incorrectly encoded
  - Sparse velocity variation (medium severity)
    → Add more dynamic contrast for musical expression

Improvements:
  - Consider adding more harmonic variety in the middle section
  - Motif development could be more varied

Quality Recommendations:
  - Overall quality is good - composition is well-structured
  - Technical execution is solid

AI Insights (optional, with --ai-naming)
----------------------------------------
Suggested Name: C major Ternary
Suggested Style: Classical
Suggested Description: Ternary form composition in C major with 3 motifs
```

## Implementation Plan

### Phase 1: Core Analysis Integration
1. **Extract shared analysis functions** from `review_and_categorize_midi.py`:
   - Quality checking (technical, musical, structure scores)
   - Musical analysis (motifs, phrases, harmony, form)
   - Technical metadata extraction

2. **Create shared analysis module** (`src/pianist/comprehensive_analysis.py`):
   - Reusable functions for both CLI and batch script
   - Single source of truth for core analysis logic
   - Clean API for analysis operations
   - Functions:
     - `analyze_quality(file_path)` - Quality assessment
     - `analyze_musical(composition)` - Musical analysis
     - `extract_technical_metadata(midi_analysis)` - Technical metadata

3. **Create user-focused analysis function**:
   - `analyze_for_user(file_path, use_ai_insights=False)` - User-focused analysis
   - Includes: quality, musical analysis, improvement suggestions
   - Excludes: duplicate detection, suggested names/IDs, suitability

4. **Enhance `analyze` command**:
   - Replace basic MIDI analysis with user-focused comprehensive analysis
   - Add `--ai-naming` flag (optional AI-assisted insights)
   - Enhance JSON analysis to include quality scores and improvement suggestions
   - Always provide comprehensive output (no flag needed)

### Phase 2: Output Formatting
1. **JSON output** (default):
   - Structured JSON with all analysis data
   - Compatible with batch script output format
   - Easy to parse programmatically
   - Always includes quality, technical, musical analysis

2. **Text output** (optional):
   - Human-readable formatted output
   - Clear sections and hierarchy
   - Use `--format text` for human-readable output

3. **Prompt format** (existing):
   - Still supports `--format prompt` for prompt generation
   - Uses comprehensive analysis data for better prompts

### Phase 3: AI Integration (Optional)
1. **AI-assisted naming**:
   - Use existing `identify_composition_with_ai()` function
   - Optional `--ai-naming` flag
   - Support for `--ai-provider` and `--ai-model` flags

2. **AI quality assessment**:
   - Optional AI-based quality feedback
   - More nuanced quality recommendations

### Phase 4: Refactoring (Cleanup)
1. **Refactor `review_and_categorize_midi.py`**:
   - Use shared `comprehensive_analysis.py` module
   - Reduce code duplication
   - Maintain backward compatibility

2. **Update documentation**:
   - Update `analyze.md` command docs
   - Add examples for comprehensive mode
   - Update README with new capabilities

## Technical Details

### New Dependencies
- None (uses existing dependencies)

### Code Organization

```
src/pianist/
  ├── comprehensive_analysis.py  # NEW: Shared analysis functions
  ├── cli/
  │   └── commands/
  │       └── analyze.py         # MODIFY: Add comprehensive mode
  └── ...

scripts/
  └── review_and_categorize_midi.py  # REFACTOR: Use shared module
```

### Key Functions to Extract/Create

1. **Shared Analysis Functions** (in `comprehensive_analysis.py`):
   - `analyze_quality(file_path)` - Quality assessment (technical, musical, structure)
   - `analyze_musical(composition)` - Musical analysis (motifs, phrases, harmony, form)
   - `extract_technical_metadata(midi_analysis)` - Technical metadata extraction

2. **User-Focused Analysis** (in `comprehensive_analysis.py`):
   - `analyze_for_user(file_path, use_ai_insights=False)`:
     - Takes file path (MIDI or JSON)
     - Returns user-focused analysis dict
     - Includes: quality, musical analysis, improvement suggestions
     - Excludes: duplicate detection, suggested names/IDs, suitability

3. **Output Formatting** (in `analyze.py` command):
   - `format_user_analysis_json()` - Formats user analysis as JSON
   - `format_user_analysis_text()` - Formats user analysis as human-readable text
   - Different from batch script output (no curation metadata)

### Integration Points

1. **Quality Checking**:
   - Use existing `check_midi_quality.py` functions
   - Already integrated in review script

2. **Musical Analysis**:
   - Use existing `musical_analysis.py` functions
   - Already used in current `analyze` command

3. **AI Naming**:
   - Use existing `identify_composition_with_ai()` from review script
   - Optional feature, doesn't block core functionality

## Usage Examples

### Basic Comprehensive Analysis
```bash
# Analyze MIDI file (comprehensive by default)
pianist analyze -i piece.mid -o analysis.json

# Analyze JSON file (comprehensive by default)
pianist analyze -i composition.json

# Human-readable output
pianist analyze -i piece.mid --format text
```

### With AI-Assisted Naming
```bash
# Get AI-generated name and description
pianist analyze -i piece.mid --ai-naming

# Use specific AI provider
pianist analyze -i piece.mid --ai-naming --ai-provider gemini
```

### Quality Assessment
```bash
# Check quality scores
pianist analyze -i composition.mid | jq '.quality.overall_score'

# Get improvement suggestions
pianist analyze -i composition.mid | jq '.improvement_suggestions.issues_to_fix'
```

### Prompt Generation (Existing Feature)
```bash
# Generate prompt template (still works, now uses comprehensive analysis)
pianist analyze -i piece.mid --format prompt
```

### Integration in Scripts
```bash
#!/bin/bash
# Analyze all MIDI files in directory
for file in *.mid; do
  pianist analyze -i "$file" --comprehensive -o "${file%.mid}_analysis.json"
done
```

## Success Criteria

1. ✅ Single-file user-focused analysis works for both MIDI and JSON
2. ✅ Output format is user-focused (improvement suggestions, not curation metadata)
3. ✅ Quality scores and improvement recommendations are accurate
4. ✅ AI insights are optional and work when enabled
5. ✅ Code is shared between CLI and batch script (core analysis functions)
6. ✅ Clear separation: user analysis vs. database curation analysis
7. ✅ Documentation is updated with examples
8. ✅ Enhanced by default (no flags needed for comprehensive analysis)
9. ✅ Existing prompt generation still works
10. ✅ No duplicate detection or curation metadata in user analysis output

## Future Enhancements

1. **Comparison Mode**: Compare two compositions side-by-side
2. **Batch Mode**: Analyze multiple files at once (via glob patterns)
3. **Export to CSV**: Export analysis results to CSV format
4. **Quality Thresholds**: Configurable quality thresholds for recommendations
5. **Visual Output**: Generate visualizations (form diagrams, harmonic progressions)
6. **Integration with Reference DB**: Auto-suggest adding to database if quality is high

## Open Questions

1. **Enhancement Approach**: Should we enhance `analyze` directly or use a flag?
   - **Decision**: Enhance directly - current output is basic, comprehensive is better default

2. **Default Format**: Should analysis default to JSON or text?
   - **Decision**: Default to JSON (structured, parseable), text with `--format text`

3. **AI Naming Default**: Should AI naming be on by default or opt-in?
   - **Decision**: Opt-in with `--ai-naming` flag (AI calls can be slow/expensive)

4. **Output Location**: Should analysis always write to file or allow stdout?
   - **Decision**: Allow both (stdout if no `-o`, file if `-o` provided) - maintain existing behavior

## Timeline Estimate

- **Phase 1** (Core Integration): 2-3 hours
- **Phase 2** (Output Formatting): 1-2 hours
- **Phase 3** (AI Integration): 1-2 hours
- **Phase 4** (Refactoring): 1-2 hours
- **Testing & Documentation**: 1-2 hours

**Total**: ~6-11 hours of development time

## Dependencies

- Existing quality check module (`check_midi_quality.py`)
- Existing musical analysis module (`musical_analysis.py`)
- Existing AI providers (for optional AI naming)
- No new external dependencies required

