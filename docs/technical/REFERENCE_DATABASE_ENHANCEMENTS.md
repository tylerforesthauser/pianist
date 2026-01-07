# Reference Database Enhancements

This document outlines enhancements to the reference database based on the rich metadata now available from the review and normalization scripts.

## Current State

### Database Schema
- **Basic fields**: id, title, description, style, form, techniques, composition_json, metadata (JSON blob)
- **Indexes**: style, form, title
- **Search capabilities**: style, form, technique, title, description (text search)

### Available Metadata (from review script)
- **Quality scores**: quality_score, technical_score, musical_score, structure_score
- **Musical analysis**: detected_key, motif_count, phrase_count, chord_count, harmonic_progression
- **Duration info**: duration_beats, duration_seconds, bars, tempo_bpm
- **Technical**: time_signature, key_signature, tracks
- **Similarity**: similarity_scores, duplicate_group

### Current Limitations

1. **find_relevant_references()** uses very basic heuristics:
   - Only matches by form (if detected)
   - Poor style inference (just checks if key contains "major")
   - No key matching
   - No quality filtering
   - No musical similarity matching

2. **Search is limited**:
   - Can't search by key
   - Can't search by tempo range
   - Can't filter by quality scores
   - Can't search by motif/phrase counts
   - No musical similarity search

3. **Metadata underutilized**:
   - Rich metadata stored in JSON blob but not searchable
   - No way to leverage harmonic progression for matching
   - No quality-based ranking

## Proposed Enhancements

### 1. Enhanced Database Schema

Add searchable columns for key metadata:

```sql
ALTER TABLE musical_references ADD COLUMN detected_key TEXT;
ALTER TABLE musical_references ADD COLUMN tempo_bpm REAL;
ALTER TABLE musical_references ADD COLUMN duration_beats REAL;
ALTER TABLE musical_references ADD COLUMN quality_score REAL;
ALTER TABLE musical_references ADD COLUMN technical_score REAL;
ALTER TABLE musical_references ADD COLUMN musical_score REAL;
ALTER TABLE musical_references ADD COLUMN structure_score REAL;
ALTER TABLE musical_references ADD COLUMN motif_count INTEGER;
ALTER TABLE musical_references ADD COLUMN phrase_count INTEGER;
ALTER TABLE musical_references ADD COLUMN chord_count INTEGER;
ALTER TABLE musical_references ADD COLUMN harmonic_progression TEXT;  -- First 10 chords
ALTER TABLE musical_references ADD COLUMN time_signature TEXT;
ALTER TABLE musical_references ADD COLUMN bars REAL;
```

**Indexes:**
```sql
CREATE INDEX IF NOT EXISTS idx_key ON musical_references(detected_key);
CREATE INDEX IF NOT EXISTS idx_quality ON musical_references(quality_score);
CREATE INDEX IF NOT EXISTS idx_tempo ON musical_references(tempo_bpm);
```

### 2. Enhanced Search Capabilities

Add search parameters:
- `key`: Filter by detected key (exact or base key match)
- `tempo_min`/`tempo_max`: Filter by tempo range
- `min_quality`: Filter by minimum quality score
- `min_motif_count`: Filter by minimum motif count
- `min_phrase_count`: Filter by minimum phrase count
- `musical_similarity`: Find references similar to a given composition

### 3. Smarter Relevance Matching

Enhance `find_relevant_references()` to:
1. **Match by key**: Exact key match (highest priority), then base key match
2. **Match by form**: Use detected form from analysis
3. **Match by harmonic progression**: Compare first 10 chords
4. **Match by style**: Use detected style from analysis (not just key inference)
5. **Quality ranking**: Prefer higher quality references
6. **Musical similarity**: Use similarity calculation from review script

### 4. Metadata Integration

Update `batch_import_references.py` to:
- Extract metadata from review CSV if available
- Populate new database columns
- Store full metadata in metadata JSON for backward compatibility

### 5. Coverage Tracking

Add methods to track coverage:
- `get_coverage_by_style()`: Count references by style
- `get_coverage_by_form()`: Count references by form
- `get_coverage_by_technique()`: Count references by technique
- `get_coverage_gaps()`: Identify missing coverage areas

### 6. Quality-Based Ranking

When searching, rank results by:
1. Exact matches (key, form, style)
2. Quality score (higher is better)
3. Musical similarity score
4. Relevance to query

## Implementation Plan

### Phase 1: Schema Migration
1. Add migration function to update existing databases
2. Add new columns with default values
3. Create new indexes
4. Update `MusicalReference` dataclass

### Phase 2: Enhanced Search
1. Extend `search_references()` with new parameters
2. Add quality-based ranking
3. Update CLI search command

### Phase 3: Smarter Matching
1. Rewrite `find_relevant_references()` with musical similarity
2. Use analysis results for better matching
3. Add quality filtering

### Phase 4: Metadata Integration
1. Update `batch_import_references.py` to extract and store metadata
2. Update normalization script to include all metadata in import CSV
3. Add metadata extraction from review CSV

### Phase 5: Coverage Tracking
1. Add coverage analysis methods
2. Add CLI command for coverage report
3. Integrate with normalization script

## Benefits

1. **Better Reference Matching**: AI expansion will get more relevant examples
2. **Quality Filtering**: Can ensure only high-quality references are used
3. **Musical Similarity**: Find references that are musically similar, not just same form/style
4. **Key Matching**: Match references in the same key for better coherence
5. **Coverage Tracking**: Know what's missing and what's well-covered
6. **Better Search**: Users can find references by musical characteristics

## Backward Compatibility

- Existing references continue to work (new columns nullable)
- Metadata JSON blob still contains all data
- Old search API still works (new parameters optional)
- Migration handles existing databases gracefully

