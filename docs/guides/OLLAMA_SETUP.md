# Using Ollama for Local AI Composition Identification

This guide explains how to use Ollama (local AI models) instead of Gemini API to avoid rate limits and reduce costs when reviewing MIDI files.

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
# Small, fast model (good for testing)
ollama pull llama3.2

# Medium model (better quality)
ollama pull mistral

# Larger model (best quality, slower)
ollama pull llama3.1
```

**Recommended for composition identification**: `llama3.2` or `mistral` - they're fast and work well for structured JSON output.

### 4. Install Python Requests (if not already installed)

```bash
pip install requests
```

## Usage

### Basic Usage with Ollama

```bash
# Use Ollama with default model (llama3.2)
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider ollama \
  --output review_report.csv
```

### Specify a Different Model

```bash
# Use a specific Ollama model
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider ollama \
  --ai-model mistral \
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
export AI_MODEL=llama3.2
export AI_DELAY_SECONDS=0

# Then run without flags
python3 scripts/review_and_categorize_midi.py --dir input/ --ai --output review_report.csv
```

## Available Models

### Recommended Models for Composition Identification

1. **llama3.2** (2B parameters)
   - Fast, good for structured output
   - ~1.3GB download
   - Good balance of speed and quality

2. **mistral** (7B parameters)
   - Better quality than llama3.2
   - ~4.1GB download
   - Slower but more accurate

3. **phi3** (3.8B parameters)
   - Fast and efficient
   - ~2.3GB download
   - Good for JSON generation

### Other Models

- `llama3.1` - Larger, higher quality (8B, ~4.7GB)
- `gemma2` - Google's model (2B, ~1.4GB)
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
ollama pull llama3.2
```

### Slow Performance

- Use a smaller model (llama3.2 instead of llama3.1)
- Ensure you have enough RAM (models load into memory)
- Close other applications

### JSON Parsing Errors

Local models sometimes produce less structured JSON than Gemini. The script will fall back to filename-based identification if JSON parsing fails.

## Custom Ollama URL

If Ollama is running on a different host/port:

```bash
export OLLAMA_URL=http://192.168.1.100:11434
python3 scripts/review_and_categorize_midi.py --dir input/ --ai --ai-provider ollama
```

## Tips

1. **Start with llama3.2**: It's fast and works well for most cases
2. **Use Gemini for difficult cases**: If Ollama can't identify something, you can manually run with Gemini
3. **Batch processing**: Ollama has no rate limits, so you can process all 150 files at once
4. **Resume capability**: The script saves progress, so you can always resume if interrupted

## Example Workflow

```bash
# 1. Start Ollama
ollama serve

# 2. Download model (one-time)
ollama pull llama3.2

# 3. Review all files with Ollama (no rate limits!)
python3 scripts/review_and_categorize_midi.py \
  --dir input/ \
  --ai \
  --ai-provider ollama \
  --ai-model llama3.2 \
  --output full_review.csv \
  --verbose

# 4. Review the CSV and manually fix any misidentifications
```

## See Also

- [Ollama Documentation](https://ollama.ai/docs)
- [Available Models](https://ollama.ai/library)
- [REFERENCE_DATABASE_CURATION.md](REFERENCE_DATABASE_CURATION.md) - Main curation guide

