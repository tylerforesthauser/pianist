# `expand` Command

## Purpose

Expand incomplete compositions to complete works using an AI provider. The system analyzes the composition, generates an expansion strategy, and uses AI to expand it according to the strategy.

## Syntax

```bash
pianist expand -i <input.json> --target-length <beats> [options]
```

## Options

- `-i, --input` - Input composition JSON (preferably annotated) (required)
- `--target-length` - Target length in beats (required)
- `-o, --output` - Output expanded JSON path. If omitted, prints to stdout.
- `--provider` - AI provider to use: `openrouter` (cloud, default), `gemini` (cloud), or `ollama` (local). Required if not set in config.
- `--model` - Model name. Default: `mistralai/devstral-2512:free` (OpenRouter), `gemini-flash-latest` (Gemini), or `gpt-oss:20b` (Ollama). Only used with `--provider`.
- `--preserve-motifs` - Preserve all marked motifs and develop them throughout
- `--preserve` - Comma-separated list of idea IDs to preserve
- `--validate` - Validate expansion quality before returning (checks motif preservation, development quality, harmonic coherence, form consistency)
- `--render` - Also render the expanded composition to MIDI
- `-m, --midi` - MIDI output path. Auto-generated from output name if `--render` is used without this flag.
- `-r, --raw` - Save the raw AI response text to this path. Auto-generated if `--output` is provided. Only used with `--provider`.
- `--verbose, -v` - Show progress indicators and timing for AI API calls
- `--debug` - Print a full traceback on errors
- `--overwrite` - Overwrite existing output files instead of creating versioned copies

## Examples

### Expand Composition

```bash
# Expand composition using AI (OpenRouter - default)
pianist expand -i sketch.json --target-length 300 \
  --provider openrouter -o expanded.json --render

# Expand composition using AI (Gemini)
pianist expand -i sketch.json --target-length 300 \
  --provider openrouter -o expanded.json --render

# Expand composition using AI (Ollama)
pianist expand -i sketch.json --target-length 300 \
  --provider ollama -o expanded.json --render

# Preserve specific motifs (with OpenRouter)
pianist expand -i annotated.json --target-length 300 \
  --provider openrouter --preserve-motifs -o expanded.json

# Preserve specific ideas by ID (with OpenRouter)
pianist expand -i annotated.json --target-length 300 \
  --provider openrouter --preserve "motif_1,phrase_1" -o expanded.json
```

### Expand with Validation

```bash
# Expand and validate the result
pianist expand -i sketch.json --target-length 300 \
  --provider openrouter --validate -o expanded.json

# Validate with verbose output to see detailed quality scores
pianist expand -i sketch.json --target-length 300 \
  --provider openrouter --validate --verbose -o expanded.json
```

Validation checks:
- **Motif Preservation**: Verifies that original motifs are preserved in the expansion
- **Development Quality**: Assesses the quality of motif/phrase development
- **Harmonic Coherence**: Checks harmonic coherence and progression
- **Form Consistency**: Verifies form structure is maintained
- **Length Validation**: Ensures target length is met (within acceptable range)
- **Overall Quality Score**: Weighted average of all quality metrics

## How It Works

1. **Analysis**: The command automatically performs musical analysis (motif detection, phrase detection, harmonic analysis, form detection)

2. **Strategy Generation**: Creates a detailed expansion strategy including:
   - Motif development techniques (sequence, variation, inversion, etc.)
   - Section expansion approaches
   - Transition suggestions
   - Preservation requirements

3. **AI Expansion**:
   - Uses the strategy to build detailed expansion instructions
   - Calls AI provider with enhanced prompt
   - Validates the result (if `--validate` is used):
     - Checks motif preservation
     - Assesses development quality
     - Verifies harmonic coherence
     - Checks form consistency
     - Validates target length
     - Calculates overall quality score

4. **Output**: Saves expanded composition

## Use Cases

1. **Expand Incomplete Compositions**: Take a 90-second sketch and expand it to a complete 5-minute piece
2. **Iterative Expansion**: Expand in stages, refining between expansions
3. **Preserve Key Ideas**: Use annotations to ensure important motifs and phrases are preserved

## Integration

- Use with `annotate` to mark key ideas and expansion points before expanding
- Use with `analyze` to understand the composition structure first
- Use with `reference` to manage example compositions that guide expansion
- Use with `diff` to compare original and expanded versions
- Use with `render` to convert expanded JSON to MIDI (or use `--render` flag)

## Reference Database Integration

When using `expand` with an AI provider, the system automatically:

1. Searches the reference database for relevant examples
2. Matches by style, form, and detected musical patterns
3. Includes up to 3 relevant references in the expansion prompt
4. Provides reference compositions as examples for the AI

To build your reference library:

```bash
# Add example compositions
pianist reference add -i example.json --style Classical --techniques sequence

# Search for relevant examples
pianist reference search --style Classical --technique sequence
```

## See Also

- [`../workflows/expanding_incomplete_compositions.md`](../workflows/expanding_incomplete_compositions.md)
- [`annotate.md`](annotate.md)
- [`analyze.md`](analyze.md)
- [`README.md`](README.md) - All commands
- [`../../README.md`](../../README.md) - Main documentation
