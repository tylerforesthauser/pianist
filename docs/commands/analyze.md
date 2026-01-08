# `analyze` Command

## Purpose

Perform comprehensive analysis of MIDI or JSON compositions, including:
- **Quality assessment** (technical, musical, structure scores)
- **Musical analysis** (motifs, phrases, harmony, form)
- **Improvement suggestions** (actionable advice for enhancement)
- **Technical metadata** (duration, tempo, time/key signatures, tracks)
- **AI insights** (suggested name, style, description)

## Syntax

```bash
pianist analyze -i <input.mid|input.json> [options]
```

## Options

- `-i, --input` - Input file: MIDI (.mid/.midi) or JSON (.json) (required)
- `-f, --format` - Output format: `json` (default), `text` (human-readable), `prompt`, or `both`
- `-o, --output` - Output path for JSON/text. If omitted, prints to stdout
- `-p, --prompt` - Write prompt text to path (only used with `--format prompt`)
- `--ai-naming` - Use AI to generate suggested name, style, and description
- `--ai-provider` - AI provider for `--ai-naming`: `gemini` (default), `ollama`, or `openrouter`
- `--ai-model` - Model name for `--ai-naming`. Default: `gemini-flash-latest` (Gemini), `gpt-oss:20b` (Ollama), or `mistralai/devstral-2512:free` (OpenRouter). Free OpenRouter options: `mistralai/devstral-2512:free` (recommended), `xiaomi/mimo-v2-flash:free`, `tngtech/deepseek-r1t2-chimera:free`, `nex-agi/deepseek-v3.1-nex-n1:free`
- `--provider` - AI provider to generate new composition: `gemini` (cloud) or `ollama` (local)
- `--model` - Model name. Default: `gemini-flash-latest` (Gemini) or `gpt-oss:20b` (Ollama). Only used with `--provider`
- `--instructions` - Instructions for composition (only used with `--provider`)
- `--render` - Also render AI-generated composition to MIDI (only valid with `--provider`)
- `-r, --raw` - Save raw AI response (only used with `--provider`)
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

### Comprehensive Analysis (Default)

```bash
# Analyze MIDI file with comprehensive analysis (JSON output)
pianist analyze -i composition.mid -o analysis.json

# Analyze JSON composition with comprehensive analysis
pianist analyze -i composition.json -o analysis.json

# Human-readable text output
pianist analyze -i composition.mid --format text

# Output to stdout (JSON)
pianist analyze -i composition.mid

# With AI-assisted naming and description (uses default provider/model)
pianist analyze -i composition.mid --ai-naming -o analysis.json

# Use OpenRouter with free model (recommended for testing)
pianist analyze -i composition.mid --ai-naming --ai-provider openrouter --ai-model "mistralai/devstral-2512:free"

# Use specific AI provider for naming
pianist analyze -i composition.mid --ai-naming --ai-provider ollama
```

### Quality Assessment

```bash
# Check quality scores
pianist analyze -i composition.mid | jq '.quality.overall_score'

# Get improvement suggestions
pianist analyze -i composition.mid | jq '.improvement_suggestions.issues_to_fix'
```

### Prompt Generation (Legacy Mode)

```bash
# Generate prompt template from MIDI analysis (for composition generation)
pianist analyze -i existing.mid --format prompt -p prompt.txt \
  --instructions "Compose a new piece with similar texture"
```

### Composition Generation (with --provider)

```bash
# Analyze MIDI and generate new composition with AI (Gemini)
pianist analyze -i existing.mid --provider gemini \
  --instructions "Compose something similar but more optimistic" \
  -o new_composition.json --render

# Analyze MIDI and generate new composition with AI (Ollama)
pianist analyze -i existing.mid --provider ollama \
  --instructions "Compose something similar but more optimistic" \
  -o new_composition.json --render
```

### Generate Composition from Analysis

```bash
# Analyze MIDI and generate new composition with AI (Gemini)
pianist analyze -i existing.mid --provider gemini \
  --instructions "Compose something similar but more optimistic" \
  -o new_composition.json --render

# Analyze MIDI and generate new composition with AI (Ollama)
pianist analyze -i existing.mid --provider ollama \
  --instructions "Compose something similar but more optimistic" \
  -o new_composition.json --render
```

## Analysis Output

The analyze command provides comprehensive analysis including:

### Quality Assessment
- **Overall score** (0.0-1.0) - Weighted average of technical, musical, and structure scores
- **Technical score** - MIDI quality, timing, structure
- **Musical score** - Musical coherence, voice leading, harmonic progression
- **Structure score** - Form, balance, development
- **Quality issues** - List of specific problems found

### Technical Metadata
- Duration (beats, seconds, bars)
- Tempo (BPM)
- Time signature
- Key signature
- Number of tracks
- File size, format info

### Musical Analysis
- **Detected key** (from harmonic analysis)
- **Detected form** (binary, ternary, sonata, etc.)
- **Motif count** and details
- **Phrase count** and details
- **Chord count** and progression
- **Harmonic progression** (first 10 chords)
- **Cadences** detected

### Improvement Suggestions
- **Issues to fix** - Specific problems with severity and suggestions
- **Improvements** - How to enhance the composition
- **Quality recommendations** - Actionable advice

### AI Insights (with `--ai-naming`)
- **Suggested name** - AI-generated descriptive title
- **Suggested style** - Baroque, Classical, Romantic, Modern, etc.
- **Suggested description** - AI-generated description of musical characteristics

## Output Formats

### JSON Format (Default)
Structured JSON output with all analysis data. Easy to parse programmatically.

### Text Format (Human-Readable)
Formatted text output with clear sections and hierarchy. Use `--format text`.

### Prompt Format (Legacy)
Prompt template for AI composition generation. Use `--format prompt`.

For detailed technical information, see [`../technical/analysis_technical_details.md`](../technical/analysis_technical_details.md).

## See Also

- [`../technical/analysis_technical_details.md`](../technical/analysis_technical_details.md)
- [`../guides/testing_analysis.md`](../guides/testing_analysis.md)
- [`../workflows/midi_analysis_generation.md`](../workflows/midi_analysis_generation.md)
- [`README.md`](README.md) - All commands
- [`../../README.md`](../../README.md) - Main documentation

