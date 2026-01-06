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
- `--provider` - AI provider to generate new composition
- `--model` - Model name
- `--instructions` - Instructions for composition
- `--render` - Also render AI-generated composition to MIDI
- `-r, --raw` - Save raw AI response
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

**TODO**: Add examples

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

