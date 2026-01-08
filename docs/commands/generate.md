# `generate` Command

## Purpose

Generate new compositions from text descriptions using an AI provider (OpenRouter cloud - default, Gemini cloud, or Ollama local).

## Syntax

```bash
pianist generate [description] [options]
```

The description can be provided as a positional argument or piped from stdin.

## Options

- `description` (positional, optional) - Text description of the composition. If omitted, reads from stdin.
- `--provider` - AI provider to use: `openrouter` (cloud, default), `gemini` (cloud), or `ollama` (local). Required if not set in config.
- `--model` - Model name. Default: `mistralai/devstral-2512:free` (OpenRouter), `gemini-flash-latest` (Gemini), or `gpt-oss:20b` (Ollama). Only used with `--provider`.
- `-o, --output` - Output JSON path. If omitted, prints to stdout.
- `--render` - Also render the generated composition to MIDI. **Requires `--provider`**.
- `-m, --midi` - MIDI output path. Auto-generated from output name if `--render` is used without this flag.
- `-p, --prompt` - Write the prompt template to this path.
- `-r, --raw` - Save the raw AI response text to this path. Auto-generated if `--output` is provided. Only used with `--provider`.
- `--verbose, -v` - Show progress indicators and timing for AI API calls.
- `--debug` - Print a full traceback on errors.
- `--overwrite` - Overwrite existing output files instead of creating versioned copies.

## Examples

### Generate Composition

```bash
# Generate with OpenRouter (cloud, default)
pianist generate --provider openrouter "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -o composition.json --render

# Generate with Gemini (cloud)
pianist generate --provider openrouter "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -o composition.json --render

# Generate with Ollama (local)
pianist generate --provider ollama "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -o composition.json --render

# Use a specific Ollama model
pianist generate --provider ollama --model gemma3:4b "Title: Morning Sketch..." -o composition.json

# MIDI path auto-generated as composition.mid
```

### Generate Without Output File

```bash
# Output JSON to stdout
pianist generate --provider openrouter "Title: Test" | pianist render -i - -o out.mid
```

## Use Cases

1. **Quick Composition Generation**: Generate compositions directly from text descriptions
2. **Iterative Composition**: Generate initial ideas, then refine with `modify` or `expand`
3. **Batch Generation**: Use with scripts to generate multiple compositions

## Integration

- Use with `render` to convert generated JSON to MIDI
- Use with `modify` to iterate on generated compositions
- Use with `expand` to develop incomplete generated compositions
- Use with `annotate` to mark key ideas in generated compositions

## See Also

- [`../workflows/ai_human_collaboration.md`](../workflows/ai_human_collaboration.md)
- [`../../README.md`](../../README.md) - Main documentation
- [`../../AI_PROMPTING_GUIDE.md`](../../AI_PROMPTING_GUIDE.md) - For external AI workflows (using ChatGPT, Claude, etc. outside the CLI)

