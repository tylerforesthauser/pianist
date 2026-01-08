# pianist

Enable AI models to demonstrate creative musical expression through a structured format (JSON) that converts to universal MIDI files for human collaboration.

## What is Pianist?

Pianist is a composition workflow platform that creates a rock solid conduit between human composers and AI models. It enables bidirectional creative workflows where:
- **AI → Human**: AI generates musical ideas that humans can refine in their DAWs
- **Human → AI**: Humans can export their work for AI expansion and iteration

Pianist provides a shared musical vocabulary (JSON schema) that both humans and AI can use, converting between structured JSON and standard MIDI files. It integrates with AI models (Gemini, Ollama, or OpenRouter) to generate, analyze, and modify musical compositions.

### How It Works

Pianist uses AI providers to:
- Generate compositions directly from text descriptions
- Analyze MIDI files and extract musical characteristics
- Iterate on existing compositions using AI
- Expand incomplete compositions into complete works

You can also create JSON manually or import from MIDI, then use `pianist render` to convert JSON to MIDI files.

### Key Features

- **JSON → MIDI conversion**: Parses structured composition data and generates accurate MIDI files
- **AI integration**: Provider support (OpenRouter cloud - default, Gemini cloud, or Ollama local) for generating and iterating on compositions
- **Configuration system**: Set default provider and model via config files or environment variables (see [Configuration Guide](docs/guides/CONFIGURATION.md))
- **MIDI analysis**: Extract musical characteristics from existing MIDI files to inspire new compositions
- **Iteration tools**: Transpose, fix pedal patterns, and modify compositions programmatically
- **Flexible input**: Handles JSON wrapped in markdown code blocks, minor formatting issues, and raw JSON

### Use Cases

- **AI-Human Collaboration**: AI generates musical ideas that humans refine in DAWs, or humans create sketches that AI expands into complete compositions
- **Compose with AI**: Generate piano compositions using AI models and convert them to MIDI
- **Expand Incomplete Compositions**: Take a 90-second sketch "full of great ideas" and have AI expand it to a complete 5-minute composition while preserving and developing the original ideas
- **MIDI analysis**: Analyze existing MIDI files to extract musical patterns and generate new compositions
- **Composition iteration**: Refine and modify compositions through multiple iterations
- **Music production**: Create MIDI files for use in DAWs, notation software, or further processing

## Install

This project uses a Python virtual environment (`.venv`) to isolate dependencies.

```bash
# Create a virtual environment (if it doesn't exist)
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install pianist in development mode
python3 -m pip install -e ".[dev]"

# Fix entry point script (required after installation)
# This ensures the 'pianist' command works correctly with editable installs
python scripts/fix_entry_point.py
```

**Note:** All scripts and commands should be run with the virtual environment activated. The project uses `.venv` as the virtual environment directory.

**Why the fix script is needed:** When using `pyproject.toml` with `setuptools.build_meta`, the entry point script needs to be configured to process `.pth` files correctly for editable installs (especially in Python 3.14+). The `fix_entry_point.py` script handles this automatically.

## Quick Start

### Creating Your First Composition

Pianist requires an AI provider to generate compositions. The easiest way to get started is using the built-in AI providers.

