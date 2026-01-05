# pianist

Convert AI-generated composition specs (JSON) into MIDI.

## Install

It's recommended to use a Python virtual environment to isolate dependencies:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install pianist in development mode
python3 -m pip install -e ".[dev]"

# If you encounter ModuleNotFoundError after installation (Python 3.14+),
# run the fix script to ensure .pth files are processed correctly:
python3 fix_entry_point.py
```

## CLI

Render a MIDI file from raw model output (supports fenced JSON code blocks and minor JSON mistakes):

```bash
pianist render --in examples/model_output.txt --out out.mid
```

## Python API

```python
from pathlib import Path
from pianist import parse_composition_from_text
from pianist.renderers import render_midi_mido

text = Path("examples/model_output.txt").read_text(encoding="utf-8")
composition = parse_composition_from_text(text)
render_midi_mido(composition, "out.mid")
```

## Schema Generation for Structured Output

Generate OpenAPI/JSON Schema files for use with AI models that support structured output:

```bash
pianist generate-schema
```

This generates:
- `schema.json` - JSON Schema (most commonly used with AI models)
- `schema.openapi.json` - Full OpenAPI 3.1.0 specification

See `SCHEMA_GENERATION.md` for detailed usage instructions with various AI models (OpenAI, Anthropic, etc.).

## Prompting

See `AI_PROMPTING_GUIDE.md` for a schema-aligned prompt template that encourages motif development and musical form.

For piano output, Pianist supports a **single Piano track** where each note (or sub-chord) can be annotated with explicit `hand` (`"lh"`/`"rh"`) and optional `voice` (1–4) via `NoteEvent` objects using the `groups` or `notes` fields.

Pianist supports tempo changes within compositions, including instant tempo changes and gradual tempo changes (ritardando/accelerando) via `TempoEvent` objects.

The prompting guide also recommends using a **system prompt** (format/schema invariants) plus a **user prompt** (musical brief) for better schema adherence.

## Troubleshooting

### ModuleNotFoundError after installation (Python 3.14+)

If you encounter `ModuleNotFoundError: No module named 'pianist'` after installing in editable mode, this is due to a Python 3.14 issue where `.pth` files aren't processed correctly in entry point scripts. Run the fix script:

```bash
python3 fix_entry_point.py
```

This will automatically fix the entry point script to ensure `.pth` files are processed correctly.