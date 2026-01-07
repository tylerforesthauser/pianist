# `annotate` Command

**Status**: Placeholder - To be fleshed out

## Purpose

Mark musical intent in compositions: key ideas, expansion points, and development directions.

## Syntax

```bash
pianist annotate -i <input.json> [options]
```

## Options

- `-i, --input` - Input composition JSON (required)
- `-o, --output` - Output JSON path
- `--key-idea` - Add a key idea (can be used multiple times)
- `--expansion-point` - Add an expansion point (can be used multiple times)
- `--development-direction` - Set overall development direction
- `--preserve` - Add to preserve list
- `--auto-detect` - Auto-detect motifs and phrases
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

### Manual Annotation

```bash
# Mark a motif
pianist annotate -i composition.json --mark-motif "0-4" "Opening ascending motif" \
  --importance high -o annotated.json

# Mark a phrase
pianist annotate -i composition.json --mark-phrase "0-16" "Opening phrase" \
  -o annotated.json

# Mark an expansion point
pianist annotate -i composition.json --mark-expansion "A" \
  --target-length 120 --development-strategy "Develop opening motif" \
  -o annotated.json

# Multiple annotations
pianist annotate -i composition.json \
  --mark-motif "0-4" "Opening motif" --importance high \
  --mark-phrase "0-16" "Opening phrase" \
  --overall-direction "Expand while preserving motifs" \
  -o annotated.json
```

### Auto-Detection

```bash
# Automatically detect and annotate motifs and phrases
pianist annotate -i composition.json --auto-detect -o annotated.json

# Auto-detect with verbose output
pianist annotate -i composition.json --auto-detect --verbose -o annotated.json
```

### View Annotations

```bash
# Show current annotations without modifying
pianist annotate -i composition.json --show
```

## Schema

**TODO**: Document MusicalIntent structure

## See Also

- [`../workflows/expanding_incomplete_compositions.md`](../workflows/expanding_incomplete_compositions.md)
- [`../reference/schema_reference.md`](../reference/schema_reference.md)
- [`README.md`](README.md) - All commands
- [`../../README.md`](../../README.md) - Main documentation

