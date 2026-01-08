# `modify` Command

**Status**: Placeholder - To be fleshed out

## Purpose

Modify existing compositions: transpose, or use AI to modify compositions based on instructions.

## Syntax

```bash
pianist modify -i <input.json> [options]
```

## Options

- `-i, --input` - Input composition JSON (required)
- `-o, --output` - Output JSON path
- `--transpose, -t` - Transpose by semitones
- `--provider` - AI provider for modification: `openrouter` (cloud, default), `gemini` (cloud), or `ollama` (local). Required for AI-based modifications if not set in config.
- `--model` - Model name. Default: `mistralai/devstral-2512:free` (OpenRouter), `gemini-flash-latest` (Gemini), or `gpt-oss:20b` (Ollama)
- `--instructions` - Modification instructions
- `--render` - Also render to MIDI
- `-p, --prompt` - Save prompt template
- `-r, --raw` - Save raw AI response
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

**TODO**: Add examples

## Use Cases

**TODO**: Document use cases

## See Also

- [`../workflows/composition_iteration.md`](../workflows/composition_iteration.md)
- [`README.md`](README.md) - All commands
- [`../../README.md`](../../README.md) - Main documentation

