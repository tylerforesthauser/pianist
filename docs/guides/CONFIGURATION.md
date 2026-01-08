# Configuration Guide

Pianist supports a global configuration system for AI provider and model settings. This allows you to set your preferred defaults once and have them apply across all commands, while still being able to override them per-command when needed.

## Configuration Priority

Settings are resolved in the following order (highest to lowest priority):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **User config file** (`~/.pianist/config.toml`)
4. **Project config file** (`.pianist/config.toml` in project root)
5. **Defaults** (lowest priority)

## Configuration Files

### User Config File

Create a config file at `~/.pianist/config.toml` to set global defaults:

```toml
[ai]
provider = "gemini"
model = "gemini-flash-latest"
delay = 0.0

# Or specify provider-specific models:
[ai.models]
gemini = "gemini-flash-latest"
ollama = "gpt-oss:20b"
openrouter = "mistralai/devstral-2512:free"
```

### Project Config File

Create a config file at `.pianist/config.toml` in your project root to set project-specific defaults:

```toml
[ai]
provider = "ollama"
model = "gpt-oss:20b"
```

Project config overrides user config, but both are overridden by command-line arguments.

## Environment Variables

You can also set defaults using environment variables:

```bash
export AI_PROVIDER="gemini"
export AI_MODEL="gemini-flash-latest"
export AI_DELAY_SECONDS="0.5"
```

Environment variables override config files but are overridden by command-line arguments.

## Examples

### Setting Global Defaults

```bash
# Create user config
mkdir -p ~/.pianist
cat > ~/.pianist/config.toml << EOF
[ai]
provider = "gemini"
model = "gemini-flash-latest"
EOF

# Now all commands use these defaults
pianist analyze -i file.mid
pianist generate --description "A waltz"
pianist expand -i comp.json --target-length 100
```

### Overriding Per-Command

```bash
# Use different provider for this command
pianist analyze -i file.mid --ai-provider ollama

# Use different model for this command
pianist generate --description "A waltz" --model "gemini-pro"
```

### Project-Specific Config

```bash
# In your project root
mkdir -p .pianist
cat > .pianist/config.toml << EOF
[ai]
provider = "ollama"
model = "gpt-oss:20b"
EOF

# Commands in this project use Ollama by default
pianist analyze -i file.mid
```

### Using Environment Variables

```bash
# Set for this session
export AI_PROVIDER="openrouter"
export AI_MODEL="mistralai/devstral-2512:free"

# All commands use OpenRouter
pianist analyze -i file.mid
pianist generate --description "A waltz"
```

## Configuration Options

### `provider`

The AI provider to use: `"gemini"`, `"ollama"`, or `"openrouter"`.

### `model`

The model name to use. If not specified, defaults to provider-specific defaults:
- Gemini: `"gemini-flash-latest"`
- Ollama: `"gpt-oss:20b"`
- OpenRouter: `"mistralai/devstral-2512:free"`

You can specify a global model or provider-specific models:

```toml
# Global model (used for all providers)
[ai]
model = "gemini-flash-latest"

# Or provider-specific models
[ai.models]
gemini = "gemini-flash-latest"
ollama = "gpt-oss:20b"
openrouter = "mistralai/devstral-2512:free"
```

### `delay`

Delay in seconds between AI calls to avoid rate limits. Default: `0.0`.

```toml
[ai]
delay = 0.5  # Wait 0.5 seconds between calls
```

## Benefits

1. **Less repetition**: Set defaults once, use everywhere
2. **Project-specific**: Different projects can use different providers
3. **Flexible**: Override per-command when needed
4. **Environment-friendly**: Works with CI/CD using environment variables

## Troubleshooting

### Config file not loading

- Ensure the file is valid TOML syntax
- Check file permissions (must be readable)
- Verify the path is correct (`~/.pianist/config.toml` or `.pianist/config.toml`)

### Wrong provider/model being used

- Check command-line arguments (highest priority)
- Check environment variables: `echo $AI_PROVIDER`
- Check config files: `cat ~/.pianist/config.toml`
- Remember: command-line args override everything

### TOML parsing errors

If you see errors about TOML parsing, ensure:
- Python 3.11+ (has built-in `tomllib`)
- Or install `tomli` for older Python versions: `pip install tomli`

