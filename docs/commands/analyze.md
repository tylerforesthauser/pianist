# `analyze` Command

**Status**: Placeholder - To be fleshed out

## Purpose

Analyze MIDI or JSON compositions to extract musical characteristics.

## Syntax

```bash
pianist analyze -i <input.mid|input.json> [options]
```

## Options

- `-i, --input` - Input file: MIDI (.mid/.midi) or JSON (.json) (required)
- `-f, --format` - Output format: prompt, json, or both (default: prompt)
- `-o, --output` - Output path for JSON
- `-p, --prompt` - Write prompt text to path
- `--provider` - AI provider to generate new composition: `gemini` (cloud) or `ollama` (local)
- `--model` - Model name. Default: `gemini-flash-latest` (Gemini) or `gpt-oss:20b` (Ollama)
- `--instructions` - Instructions for composition
- `--render` - Also render AI-generated composition to MIDI
- `-r, --raw` - Save raw AI response
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

### Analyze MIDI File

```bash
# Generate prompt template from MIDI analysis
pianist analyze -i existing.mid -f prompt -p prompt.txt \
  --instructions "Compose a new piece with similar texture"

# Export structured analysis JSON
pianist analyze -i existing.mid -f json -o analysis.json

# Both prompt and JSON
pianist analyze -i existing.mid -f both -o analysis.json -p prompt.txt
```

### Analyze JSON Composition

```bash
# Analyze a Pianist JSON composition
pianist analyze -i composition.json -o analysis.json

# Output to stdout
pianist analyze -i composition.json

# Analyze and generate new composition with AI (Gemini)
pianist analyze -i composition.json --provider gemini \
  --instructions "Expand this into a full piece" -o expanded.json

# Analyze and generate new composition with AI (Ollama)
pianist analyze -i composition.json --provider ollama \
  --instructions "Expand this into a full piece" -o expanded.json
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

## Analysis Types

The analyze command performs several types of analysis:

- **Motif Detection** - Identifies recurring pitch patterns
- **Phrase Detection** - Detects musical phrases
- **Harmonic Analysis** - Analyzes chord progressions
- **Form Detection** - Identifies musical form (if sections are marked)

For detailed technical information, see [`../technical/analysis_technical_details.md`](../technical/analysis_technical_details.md).

## See Also

- [`../technical/analysis_technical_details.md`](../technical/analysis_technical_details.md)
- [`../guides/testing_analysis.md`](../guides/testing_analysis.md)
- [`../workflows/midi_analysis_generation.md`](../workflows/midi_analysis_generation.md)
- [`../reference/command_reference.md`](../reference/command_reference.md)