**Step 1: Set up an AI provider** (see [AI Provider Setup](#ai-provider-setup) below)

**Step 2: Generate a composition**

```bash
./pianist generate --provider openrouter "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84
Style/Character: lyrical, contemplative

A gentle, flowing piece with a memorable melody that develops throughout." \
  -o composition.json --render
```

This creates:
- `output/generate-output/generate/composition.json` - The generated composition
- `output/generate-output/generate/composition.mid` - Rendered MIDI file

**Alternative: Import from MIDI**

If you have an existing MIDI file, you can import it:

```bash
./pianist import -i existing.mid -o composition.json
./pianist render -i composition.json -o out.mid
```

**Using External AI Models**

If you prefer to use external AI models (ChatGPT, Claude, etc.) to generate JSON outside of the CLI tool, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md) for comprehensive guidance on system prompts, user prompts, and examples.

## AI Provider Setup

Pianist requires an AI provider to generate, analyze, and modify compositions. Configure one of the following providers:

**💡 Tip:** You can set your default provider using the [configuration system](docs/guides/CONFIGURATION.md) so you don't need to specify `--provider` on every command.

Currently supported providers:
- **OpenRouter** (Cloud) - Unified API for hundreds of AI models, requires API key (default)
- **Gemini** (Google) - Cloud-based, requires API key
- **Ollama** (Local) - Run AI models locally, no API key needed

**Default Provider:** OpenRouter (free tier available)

### OpenRouter (Default - Recommended)

OpenRouter is the default provider and provides access to hundreds of AI models through a single API, including free options.

1. **Sign up and get an API key:**
   - Sign up at https://openrouter.ai
   - Get your API key from the dashboard

2. **Set your API key:**

**Option 1: Environment variable (Recommended)**
```bash
export OPENROUTER_API_KEY='your-api-key-here'
```

**Option 2: .env file**
```bash
# Add to .env file
OPENROUTER_API_KEY=your-api-key-here
```

3. **Use OpenRouter with pianist:**
   ```bash
   # Use OpenRouter with default model (mistralai/devstral-2512:free - free tier)
   ./pianist generate --provider openrouter "Title: Morning Sketch..." -o composition.json
   
   # Use a specific model (see https://openrouter.ai/models for available models)
   ./pianist generate --provider openrouter --model "anthropic/claude-3.5-sonnet" "Title: Morning Sketch..." -o composition.json
   ```

OpenRouter provides access to hundreds of AI models through a single API. See https://openrouter.ai/models for the full list of available models.

**Free tier options:**
- `mistralai/devstral-2512:free` (recommended, default)
- `xiaomi/mimo-v2-flash:free`
- `tngtech/deepseek-r1t2-chimera:free`
- `nex-agi/deepseek-v3.1-nex-n1:free`

### Gemini (Google)

To enable Gemini integration:

1. **Install the Gemini dependency:**
```bash
python3 -m pip install -e ".[gemini]"
```

2. **Install python-dotenv (recommended for local development):**
```bash
python3 -m pip install python-dotenv
# or install both at once:
python3 -m pip install -e ".[gemini,dotenv]"
```

3. **Configure your API key:**

**Option 1: .env file (Recommended for local development)**
```bash
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

For detailed API key management, see [docs/guides/API_KEY_MANAGEMENT.md](docs/guides/API_KEY_MANAGEMENT.md).

#### Ollama (Local AI)

Ollama allows you to run AI models locally without any API keys or rate limits. This is great for:
- Processing many files without hitting rate limits
- Keeping your data private (all processing happens locally)
- Avoiding API costs

To enable Ollama integration:

1. **Install Ollama:**
   Visit https://ollama.ai and install Ollama for your platform, or use:
   ```bash
   # macOS (using Homebrew)
   brew install ollama
   ```

2. **Start Ollama service:**
   ```bash
   ollama serve
   ```
   This starts a local server at `http://localhost:11434`

3. **Download a model:**
   ```bash
   # Primary recommendation (best quality)
   ollama pull gpt-oss:20b
   
   # Alternative options
   ollama pull gemma3:4b
   ollama pull deepseek-r1:8b
   ```

4. **Install Python requests (if not already installed):**
   ```bash
   pip install requests
   ```

5. **Use Ollama with pianist:**
   ```bash
   # Use Ollama with default model (gpt-oss:20b)
   ./pianist generate --provider ollama "Title: Morning Sketch..." -o composition.json
   
   # Use a specific model
   ./pianist generate --provider ollama --model gemma3:4b "Title: Morning Sketch..." -o composition.json
   ```

For detailed Ollama setup and usage, see [docs/guides/OLLAMA_SETUP.md](docs/guides/OLLAMA_SETUP.md).

## Core Workflows

### Command Overview

**Commands that require an AI provider:**
- `generate --provider openrouter|gemini|ollama` - Generates composition from description (default: openrouter)
- `modify --provider openrouter|gemini|ollama` - Uses AI to modify existing composition (default: openrouter)
- `analyze --ai-provider openrouter|gemini|ollama` - Uses AI for analysis insights (default: openrouter)
- `expand --provider openrouter|gemini|ollama` - Uses AI to expand incomplete compositions (default: openrouter)

**Note:** You can set default provider using the [configuration system](docs/guides/CONFIGURATION.md) so you don't need to specify `--provider` on every command.

**Commands that work without AI provider (utility commands):**
- `render` - Converts JSON to MIDI (pure conversion)
- `import` - Converts MIDI to JSON
- `fix` - Algorithmic fixes (e.g., `fix --pedal`)
- `annotate` - Marks musical intent
- `diff` - Compares compositions

### 1. Creating New Compositions

#### From Scratch

**Option 1: Generate with Built-in AI Provider**

Generate a composition directly from a text description:

```bash
# Generate and render in one command
./pianist generate --provider openrouter "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84
Style/Character: lyrical, contemplative

A gentle, flowing piece with a memorable melody that develops throughout." \
  -o composition.json --render
# MIDI path auto-generated as composition.mid
```

You can also pipe the description from stdin:

```bash
echo "Title: Evening Prelude
Form: binary
Length: ~32 beats
Key: G minor
Tempo: 100
Style/Character: dramatic, expressive" | \
  ./pianist generate --provider openrouter -o composition.json --render
```

This creates:
- `output/generate-output/generate/composition.json` - The generated composition
- `output/generate-output/generate/composition.json.<provider>.txt` - Raw AI response (e.g., `.openrouter.txt`, `.gemini.txt`, or `.ollama.txt`)
- `output/generate-output/generate/composition.mid` - Rendered MIDI file (if `--render` is used)

**Option 2: Use External AI Models**

If you prefer to use external AI models (ChatGPT, Claude, etc.) to generate JSON outside of the CLI tool, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md) for comprehensive guidance on system prompts, user prompts, and examples for generating new compositions, modifying existing ones, and creating new works from existing MIDI files.

