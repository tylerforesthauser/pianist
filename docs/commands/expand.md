# `expand` Command

**Status**: Placeholder - To be fleshed out

## Purpose

Expand incomplete compositions into complete works, preserving and developing key ideas.

## Syntax

```bash
pianist expand -i <input.json> --target-length <beats> [options]
```

## Options

- `-i, --input` - Input composition JSON (required)
- `--target-length` - Target length in beats (required)
- `-o, --output` - Output JSON path
- `--provider` - AI provider for expansion
- `--model` - Model name
- `--instructions` - Expansion instructions
- `--preserve-motifs` - Preserve all marked motifs
- `--preserve` - Preserve specific ideas (comma-separated IDs)
- `--validate` - Validate expanded composition
- `--render` - Also render to MIDI
- `-r, --raw` - Save raw AI response
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

**TODO**: Add examples

## Workflow

**TODO**: Document how it uses annotations

## See Also

- [`../workflows/expanding_incomplete_compositions.md`](../workflows/expanding_incomplete_compositions.md)
- [`annotate.md`](annotate.md)
- [`../reference/command_reference.md`](../reference/command_reference.md)

