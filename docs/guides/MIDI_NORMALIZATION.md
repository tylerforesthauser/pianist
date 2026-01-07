# MIDI File Normalization Guide

This guide covers the process of normalizing and organizing MIDI files after analysis for database import.

## Overview

After running `review_and_categorize_midi.py` to analyze your MIDI collection, you'll have a `review_report.csv` file with comprehensive metadata. The `normalize_midi_review.py` script processes this data to:

1. **Rename files** according to suggested names
2. **Identify duplicate groups** for manual review
3. **Flag files for exclusion** based on quality criteria
4. **Validate data completeness**
5. **Generate reports** for manual review

## Usage

### Basic Usage (Dry Run)

First, run in dry-run mode to see what would be done:

```bash
python3 scripts/normalize_midi_review.py \
  --csv output/review_report.csv \
  --dir references/ \
  --dry-run
```

This will:
- Show what files would be renamed
- Generate all reports without making changes
- Display summary statistics

### Actual Normalization

Once you've reviewed the dry-run output:

```bash
python3 scripts/normalize_midi_review.py \
  --csv output/review_report.csv \
  --dir references/
```

This will:
- Rename files according to suggested names
- Generate all reports
- Create rename mapping files

### Custom Quality Thresholds

Adjust quality thresholds for exclusion detection:

```bash
python3 scripts/normalize_midi_review.py \
  --csv output/review_report.csv \
  --dir references/ \
  --min-quality 0.8 \
  --min-technical 0.7 \
  --min-musical 0.7 \
  --min-structure 0.7
```

### Custom Output Locations

```bash
python3 scripts/normalize_midi_review.py \
  --csv output/review_report.csv \
  --dir references/ \
  --output-dir references/normalized/ \
  --reports-dir output/normalization/
```

## Generated Reports

The script generates several reports in the reports directory (default: same directory as CSV):

### 1. Duplicate Groups Report

**Files:**
- `duplicate_groups_report.json` - Detailed JSON with all groups
- `duplicate_groups_report.csv` - CSV for easy spreadsheet review

**Contents:**
- Groups of similar/duplicate compositions
- Quality scores for each file in the group
- Musical characteristics (key, form, etc.)

**Use for:**
- Identifying which files are duplicates
- Deciding which version to keep (usually highest quality)
- Manual review of similar compositions

### 2. Exclusions Report

**Files:**
- `exclusions_report.json` - Detailed JSON with exclusion reasons
- `exclusions_report.csv` - CSV for easy review

**Contents:**
- Files that fail quality thresholds
- Specific reasons for each exclusion
- Scores for all quality dimensions

**Use for:**
- Reviewing low-quality files
- Deciding which files to exclude from database
- Identifying files that need re-analysis or fixing

### 3. Rename Mapping

**Files:**
- `rename_mapping.json` - Complete mapping with conflicts
- `rename_mapping.csv` - Simple CSV mapping

**Contents:**
- Original filename → New filename mapping
- Suggested names and IDs
- Conflict detection (when multiple files would get same name)

**Use for:**
- Tracking file renames
- Resolving naming conflicts
- Verifying rename operations

### 4. Summary Report

**File:**
- `normalization_summary.json`

**Contents:**
- Total statistics
- Data completeness metrics
- Counts of duplicates, exclusions, renames
- Files ready for import
- Coverage analysis

**Use for:**
- Quick overview of normalization results
- Data quality assessment
- Import readiness check

### 5. Import Metadata CSV

**File:**
- `import_metadata.csv`

**Contents:**
- Ready-to-use metadata for `batch_import_references.py`
- Columns: `filename`, `id`, `title`, `description`, `style`, `form`, `techniques`
- Uses new filenames (if renamed)
- Excludes originals and low-quality files by default

**Use for:**
- Direct import to reference database
- No manual CSV creation needed
- Review and add techniques column manually if needed

### 6. Coverage Analysis

**File:**
- `coverage_analysis.json`

**Contents:**
- Distribution by style
- Distribution by form
- Quality distribution (high/medium/low)

**Use for:**
- Identify gaps in collection
- Plan future curation
- Track progress toward coverage goals

## Workflow

### Step 1: Review Duplicate Groups

1. Open `duplicate_groups_report.csv` in a spreadsheet
2. For each group:
   - Compare quality scores
   - Check musical characteristics
   - Decide which file(s) to keep
   - Note files to exclude

### Step 2: Review Exclusions

1. Open `exclusions_report.csv`
2. Review each file's exclusion reasons
3. Decide:
   - **Exclude**: File is not suitable for database
   - **Keep**: File is acceptable despite low scores
   - **Fix**: File needs correction before inclusion

### Step 3: Resolve Naming Conflicts

