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

**TODO**: Add examples

## Schema

**TODO**: Document MusicalIntent structure

## See Also

- [`../workflows/expanding_incomplete_compositions.md`](../workflows/expanding_incomplete_compositions.md)
- [`../reference/schema_reference.md`](../reference/schema_reference.md)
- [`../reference/command_reference.md`](../reference/command_reference.md)

