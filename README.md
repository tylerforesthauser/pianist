# pianist

Enable AI models to demonstrate creative musical expression through a structured format (JSON) that converts to universal MIDI files for human collaboration.

## What is Pianist?

Pianist is a composition workflow platform that creates a rock solid conduit between human composers and AI models. It enables bidirectional creative workflows where:
- **AI → Human**: AI generates musical ideas that humans can refine in their DAWs
- **Human → AI**: Humans can export their work for AI expansion and iteration

Pianist provides a shared musical vocabulary (JSON schema) that both humans and AI can use, converting between structured JSON and standard MIDI files. It works seamlessly with AI models (like ChatGPT, Claude, Gemini, etc.) that can generate musical compositions in JSON format, but it also works perfectly fine without any AI—you can create JSON manually, import from MIDI, or use any external AI tool.

### How It Works

**Without AI (Core Functionality):**
1. **Create or import JSON**: Write JSON manually, import from MIDI, or get it from any external AI tool
2. **Render to MIDI**: Use `pianist render` to convert the JSON into a standard MIDI file
3. **Iterate & Refine**: Modify compositions, transpose, fix issues programmatically

**With AI Provider (Optional):**
- Generate compositions directly from text descriptions
- Iterate on existing compositions using AI
- Analyze MIDI files and generate new compositions inspired by them

### Key Features

- **JSON → MIDI conversion**: Parses structured composition data and generates accurate MIDI files
- **AI integration**: Optional provider support (Gemini cloud or Ollama local) for generating and iterating on compositions directly
- **MIDI analysis**: Extract musical characteristics from existing MIDI files to inspire new compositions
- **Iteration tools**: Transpose, fix pedal patterns, and modify compositions programmatically
- **Flexible input**: Handles JSON wrapped in markdown code blocks, minor formatting issues, and raw JSON
- **Works standalone**: All core features work without any AI provider—AI is completely optional

### Use Cases

- **AI-Human Collaboration**: AI generates musical ideas that humans refine in DAWs, or humans create sketches that AI expands into complete compositions
- **Compose with AI**: Generate piano compositions using AI models and convert them to MIDI
- **Expand Incomplete Compositions**: Take a 90-second sketch "full of great ideas" and have AI expand it to a complete 5-minute composition while preserving and developing the original ideas
- **MIDI analysis**: Analyze existing MIDI files to extract musical patterns and generate prompts for new compositions
- **Composition iteration**: Refine and modify compositions through multiple iterations
- **Music production**: Create MIDI files for use in DAWs, notation software, or further processing
- **Manual composition**: Create JSON manually and render to MIDI without any AI

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
```

**Note:** All scripts and commands should be run with the virtual environment activated. The project uses `.venv` as the virtual environment directory.

## Quick Start

### Creating Your First Composition

Pianist works with JSON compositions. You can get JSON from:
- **External AI models** (ChatGPT, Claude, etc.) - see [AI_PROMPTING_GUIDE.md](AI_PROMPTING_GUIDE.md)
- **Built-in AI providers** (Gemini cloud or Ollama local) - requires setup (see below)
- **Manual creation** - write JSON yourself
- **MIDI import** - convert existing MIDI files to JSON

**Step 1: Get JSON** (choose one method)

**Option A: Use external AI** (no setup required)
Use your preferred AI model with the two-part prompt structure:

**System prompt** (copy from `AI_PROMPTING_GUIDE.md` Part 2):
```
[Copy the system prompt template from AI_PROMPTING_GUIDE.md]
```

**User prompt** (example):
```
Compose a piano piece:

Title: "Morning Sketch"
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84
Style/Character: lyrical, contemplative