1. Check `rename_mapping.json` for conflicts
2. If conflicts exist:
   - Review suggested names
   - Manually rename conflicting files if needed
   - Update mapping if necessary

### Step 4: Manual File Management

Based on your reviews:

1. **Remove duplicates**: Delete files you've identified as duplicates
2. **Remove exclusions**: Delete files you've decided to exclude
3. **Fix issues**: Correct any files that need fixing

### Step 5: Final Import

Once files are normalized and cleaned:

```bash
# Import normalized files
python3 scripts/batch_import_references.py \
  --dir references/ \
  --metadata output/review_report.csv
```

## Quality Thresholds

Default thresholds (can be customized):

- **min-quality**: 0.7 - Overall quality score
- **min-technical**: 0.5 - Technical quality (MIDI structure, timing)
- **min-musical**: 0.5 - Musical quality (harmony, melody)
- **min-structure**: 0.5 - Structural quality (form, phrases)

### Additional Exclusion Criteria

Files are also flagged for exclusion if:

- **Very short**: < 20 beats (likely fragments)
- **Very long**: > 1000 beats (might be multi-movement works)
- **Missing critical metadata**: No suggested_name, detected_key, or detected_form

## Filename Sanitization

The script automatically sanitizes suggested names to valid filenames:

- Removes invalid characters (`<>:"/\|?*` and control characters)
- Limits length to 200 characters (cuts at word boundary)
- Preserves readability
- Falls back to `suggested_id` if name is too short

## Conflict Resolution

If multiple files would get the same name:

1. Script automatically adds numeric suffix (`_01`, `_02`, etc.)
2. Conflicts are reported in `rename_mapping.json`
3. Review conflicts and manually adjust if needed

## Data Completeness

The script validates that all required fields are present:

- **Required fields**: filename, quality_score, suggested_name, suggested_id, detected_key, detected_form, duration_beats, bars, tempo_bpm, time_signature, motif_count, phrase_count, chord_count, technical_score, musical_score, structure_score

- **Completeness report**: Shows percentage of files with each field

If fields are missing:
- Review the original analysis
- Re-run analysis for files with missing data
- Consider excluding files with critical missing fields

## Best Practices

1. **Always dry-run first**: Review what will happen before making changes
2. **Backup your files**: Rename operations are irreversible
3. **Review reports carefully**: Manual review is essential for quality
4. **Keep original filenames**: The rename mapping preserves original names
5. **Iterate on thresholds**: Adjust quality thresholds based on your collection

## Troubleshooting

### Files Not Found

If files aren't found during rename:
- Check that `--dir` points to the correct directory
- Verify filenames in CSV match actual files
- Check for case sensitivity issues

### Too Many Exclusions

If too many files are flagged:
- Lower quality thresholds
- Review exclusion reasons - some may be acceptable
- Consider fixing files instead of excluding

### Too Many Duplicates

If duplicate groups seem incorrect:
- Review similarity detection in original analysis
- Check if files are actually duplicates or just similar
- Adjust similarity threshold in review script

## Integration with Database Import

After normalization:

1. Files are renamed and organized
2. Duplicate groups are identified
3. Exclusions are documented
4. Data is validated
5. **Import metadata CSV is generated** - Ready for batch import

### Import Metadata CSV

The script automatically generates `import_metadata.csv` which is ready for use with `batch_import_references.py`:

```bash
# After normalization, import directly:
python3 scripts/batch_import_references.py \
  --dir references/ \
  --metadata output/import_metadata.csv \
  --verbose
```

**Default behavior:**
- Excludes original compositions (`is_original=Yes`)
- Excludes files flagged for exclusion
- Maps review data to database format:
  - `suggested_id` → `id`
  - `suggested_name` → `title`
  - `suggested_description` → `description`
  - `suggested_style` → `style`
  - `detected_form` → `form`
  - `techniques` → left empty (for manual addition)

**Options:**
```bash
# Include original compositions
python3 scripts/normalize_midi_review.py \
  --csv output/review_report.csv \
  --dir references/ \
  --include-originals

# Include files flagged for exclusion
python3 scripts/normalize_midi_review.py \
  --csv output/review_report.csv \
  --dir references/ \
  --include-excluded
```

### Coverage Analysis

The script generates a coverage analysis showing:
- Distribution by style (Baroque, Classical, Romantic, etc.)
- Distribution by form (binary, ternary, sonata, etc.)
- Quality distribution (high ≥0.8, medium ≥0.6, low <0.6)

This helps identify gaps in your collection relative to the target coverage goals:
- **By Style**: Baroque (15-20), Classical (20-25), Romantic (20-25), Modern (15-20)
- **By Form**: Binary (10-15), Ternary (15-20), Sonata (10-15), etc.

Review `coverage_analysis.json` to see where you need more examples.

