# Using Ollama for Local AI

This guide explains how to use Ollama (local AI models) instead of Gemini API to avoid rate limits and reduce costs. Ollama can be used with all AI-enabled commands in pianist: `generate`, `modify`, `analyze`, `expand`, and the MIDI quality check script.

## Why Use Ollama?

- **No rate limits**: Process unlimited files without API quotas
- **Free**: No API costs
- **Private**: All processing happens locally
- **Fast**: No network latency (after initial model download)

## Setup

### 1. Install Ollama

Visit https://ollama.ai and install Ollama for your platform:

```bash
# macOS (using Homebrew)
brew install ollama

# Or download from https://ollama.ai
```

### 2. Start Ollama

```bash
# Start the Ollama service
ollama serve
```

This starts a local server at `http://localhost:11434`

### 3. Download a Model

Download a model suitable for text generation. Recommended models:

```bash
# Primary recommendation (best quality for composition tasks)
ollama pull gpt-oss:20b

# Alternative options (good quality, different trade-offs)
ollama pull gemma3:4b
ollama pull deepseek-r1:8b
```

**Recommended for composition tasks**: `gpt-oss:20b` provides the best quality for musical composition generation and analysis. Alternatives `gemma3:4b` (faster, smaller) and `deepseek-r1:8b` (excellent reasoning) are also excellent choices.

### 4. Install Python Requests (if not already installed)

```bash
pip install requests
```

## Usage

Ollama can be used with all AI-enabled commands in pianist:

### Generate Command

```bash
# Generate a composition with Ollama
./pianist generate --provider ollama "Title: Morning Sketch
Form: ternary
Length: ~64 beats
Key: C major
Tempo: 84" -o composition.json --render

# Use a specific model
./pianist generate --provider ollama --model mistral "Title: Test..." -o composition.json
```

### Modify Command

```bash
# Modify a composition with Ollama
./pianist modify -i seed.json --provider ollama \
  --instructions "Make it more lyrical" -o updated.json
```

### Analyze Command

```bash
# Comprehensive analysis with quality assessment and improvement suggestions
./pianist analyze -i existing.mid -o analysis.json

# Human-readable text output
./pianist analyze -i existing.mid --format text

# With AI-assisted naming using Ollama
./pianist analyze -i existing.mid --ai-naming --ai-provider ollama -o analysis.json

# Analyze and generate new composition with Ollama
./pianist analyze -i existing.mid --provider ollama \
  --instructions "Compose something similar" -o new_composition.json
```

### Expand Command

```bash
# Expand a composition with Ollama
./pianist expand -i sketch.json --target-length 300 \
  --provider ollama -o expanded.json --render
```

### MIDI Quality Check Script

```bash
# Use Ollama with default model (gpt-oss:20b)
python3 scripts/check_midi_quality.py file.mid --ai --provider ollama

# Use a specific model
python3 scripts/check_midi_quality.py file.mid --ai --provider ollama --model mistral
```

### Review and Categorize MIDI Script

```bash
# Use Ollama with default model (gpt-oss:20b)
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider ollama \
  --output review_report.csv

# Use a specific Ollama model
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider ollama \
  --ai-model gemma3:4b \
  --output review_report.csv
```

### With Rate Limiting (for Gemini)

If you want to use Gemini but avoid rate limits:

```bash
# Add delay between API calls (2 seconds)
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider gemini \
  --ai-delay 2.0 \
  --output review_report.csv
```

### Environment Variables

You can also set defaults via environment variables:

```bash
# Set default provider
export AI_PROVIDER=ollama
export AI_MODEL=gpt-oss:20b
export AI_DELAY_SECONDS=0

# Then run without flags
python3 scripts/review_and_categorize_midi.py --dir input/ --ai --output review_report.csv
```

## Available Models

### Recommended Models for Composition Tasks

1. **gpt-oss:20b** (20B parameters) ⭐ **PRIMARY RECOMMENDATION**
   - Best quality for musical composition and analysis
   - Excellent at structured JSON output
   - Strong reasoning and creative capabilities
   - ~12GB download
   - Recommended for all composition tasks

2. **gemma3:4b** (4B parameters)
   - Fast and efficient
   - Good quality for structured output
   - ~2.5GB download
   - Good balance of speed and quality

3. **deepseek-r1:8b** (8B parameters)
   - Excellent reasoning capabilities
   - Strong at complex tasks
   - ~4.8GB download
   - Great for analytical composition tasks

### Other Models

- `llama3.2` - Fast, small (3B, ~2GB) - good for quick tests
- `mistral` - Solid general purpose (7B, ~4.1GB)
- `llama3.1` - Larger, higher quality (8B, ~4.7GB)
- `qwen2.5` - Good multilingual support

## Performance Comparison

| Provider | Speed | Cost | Rate Limits | Quality |
|----------|-------|------|-------------|---------|
| Gemini (free) | Fast | Free | 20/day | Excellent |
| Gemini (paid) | Fast | $ | Higher limits | Excellent |
| Ollama (local) | Medium | Free | None | Good |

## Troubleshooting

### "Could not connect to Ollama"

Make sure Ollama is running:
```bash
ollama serve
```

Check if it's running:
```bash
curl http://localhost:11434/api/tags
```

### "Model not found"

Download the model first:
```bash
ollama pull gpt-oss:20b
# or for alternatives:
ollama pull gemma3:4b
ollama pull deepseek-r1:8b
```

### Slow Performance

- Use a smaller model (gemma3:4b instead of gpt-oss:20b)
- Ensure you have enough RAM (models load into memory)
- Close other applications
- Consider using `deepseek-r1:8b` for a balance of quality and speed

### JSON Parsing Errors

Local models sometimes produce less structured JSON than Gemini. The script will fall back to filename-based identification if JSON parsing fails.

## Custom Ollama URL

If Ollama is running on a different host/port:

```bash
export OLLAMA_URL=http://192.168.1.100:11434
python3 scripts/review_and_categorize_midi.py --dir input/ --ai --ai-provider ollama
```

## Tips

1. **Start with gpt-oss:20b**: Best quality for composition tasks, excellent at structured output
2. **Use alternatives for speed**: `gemma3:4b` is faster if you need quicker responses
3. **Use deepseek-r1:8b for reasoning**: Excellent for complex analytical tasks
4. **Batch processing**: Ollama has no rate limits, so you can process all files at once
5. **Resume capability**: Scripts save progress, so you can always resume if interrupted

## Example Workflow

```bash
# 1. Start Ollama
ollama serve

# 2. Download model (one-time)
ollama pull gpt-oss:20b

# 3. Review all files with Ollama (no rate limits!)
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider ollama \
  --ai-model gpt-oss:20b \
  --output full_review.csv \
  --verbose

# 4. Review the CSV and manually fix any misidentifications
```

## See Also

- [Ollama Documentation](https://ollama.ai/docs)
- [Available Models](https://ollama.ai/library)
- [REFERENCE_DATABASE_CURATION.md](REFERENCE_DATABASE_CURATION.md) - Main curation guide