A gentle, flowing piece with a memorable melody that develops throughout.
```

Save the model's JSON output to a file (e.g., `composition.json`).

**Option B: Use built-in AI provider** (requires setup, see below)
```bash
./pianist generate --provider gemini "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84
Style/Character: lyrical, contemplative" -o composition.json
```

**Option C: Generate prompt template** (no AI needed)
```bash
./pianist generate "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -o prompt.txt
```
Then paste the prompt into your preferred AI model.

**Step 2: Render to MIDI**

```bash
./pianist render -i composition.json -o out.mid
```

This parses the JSON (even if it's wrapped in markdown code blocks) and creates a playable MIDI file.

**For detailed prompting guidance**, including system prompt templates, user prompt examples, and tips for different musical styles, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md).

## AI Provider Setup (Optional)

Pianist can call AI providers directly to generate or modify compositions. This is completely optional—you can always use external AI tools or create JSON manually.

Currently supported providers:
- **Gemini** (Google) - Cloud-based, requires API key
- **Ollama** (Local) - Run AI models locally, no API key needed

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

For detailed API key management, see [docs/API_KEY_MANAGEMENT.md](docs/API_KEY_MANAGEMENT.md).

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

### Understanding AI vs Non-AI Workflows

**Commands that work WITHOUT any AI provider:**
- `render` - Always works (pure JSON→MIDI conversion)
- `import` - Always works (converts MIDI→JSON)
- `modify` - Works without `--provider` (transposes, generates prompts)
- `fix` - Always works (algorithmic fixes, e.g., `fix --pedal`)
- `analyze` - Works without `--provider` (extracts analysis, generates prompts)
- `generate` - Works without `--provider` (generates prompt templates)
- `annotate` - Always works (marks musical intent)
- `expand` - Works without `--provider` (generates expansion strategy)
- `diff` - Always works (compares compositions)

**Commands that can USE an AI provider (optional):**
- `generate --provider gemini|ollama` - Generates composition from description
- `modify --provider gemini|ollama` - Uses AI to modify existing composition
- `analyze --provider gemini|ollama` - Uses AI to generate new composition from analysis
- `expand --provider gemini|ollama` - Uses AI to expand incomplete compositions

### 1. Creating New Compositions

#### From Scratch

**Option 1: Generate with Built-in AI Provider**

Generate a composition directly from a text description:

```bash
# Generate and render in one command
./pianist generate --provider gemini "Title: Morning Sketch
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
  ./pianist generate --provider gemini -o composition.json --render
```

This creates:
- `output/generate-output/generate/composition.json` - The generated composition
- `output/generate-output/generate/composition.json.gemini.txt` - Raw AI response
- `output/generate-output/generate/composition.mid` - Rendered MIDI file (if `--render` is used)

**Option 2: Generate Prompt Template (No AI Required)**

Generate a ready-to-paste prompt for use with external AI:

```bash
./pianist generate "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84
Style/Character: lyrical, contemplative" -o prompt.txt
```

Then paste the prompt into your preferred AI model (ChatGPT, Claude, etc.) and render the result.

**Option 3: Use External AI Directly**

Use the two-part prompt structure (system + user prompts) described in the Quick Start section. For comprehensive guidance, examples, and system prompt templates, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md).

#### From an Existing MIDI (Analysis → Generation)

**With Built-in AI Provider:**

Analyze a reference MIDI to extract musical characteristics, then generate a new composition inspired by it:

```bash
# Analyze and generate with AI provider in one command
./pianist analyze -i existing.mid --provider gemini --instructions "Compose a new 64-bar piece with a similar texture, but more optimistic." \
  -o composition.json --render
# MIDI path auto-generated as composition.mid
```

This creates:
- `output/existing/analyze/composition.json` - The generated composition
- `output/existing/analyze/composition.json.gemini.txt` - Raw AI response
- `output/existing/analyze/composition.mid` - Rendered MIDI file

**Without AI Provider (Generate Prompt for External AI):**

If you prefer to use a different AI model, generate a ready-to-paste prompt:

```bash
# Generate a prompt for a NEW composition
mkdir -p analysis
./pianist analyze -i existing.mid -f prompt -p analysis/new_piece_prompt.txt \
  --instructions "Compose a new 64-bar piece with a similar texture, but more optimistic."

