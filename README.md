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
```

## CLI

Render a MIDI file from raw model output (supports fenced JSON code blocks and minor JSON mistakes):

```bash
./pianist render --in examples/model_output.txt --out out.mid
```

### Prompt sync (keeping `AI_PROMPTING_GUIDE.md` up to date)

Canonical system prompt text lives in `src/pianist/prompts/*.txt` and is synced into `AI_PROMPTING_GUIDE.md`.

```bash
make sync-prompts
make check-prompts
```

See `PROMPT_SYNC.md` for details.

Iterate on an existing work by importing either a Pianist JSON (or raw LLM output text) **or a MIDI file**, emitting a clean JSON seed you can tweak and re-render:

```bash
# From MIDI -> Pianist JSON seed
./pianist iterate --in existing.mid --out seed.json

# Quick tweak example: transpose up a whole step
./pianist iterate --in seed.json --transpose 2 --out seed_transposed.json

# Generate a ready-to-paste LLM prompt (includes the seed JSON)
./pianist iterate --in seed.json --prompt-out iterate_prompt.txt --instructions "Make it more lyrical and add an 8-beat coda."

# Then render the updated JSON back to MIDI
./pianist render --in seed_transposed.json --out out.mid
```

Analyze an existing MIDI file to extract prompt-friendly musical constraints (tempo/time/key, note density, chord sizes, register, pedal usage, etc.) and generate a **NEW-composition prompt** inspired by that MIDI:

```bash
# Generate a ready-to-paste prompt for a NEW composition
./pianist analyze --in existing.mid --format prompt --prompt-out new_piece_prompt.txt \
  --instructions "Compose a new 64-bar piece with a similar texture, but more optimistic."

# Or export structured analysis JSON (for building UIs/tools)
./pianist analyze --in existing.mid --format json --out analysis.json

# Or both
./pianist analyze --in existing.mid --format both --out analysis.json --prompt-out new_piece_prompt.txt
```

Fix incorrect sustain pedal patterns in existing compositions:

```bash
# Fix pedal patterns (overwrites input)
./pianist fix-pedal --in "composition.json"

# Fix and save to new file, also render to MIDI
./pianist fix-pedal --in "composition.json" --out "composition_fixed.json" --render --out-midi "composition_fixed.mid"
```

See `PEDAL_FIX_USAGE.md` for details on fixing sustain pedal patterns.
**Alternative:** You can also use the Python module directly:

```bash
python3 -m pianist render --in examples/model_output.txt --out out.mid
```

`analyze` and `iterate` are also available via `python3 -m pianist ...`.

**Note:** Use `./pianist` (recommended) or `python3 -m pianist` instead of `pianist` for maximum compatibility with editable installs.

## Python API

```python
from pathlib import Path
from pianist import parse_composition_from_text
from pianist.renderers import render_midi_mido

text = Path("examples/model_output.txt").read_text(encoding="utf-8")
composition = parse_composition_from_text(text)
render_midi_mido(composition, "out.mid")
```

Analyze a MIDI file and generate a new-composition prompt:

```python
from pianist import analyze_midi, analysis_prompt_template

analysis = analyze_midi("existing.mid")
prompt = analysis_prompt_template(analysis, instructions="Write a calm nocturne.")
```

## Schema Generation for Structured Output

Generate OpenAPI/JSON Schema files for use with AI models that support structured output:

```bash
./pianist generate-schema
```

**Alternative:** You can also use the Python module directly:

```bash
python3 -m pianist generate-schema
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