# pianist

Convert AI-generated composition specs (JSON) into MIDI.

## Install

```bash
python3 -m pip install -e ".[dev]"
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

## Prompting

See `AI_PROMPTING_GUIDE.md` for a schema-aligned prompt template that encourages motif development and musical form.

For piano output, Pianist supports a **single Piano track** where each note (or sub-chord) can be annotated with explicit `hand` (`"lh"`/`"rh"`) and optional `voice` (1–4) via `NoteEvent` objects using the `groups` or `notes` fields.

Pianist supports tempo changes within compositions, including instant tempo changes and gradual tempo changes (ritardando/accelerando) via `TempoEvent` objects.

The prompting guide also recommends using a **system prompt** (format/schema invariants) plus a **user prompt** (musical brief) for better schema adherence.