#### From an Existing MIDI (Analysis → Generation)

**With Built-in AI Provider:**

Analyze a reference MIDI to extract musical characteristics, then generate a new composition inspired by it:

```bash
# Analyze and generate with AI provider in one command
./pianist analyze -i existing.mid --provider openrouter --instructions "Compose a new 64-bar piece with a similar texture, but more optimistic." \
  -o composition.json --render
# MIDI path auto-generated as composition.mid
```

This creates:
- `output/existing/analyze/composition.json` - The generated composition
- `output/existing/analyze/composition.json.<provider>.txt` - Raw AI response (e.g., `.openrouter.txt`, `.gemini.txt`, or `.ollama.txt`)
- `output/existing/analyze/composition.mid` - Rendered MIDI file

**Comprehensive Analysis:**

Get detailed analysis including quality assessment, musical analysis, and improvement suggestions:

```bash
# Comprehensive analysis with quality scores and improvement suggestions
./pianist analyze -i existing.mid -o analysis.json

# Human-readable text output
./pianist analyze -i existing.mid --format text

# With AI-assisted naming and description
./pianist analyze -i existing.mid --ai-naming -o analysis.json
```

### 2. Importing and Modifying Compositions

#### Import from MIDI

Convert an existing MIDI file to Pianist JSON format:

```bash
# From MIDI -> Pianist JSON
./pianist import -i existing.mid -o seed.json
```

#### Modify with AI Provider

Modify an existing composition using the built-in AI provider:

```bash
./pianist modify -i seed.json --provider openrouter --instructions "Make it more lyrical and add an 8-beat coda." \
  -o seed_updated.json --render
# MIDI path auto-generated as seed_updated.mid
```

If you provide `--output` (`-o`) but omit `--raw` (`-r`), Pianist automatically saves the raw AI response next to your JSON as `<out>.<provider>.txt` (e.g., `.openrouter.txt`, `.gemini.txt`, or `.ollama.txt`).

#### Quick Tweaks

Make simple modifications like transposition:

```bash
# Transpose up a whole step
./pianist modify -i seed.json --transpose 2 -o seed_transposed.json
```

### 2b. Annotating and Expanding Compositions

#### Mark Musical Intent

Annotate compositions to mark key ideas and expansion points:

```bash
# Mark a motif
./pianist annotate -i sketch.json --mark-motif "0-4" "Opening motif" --importance high -o annotated.json

# Mark an expansion point
./pianist annotate -i sketch.json --mark-expansion "A" --target-length 120 \
  --development-strategy "Develop opening motif with variations" -o annotated.json

# Show current annotations
./pianist annotate -i annotated.json --show
```

#### Expand Incomplete Compositions

Expand a sketch into a complete composition:

```bash
# Expand with AI provider
./pianist expand -i annotated.json --target-length 300 --provider openrouter \
  --preserve-motifs -o expanded.json --render

```

#### Compare Compositions

See what changed between compositions:

```bash
# Basic diff
./pianist diff original.json expanded.json

# Musical diff with preservation highlights
./pianist diff original.json expanded.json --musical --show-preserved

# JSON format
./pianist diff original.json expanded.json --format json -o diff.json
```

### 3. Rendering to MIDI

Convert any Pianist JSON to a MIDI file:

```bash
./pianist render -i composition.json -o out.mid
```

By default, MIDI files are saved to `output/<input-name>/render/out.mid`. You can provide an absolute path to save elsewhere.

**Note:** Use `./pianist` (recommended) or `python3 -m pianist` instead of `pianist` for maximum compatibility with editable installs.

### 4. Fixing Issues

#### Fix Composition Issues

Correct issues in compositions:

```bash
# Fix pedal patterns (overwrites input)
./pianist fix --pedal -i "composition.json"

# Fix and save to new file, also render to MIDI
./pianist fix --pedal -i "composition.json" -o "composition_fixed.json" --render
# MIDI path auto-generated as composition_fixed.mid

# Fix all available issues
./pianist fix --all -i "composition.json"
```

See [`docs/guides/PEDAL_FIX_USAGE.md`](docs/guides/PEDAL_FIX_USAGE.md) for details on fixing sustain pedal patterns.

## Building Effective Prompts

When working with AI providers, you can phrase your request naturally—the model will interpret it. You don't need to include all parameters; provide only what matters to you.

**Example prompt:**
```
Title: "Morning Sketch"
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84
Style/Character: lyrical, contemplative

A gentle, flowing piece with a memorable melody that develops throughout.
```

**Quick parameter reference:**
- **Form**: binary, ternary, rondo, sonata, theme and variations, free-form
- **Length**: ~64 beats (short), ~200 beats (extended), or describe in words
- **Key**: "C", "Gm", "F#", "Bb" (major keys are brighter, minor keys are darker)
- **Tempo**: 84 (BPM), or describe as "slow", "moderate", "fast"
- **Style**: lyrical, dramatic, playful, contemplative, energetic, etc.

**Tips for better results:**
- Request "continuous music with no gaps between sections" for smooth transitions
- Request "regular phrase lengths (4, 8, or 16 beats)" for structural clarity
- For longer works, emphasize that all themes should relate through motivic development

**For external AI workflows:** If you're using external AI models (ChatGPT, Claude, etc.) to generate JSON outside of the CLI tool, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md) for comprehensive guidance including system prompt templates, detailed examples, and tips for different musical styles and forms.

