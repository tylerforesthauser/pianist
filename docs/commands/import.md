# `import` Command

**Status**: Placeholder - To be fleshed out

## Purpose

Import MIDI files and convert them to Pianist JSON format.

## Syntax

```bash
pianist import -i <input.mid> [-o <output.json>]
```

## Options

- `-i, --input` - Input MIDI file (required)
- `-o, --output` - Output JSON path (optional, prints to stdout if omitted)
- `--verbose, -v` - Show progress
- `--debug` - Show tracebacks
- `--overwrite` - Overwrite existing files

## Examples

**TODO**: Add examples

## Limitations

**TODO**: Document what gets preserved/lost in conversion

## See Also

- [`../workflows/midi_analysis_generation.md`](../workflows/midi_analysis_generation.md)
- [`../technical/midi_conversion.md`](../technical/midi_conversion.md)
- [`README.md`](README.md) - All commands
- [`../../README.md`](../../README.md) - Main documentation

