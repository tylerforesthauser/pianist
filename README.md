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

### Gemini-connected mode (optional)

By default, Pianist is file/stdin-driven: you can paste model output into a file and run `render`.

Optionally, you can have the CLI **call Google Gemini directly** for iteration/generation workflows.

- Install the optional Gemini dependency:

```bash
python3 -m pip install -e ".[gemini]"
```

- (Optional) Install python-dotenv for `.env` file support:

```bash
python3 -m pip install python-dotenv
# or install both at once:
python3 -m pip install -e ".[gemini,dotenv]"
```

- Configure your API key using one of these methods:

**Option 1: .env file (Recommended for local development)**
```bash
# Install python-dotenv (optional but recommended)
python3 -m pip install python-dotenv

# Copy the example file and add your key
cp .env.example .env
# Edit .env and uncomment/add your API key:
# GEMINI_API_KEY=your_key_here
```

**Option 2: Environment variable (Recommended for CI/CD)**
```bash
export GEMINI_API_KEY="YOUR_KEY"
# or
export GOOGLE_API_KEY="YOUR_KEY"
```

**Note**: If both `GEMINI_API_KEY` and `GOOGLE_API_KEY` are set, `GEMINI_API_KEY` takes precedence. Environment variables override values from `.env` files.

Iterate (modify an existing seed JSON) with Gemini, saving the updated JSON, saving the raw Gemini response, and rendering to MIDI in one shot:

```bash
./pianist iterate --in seed.json --gemini --instructions "Make it more lyrical and add an 8-beat coda." \
  --out seed_updated.json --render --out-midi out.mid
```

If you provide `--out` but omit `--raw-out`, Pianist will automatically save the raw Gemini response next to your JSON as `seed_updated.json.gemini.txt`.

Analyze a reference MIDI and have Gemini generate a new inspired composition, then render:

```bash
./pianist analyze --in existing.mid --gemini --instructions "Compose a new 64-bar piece with a similar texture, but more optimistic." \
  --out composition.json --render --out-midi composition.mid
```

**Model Selection**: Both `iterate` and `analyze` commands support `--gemini-model` to choose a specific Gemini model. The default is `gemini-flash-latest` (always uses the latest Flash model). You can use other models like `gemini-1.5-pro` (more capable) or specific versions like `gemini-2.5-flash`:

```bash
./pianist iterate --in seed.json --gemini --gemini-model gemini-1.5-pro \
  --instructions "Make it more complex." --out updated.json
```

### API Key Management

For detailed information on managing API keys, including `.env` file support and best practices, see [docs/API_KEY_MANAGEMENT.md](docs/API_KEY_MANAGEMENT.md).

### Testing

Run the test suite:

```bash
# Run all unit tests (excludes integration tests)
pytest -m "not integration"

# Run only integration tests (requires API key)
pytest -m integration

# Run all tests
pytest
```

For more information on integration testing best practices, see [docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md).

### Prompt sync (keeping `AI_PROMPTING_GUIDE.md` up to date)

Canonical system prompt text lives in `src/pianist/prompts/*.txt` and is synced into `AI_PROMPTING_GUIDE.md` between markers.

```bash
make sync-prompts
make check-prompts
```

**Workflow:**
- Edit prompt text in `src/pianist/prompts/*.txt`
- Run `make sync-prompts` to update the embedded prompts in `AI_PROMPTING_GUIDE.md`
- Run `make check-prompts` to verify there is no drift

**CI:** GitHub Actions runs `python3 scripts/sync_prompts_to_guide.py --check` on PRs to prevent drift.

Iterate on an existing work by importing either a Pianist JSON (or raw LLM output text) **or a MIDI file**, emitting a clean JSON seed you can tweak and re-render:

```bash
# From MIDI -> Pianist JSON seed
./pianist iterate --in existing.mid --out seed.json

# Quick tweak example: transpose up a whole step
./pianist iterate --in seed.json --transpose 2 --out seed_transposed.json

# Generate a ready-to-paste LLM prompt (includes the seed JSON)
mkdir -p analysis
./pianist iterate --in seed.json --prompt-out analysis/iterate_prompt.txt --instructions "Make it more lyrical and add an 8-beat coda."

# Then render the updated JSON back to MIDI
./pianist render --in seed_transposed.json --out out.mid
```

Analyze an existing MIDI file to extract prompt-friendly musical constraints (tempo/time/key, note density, chord sizes, register, pedal usage, etc.) and generate a **NEW-composition prompt** inspired by that MIDI:

```bash
# Generate a ready-to-paste prompt for a NEW composition
mkdir -p analysis
./pianist analyze --in existing.mid --format prompt --prompt-out analysis/new_piece_prompt.txt \
  --instructions "Compose a new 64-bar piece with a similar texture, but more optimistic."

# Or export structured analysis JSON (for building UIs/tools)
./pianist analyze --in existing.mid --format json --out analysis/analysis.json

# Or both
./pianist analyze --in existing.mid --format both --out analysis/analysis.json --prompt-out analysis/new_piece_prompt.txt
```

Fix incorrect sustain pedal patterns in existing compositions:

```bash
# Fix pedal patterns (overwrites input)
./pianist fix-pedal --in "composition.json"

# Fix and save to new file, also render to MIDI
./pianist fix-pedal --in "composition.json" --out "composition_fixed.json" --render --out-midi "composition_fixed.mid"
```

See `docs/PEDAL_FIX_USAGE.md` for details on fixing sustain pedal patterns.
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
- `schemas/schema.openapi.json` - Full OpenAPI 3.1.0 specification
- `schemas/schema.gemini.json` - Gemini-compatible schema (inlined, ready for UI)

See `docs/SCHEMA_GENERATION.md` for detailed usage instructions with various AI models (OpenAI, Anthropic, etc.).

## Prompting

See `AI_PROMPTING_GUIDE.md` for a schema-aligned prompt template that encourages motif development and musical form.

For piano output, Pianist supports a **single Piano track** where each note (or sub-chord) can be annotated with explicit `hand` (`"lh"`/`"rh"`) and optional `voice` (1–4) via `NoteEvent` objects using the `groups` or `notes` fields.

Pianist supports tempo changes within compositions, including instant tempo changes and gradual tempo changes (ritardando/accelerando) via `TempoEvent` objects.

The prompting guide also recommends using a **system prompt** (format/schema invariants) plus a **user prompt** (musical brief) for better schema adherence.

## Dataset analysis (prompt engineering)

Generated analysis outputs should go to the (gitignored) `analysis/` directory:

```bash
mkdir -p analysis
```

Quick analysis (sanity check):

```bash
python3 scripts/quick_analysis.py ref --output analysis/ref_quick_analysis.json
```

Full dataset analysis:

```bash
python3 scripts/analyze_dataset.py ref --output analysis/ref_metrics.json --verbose
```

How to use the results:
- **Gaps / continuity**: set maximum allowed gaps between notes and between sections.
- **Transitions**: set typical transition lengths and prevent “silence transitions”.
- **Motifs / phrases**: treat as experimental unless you’ve validated the detectors on a few pieces.

Updating the system prompt from analysis:
- Edit `src/pianist/prompts/system_prompt_full.txt` / `src/pianist/prompts/system_prompt_short.txt`
- Run `make sync-prompts` and `make check-prompts`

Dataset curation prompt (short version):

```
Generate a curated list of 40-50 professional piano compositions for analyzing composition patterns. Include:

- Diversity: short (32-64 beats), medium (64-200 beats), long (200+ beats) pieces
- Various forms: binary, ternary, rondo, sonata, theme & variations, through-composed
- Multiple periods: Baroque, Classical, Romantic, Impressionist, Modern
- Mix of popular classics and lesser-known but musically significant works
- Clear formal structure with motivic development

For each piece, provide: composer, title, length category, form, period, and why it's relevant.

Prioritize well-transcribed MIDI files that are musically coherent and representative of their style.
```