# Or export structured analysis JSON (for building UIs/tools)
./pianist analyze -i existing.mid -f json -o analysis/analysis.json

# Or both
./pianist analyze -i existing.mid -f both -o analysis/analysis.json -p analysis/new_piece_prompt.txt
```

Then paste the prompt into your preferred AI model and render the result.

### 2. Importing and Modifying Compositions

#### Import from MIDI (No AI Required)

Convert an existing MIDI file to Pianist JSON format:

```bash
# From MIDI -> Pianist JSON
./pianist import -i existing.mid -o seed.json
```

#### Modify with AI Provider

Modify an existing composition using the built-in AI provider:

```bash
./pianist modify -i seed.json --provider gemini --instructions "Make it more lyrical and add an 8-beat coda." \
  -o seed_updated.json --render
# MIDI path auto-generated as seed_updated.mid
```

If you provide `--output` (`-o`) but omit `--raw` (`-r`), Pianist automatically saves the raw AI response next to your JSON as `<out>.gemini.txt`.

#### Quick Tweaks (No AI Required)

Make simple modifications without using AI:

```bash
# Transpose up a whole step
./pianist modify -i seed.json --transpose 2 -o seed_transposed.json
```

#### Generate Modification Prompt for External AI (No AI Required)

Create a ready-to-paste prompt for modifying a composition:

```bash
mkdir -p analysis
./pianist modify -i seed.json -p analysis/modify_prompt.txt --instructions "Make it more lyrical and add an 8-beat coda."
```

Then paste the prompt into your preferred AI model and render the result.

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
./pianist expand -i annotated.json --target-length 300 --provider gemini \
  --preserve-motifs -o expanded.json --render

# Or just generate expansion strategy (no AI)
./pianist expand -i annotated.json --target-length 300 -o strategy.json
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

Convert any Pianist JSON to a MIDI file (always works, no AI required):

```bash
./pianist render -i composition.json -o out.mid
```

By default, MIDI files are saved to `output/<input-name>/render/out.mid`. You can provide an absolute path to save elsewhere.

**Note:** Use `./pianist` (recommended) or `python3 -m pianist` instead of `pianist` for maximum compatibility with editable installs.

### 4. Fixing Issues

#### Fix Composition Issues (No AI Required)

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

See `docs/PEDAL_FIX_USAGE.md` for details on fixing sustain pedal patterns.

## Building Effective Prompts

When working with AI (either built-in provider or external), the key to success is splitting your prompt into two parts:

- **System prompt (model-facing)**: Stable "rules of the game" (format + schema constraints). Typically fixed and reused.
- **User prompt (model-facing)**: Your musical brief (style, form, length, key, tempo, etc.). This is where you specify what you want.

This two-part approach typically improves **schema adherence** and reduces output drift compared to a single combined prompt.

### User Prompt Template

You can phrase your request naturally—the model will interpret it. You don't need to include all parameters; provide only what matters to you.

**Template structure:**

```
[OPTIONAL OPENING - phrase naturally]
Compose a piano piece: or I'd like a piano piece or Create a piano composition or just start with the title

Title: "Morning Sketch" or "Sonata in C Minor"

[OPTIONAL SPECIFICATIONS - include only what you want to specify]
- Form: binary | ternary/ABA | rondo | sonata | theme and variations | free-form
- Length: ~64 beats or ~200 beats (or describe: "short piece", "extended work", etc.)
- Key: "C" | "Gm" | "F#" | "Bb"
- Tempo: 84 | 120 | 160 (BPM, or describe: "slow", "moderate", "fast")
- Time signature: 4/4 | 3/4 | 6/8
- Style/Character: lyrical | dramatic | playful | contemplative | energetic | [your description]