## Advanced Features

### Output Directory Structure

By default, all generated files are saved to the `output/` directory, organized by input file name and then by command:

- `output/<base-name>/<command>/` - Contains all output files for a command run
  - `<base-name>` is derived from the input file name (without extension)
  - `<command>` is the command name (e.g., `render`, `import`, `modify`, `analyze`, `fix`, `generate`, `annotate`, `expand`, `diff`)

**Why this structure?** This groups all operations on the same source material together, making it easy to find related files. For example, if you analyze `song.mid` and then iterate on it, both operations will be under `output/song/`, just in different command subdirectories. This also prevents filename conflicts between commands (e.g., both `analyze` and `iterate` might create `composition.json`).

**Cross-command workflows:** If you use an output file as input to another command, the system will detect if it's already in the output directory and maintain the same base name. For example:
- `analyze -i song.mid -o analysis.json` → `output/song/analyze/analysis.json`
- `modify -i output/song/analyze/analysis.json -o comp.json` → `output/song/modify/comp.json`

**Note:** If you provide an absolute path (e.g., `/path/to/file.json`), it will be used as-is. Relative paths are resolved relative to the output directory structure.

### File Versioning

By default, if an output file already exists, Pianist will automatically create a versioned copy instead of overwriting it. This preserves your previous results when iterating on the same input with different instructions.

**Versioning behavior:**
- If `updated.json` exists, the next run creates `updated.v2.json`, then `updated.v3.json`, etc.
- The raw AI response (`.<provider>.txt`, e.g., `.openrouter.txt`, `.gemini.txt`, or `.ollama.txt`) is automatically versioned to match the JSON file
- Use `--overwrite` to explicitly overwrite existing files instead of versioning

**Example:**
```bash
# First run
./pianist modify -i seed.json -o updated.json --provider gemini --instructions "Make it faster"
# Creates: output/seed/modify/updated.json and updated.json.gemini.txt

# Second run with different instructions
./pianist modify -i seed.json -o updated.json --provider gemini --instructions "Make it slower"
# Creates: output/seed/modify/updated.v2.json and updated.v2.json.gemini.txt
# Original files are preserved

# To overwrite instead
./pianist modify -i seed.json -o updated.json --provider gemini --instructions "Try again" --overwrite
# Overwrites: output/seed/modify/updated.json
```

### Model Selection

The `generate`, `modify`, `analyze`, and `expand` commands support `--model` to choose a specific model for the provider.

**For OpenRouter (Recommended):**

**Free tier options** (default: `mistralai/devstral-2512:free`):
- `mistralai/devstral-2512:free` (recommended, default) - 262K context window
- `xiaomi/mimo-v2-flash:free`
- `tngtech/deepseek-r1t2-chimera:free`
- `nex-agi/deepseek-v3.1-nex-n1:free`

