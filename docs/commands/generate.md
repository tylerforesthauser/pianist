# `generate` Command

## Purpose

Generate new compositions from text descriptions. Can work with or without an AI provider.

**Without AI Provider**: Generates a ready-to-paste prompt template that you can use with any AI model.

**With AI Provider**: Directly generates a composition using the built-in AI provider (currently Gemini).

## Syntax

```bash
pianist generate [description] [options]
```

The description can be provided as a positional argument or piped from stdin.

## Options

- `description` (positional, optional) - Text description of the composition. If omitted, reads from stdin.
- `--provider` - AI provider to use (currently: `gemini`). If omitted, only generates a prompt template.
- `--model` - Model name (default: `gemini-flash-latest`). Only used with `--provider`.
- `-o, --output` - Output JSON path. If omitted, prints to stdout (prompt mode) or stdout (JSON mode).
- `--render` - Also render the generated composition to MIDI. **Requires `--provider`**.
- `-m, --midi` - MIDI output path. Auto-generated from output name if `--render` is used without this flag.
- `-p, --prompt` - Write the prompt template to this path (useful when using external AI).
- `-r, --raw` - Save the raw AI response text to this path. Auto-generated if `--output` is provided. Only used with `--provider`.
- `--verbose, -v` - Show progress indicators and timing for AI API calls.
- `--debug` - Print a full traceback on errors.
- `--overwrite` - Overwrite existing output files instead of creating versioned copies.

## Examples

### Generate Prompt Template (No AI Required)

```bash
# Generate a prompt template for external AI
pianist generate "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -p prompt.txt

# Or read from stdin
echo "Title: Test Piece" | pianist generate -p prompt.txt
```

### Generate with AI Provider

```bash
# Generate and render in one command
pianist generate --provider gemini "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -o composition.json --render

# MIDI path auto-generated as composition.mid
```

### Generate Without Output File

```bash
# Output JSON to stdout
pianist generate --provider gemini "Title: Test" | pianist render -i - -o out.mid
```

## Use Cases

1. **Quick Composition Generation**: Generate compositions directly from text descriptions
2. **Prompt Template Creation**: Create reusable prompts for external AI models
3. **Iterative Composition**: Generate initial ideas, then refine with `modify` or `expand`
4. **Batch Generation**: Use with scripts to generate multiple compositions

## Integration

- Use with `render` to convert generated JSON to MIDI
- Use with `modify` to iterate on generated compositions
- Use with `expand` to develop incomplete generated compositions
- Use with `annotate` to mark key ideas in generated compositions

## See Also

- [`../workflows/ai_human_collaboration.md`](../workflows/ai_human_collaboration.md)
- [`../guides/ai_prompting.md`](../guides/ai_prompting.md)
- [`../reference/command_reference.md`](../reference/command_reference.md)