[DESCRIPTION - describe what you want in natural language]
A gentle, flowing piece with a memorable melody that develops throughout.
```

### Quick Reference: Choosing Parameters

**Form:**
- **binary (A-B)**: Simple two-section structure. Good for short pieces (32-64 beats).
- **ternary (A-B-A)**: Three-part form with a return. Classic structure for character pieces (48-128 beats).
- **rondo**: Recurring main theme alternates with contrasting episodes. Good for lively, dance-like pieces.
- **sonata form**: Large-scale form (150-300+ beats) with exposition, development, and recapitulation.
- **theme and variations**: A clear theme followed by variations that transform it.

**Key:**
- **Major keys** (C, G, D, F, Bb): Generally brighter, more optimistic, or energetic.
- **Minor keys** (Am, Dm, Gm, Cm): Generally darker, more emotional, or introspective.

**Tempo (BPM):**
- **Very slow (40-60)**: Grave, largo. For solemn, meditative pieces.
- **Slow (60-80)**: Adagio, andante. For lyrical, contemplative pieces.
- **Moderate (80-100)**: Moderato. Balanced, comfortable pace.
- **Moderately fast (100-120)**: Allegretto. Light, flowing.
- **Fast (120-160)**: Allegro. Energetic, exciting.
- **Very fast (160+)**: Presto, vivace. Brilliant, virtuosic.

**Style/Character:**
- **lyrical**: Song-like, melodic, expressive
- **dramatic**: Intense, emotional, with strong contrasts
- **playful**: Light, cheerful, with bouncy rhythms
- **contemplative**: Thoughtful, introspective, often slower
- **energetic**: Fast, active, with driving rhythms

**Important considerations for cohesive compositions:**
- **Thematic coherence**: When requesting longer works, emphasize that all themes should relate through motivic development.
- **Continuous music**: Request "continuous music with no gaps between sections" or "smooth transitions throughout."
- **Regular phrase structure**: Request "regular phrase lengths (4, 8, or 16 beats)" for structural clarity.

For comprehensive prompting guidance, including detailed examples, system prompt templates, and tips for different musical styles, see [`AI_PROMPTING_GUIDE.md`](AI_PROMPTING_GUIDE.md).

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
- The raw AI response (`.gemini.txt`) is automatically versioned to match the JSON file
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

**For Gemini:**
- Default: `gemini-flash-latest` (always uses the latest Flash model)
- Other options: `gemini-1.5-pro` (more capable), `gemini-2.5-flash` (specific version)

**For Ollama:**
- Default: `gpt-oss:20b` (best quality for composition tasks)
- Other options: `gemma3:4b` (faster, smaller), `deepseek-r1:8b` (excellent reasoning)

```bash
# Generate with Gemini using a specific model
./pianist generate --provider gemini --model gemini-1.5-pro \
  "Compose a complex sonata in C minor" -o composition.json

# Generate with Ollama using a specific model
./pianist generate --provider ollama --model gemma3:4b \
  "Compose a complex sonata in C minor" -o composition.json

# Iterate with a specific model
./pianist modify -i seed.json --provider gemini --model gemini-1.5-pro \
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

### Prompting Guide

See `AI_PROMPTING_GUIDE.md` for a comprehensive schema-aligned prompt template that encourages motif development and musical form.

For piano output, Pianist supports a **single Piano track** where each note (or sub-chord) can be annotated with explicit `hand` (`"lh"`/`"rh"`) and optional `voice` (1–4) via `NoteEvent` objects using the `groups` or `notes` fields.

Pianist supports tempo changes within compositions, including instant tempo changes and gradual tempo changes (ritardando/accelerando) via `TempoEvent` objects.

The prompting guide also recommends using a **system prompt** (format/schema invariants) plus a **user prompt** (musical brief) for better schema adherence.

## Development

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
- **Transitions**: set typical transition lengths and prevent "silence transitions".
- **Motifs / phrases**: treat as experimental unless you've validated the detectors on a few pieces.

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
