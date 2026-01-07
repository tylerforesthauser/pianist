# `expand` Command

## Purpose

Expand incomplete compositions to complete works. Can work with or without an AI provider.

**Without AI Provider**: Generates and displays a detailed expansion strategy based on musical analysis.

**With AI Provider**: Uses AI to expand the composition according to the generated strategy, incorporating musical analysis results.

## Syntax

```bash
pianist expand -i <input.json> --target-length <beats> [options]
```

## Options

- `-i, --input` - Input composition JSON (preferably annotated) (required)
- `--target-length` - Target length in beats (required)
- `-o, --output` - Output expanded JSON path. If omitted, prints to stdout.
- `--provider` - AI provider to use (currently: `gemini`). If omitted, only generates expansion strategy.
- `--model` - Model name (default: `gemini-flash-latest`). Only used with `--provider`.
- `--preserve-motifs` - Preserve all marked motifs and develop them throughout
- `--preserve` - Comma-separated list of idea IDs to preserve
- `--validate` - Validate expansion quality before returning (basic checks implemented)
- `--render` - Also render the expanded composition to MIDI
- `-m, --midi` - MIDI output path. Auto-generated from output name if `--render` is used without this flag.
- `-r, --raw` - Save the raw AI response text to this path. Auto-generated if `--output` is provided. Only used with `--provider`.
- `--verbose, -v` - Show progress indicators and timing for AI API calls
- `--debug` - Print a full traceback on errors
- `--overwrite` - Overwrite existing output files instead of creating versioned copies

## Examples

### Generate Expansion Strategy (No AI Required)

```bash
# Generate and display expansion strategy
pianist expand -i sketch.json --target-length 300 -o strategy_output.json

# Output strategy to stdout
pianist expand -i sketch.json --target-length 300
```

### Expand with AI Provider

```bash
# Expand composition using AI
pianist expand -i sketch.json --target-length 300 \
  --provider gemini -o expanded.json --render

# Preserve specific motifs
pianist expand -i annotated.json --target-length 300 \
  --provider gemini --preserve-motifs -o expanded.json

# Preserve specific ideas by ID
pianist expand -i annotated.json --target-length 300 \
  --provider gemini --preserve "motif_1,phrase_1" -o expanded.json
```

### Expand with Validation

```bash
# Expand and validate the result
pianist expand -i sketch.json --target-length 300 \
  --provider gemini --validate -o expanded.json
```

## How It Works

1. **Analysis**: The command automatically performs musical analysis (motif detection, phrase detection, harmonic analysis, form detection)

2. **Strategy Generation**: Creates a detailed expansion strategy including:
   - Motif development techniques (sequence, variation, inversion, etc.)
   - Section expansion approaches
   - Transition suggestions
   - Preservation requirements

3. **AI Expansion** (if `--provider` is used):
   - Uses the strategy to build detailed expansion instructions
   - Calls AI provider with enhanced prompt
   - Validates the result (if `--validate` is used)

4. **Output**: Saves expanded composition (or strategy if no provider)

## Use Cases

1. **Expand Incomplete Compositions**: Take a 90-second sketch and expand it to a complete 5-minute piece
2. **Strategy Planning**: Generate expansion strategies without AI to plan the expansion approach
3. **Iterative Expansion**: Expand in stages, refining between expansions
4. **Preserve Key Ideas**: Use annotations to ensure important motifs and phrases are preserved

## Integration

- Use with `annotate` to mark key ideas and expansion points before expanding
- Use with `analyze` to understand the composition structure first
- Use with `diff` to compare original and expanded versions
- Use with `render` to convert expanded JSON to MIDI (or use `--render` flag)

## See Also

- [`../workflows/expanding_incomplete_compositions.md`](../workflows/expanding_incomplete_compositions.md)
- [`annotate.md`](annotate.md)
- [`analyze.md`](analyze.md)
- [`../reference/command_reference.md`](../reference/command_reference.md)