**Paid models** (higher quality, see [OpenRouter pricing](https://openrouter.ai/models)):
- `anthropic/claude-sonnet-4.5` - Excellent for complex compositions (recommended, best balance)
- `anthropic/claude-opus-4.5` - Most capable, best for large-scale works
- `anthropic/claude-3.5-sonnet` - Previous generation (still available, lower cost)
- `openai/gpt-4o` - Strong general performance
- `google/gemini-2.5-flash` - Fast and capable (via OpenRouter)

**Find latest models:** See [OpenRouter Models](https://openrouter.ai/models) for the complete list of available models, pricing, and updates.

**For Ollama (Local):**
- Default: `gpt-oss:20b` (best quality for composition tasks)
- Other options: `gemma3:4b` (faster, smaller), `deepseek-r1:8b` (excellent reasoning)

**Find latest models:** See [Ollama Library](https://ollama.ai/library) for available models and download commands.

**For Gemini (Google):**
- Default: `gemini-flash-latest` (uses latest Flash model, currently maps to `gemini-2.5-flash`)
- **Current stable models** (shutdown dates: June-July 2026):
  - `gemini-2.5-flash` (recommended, best balance of speed and quality)
  - `gemini-2.5-pro` (more capable, best for complex compositions)
  - `gemini-2.5-flash-lite` (cost-efficient, high throughput)
- **Preview models** (future replacements):
  - `gemini-3-flash-preview` (preview of next Flash model)
  - `gemini-3-pro` (preview of next Pro model)
- **Note**: Gemini 2.0 models are deprecated (shutdown February 2026). See [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations) for details.

**Find latest models:** See [Gemini API Models](https://ai.google.dev/gemini-api/docs/models/gemini) for current models, capabilities, and [deprecation schedule](https://ai.google.dev/gemini-api/docs/deprecations).

```bash
# Generate with OpenRouter using free model (default)
./pianist generate --provider openrouter \
  "Compose a complex sonata in C minor" -o composition.json

# Generate with OpenRouter using paid model
./pianist generate --provider openrouter --model "anthropic/claude-3.5-sonnet" \
  "Compose a complex sonata in C minor" -o composition.json

# Generate with Ollama using a specific model
./pianist generate --provider ollama --model gemma3:4b \
  "Compose a complex sonata in C minor" -o composition.json

# Generate with Gemini using latest model
./pianist generate --provider gemini --model "gemini-2.5-pro" \
  "Compose a complex sonata in C minor" -o composition.json

# Iterate with a specific model
./pianist modify -i seed.json --provider openrouter --model "anthropic/claude-3.5-sonnet" \
  --instructions "Make it more complex." -o updated.json
```

## Reference

### Python API

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

### Schema and Format Reference

For piano output, Pianist supports a **single Piano track** where each note (or sub-chord) can be annotated with explicit `hand` (`"lh"`/`"rh"`) and optional `voice` (1–4) via `NoteEvent` objects using the `groups` or `notes` fields.

Pianist supports tempo changes within compositions, including instant tempo changes and gradual tempo changes (ritardando/accelerando) via `TempoEvent` objects.

**For external AI workflows:** If you're using external AI models to generate JSON outside of the CLI tool, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md) for comprehensive guidance including system prompt templates, user prompt examples, and tips for generating new compositions, modifying existing ones, and creating new works from existing MIDI files.

## Development

### Testing

Run the test suite:

```bash
# Run all unit tests (excludes integration tests)
pytest -m "not integration"

# Run tests in parallel for faster execution (recommended)
pytest -m "not integration" -n auto

# Run only failed tests (faster iteration during development)
pytest -m "not integration" --lf

# Run only integration tests (requires API key)
pytest -m integration

# Run all tests
pytest
```

**Performance:** The test suite uses `pytest-xdist` for parallel execution. Use `-n auto` to automatically use all CPU cores, which can reduce test runtime from ~3 minutes to under 90 seconds on multi-core systems. Module-scoped fixtures are used to cache expensive operations like music21 stream conversions.

For more information on integration testing best practices, see [docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md).

### Prompt Sync (keeping `AI_PROMPTING_GUIDE.md` up to date)

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

### Dataset Analysis (Prompt Engineering)

Generated analysis outputs should go to the (gitignored) `output/analysis/` directory:

```bash
mkdir -p output/analysis
```

Quick analysis (sanity check):

```bash
python3 scripts/quick_analysis.py ref --output output/analysis/ref_quick_analysis.json
```

Full dataset analysis:

```bash
python3 scripts/analyze_dataset.py ref --output output/analysis/ref_metrics.json --verbose
```

How to use the results:
- **Gaps / continuity**: set maximum allowed gaps between notes and between sections.
- **Transitions**: set typical transition lengths and prevent "silence transitions".
- **Motifs / phrases**: treat as experimental unless you've validated the detectors on a few pieces.

Updating the system prompt from analysis:
- Edit `src/pianist/prompts/system_prompt.txt`
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
