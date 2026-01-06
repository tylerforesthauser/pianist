# API Key Management Best Practices

This document describes best practices for managing Gemini/Google API keys when using pianist.

## Overview

Pianist supports multiple methods for providing API keys, in order of precedence:
1. Environment variables (highest priority)
2. `.env` file (if python-dotenv is installed)
3. Error if neither is available

## Methods

### Method 1: `.env` File (Recommended for Local Development)

The `.env` file is the most convenient method for local development as it keeps your API key in one place and doesn't require exporting it in every terminal session.

**Setup:**
```bash
# 1. Install python-dotenv (optional but recommended)
python3 -m pip install python-dotenv

# 2. Copy the example file
cp .env.example .env

# 3. Edit .env and add your API key
# Uncomment and set one of:
GEMINI_API_KEY=your_key_here
# or
GOOGLE_API_KEY=your_key_here
```

**Benefits:**
- ✅ Key stored in one place
- ✅ Automatically loaded when pianist runs
- ✅ `.env` is gitignored (won't be committed)
- ✅ Easy to switch between projects

**Note:** The `.env` file is automatically loaded from:
- Current working directory
- Parent directories (up to 3 levels)
- Project root (where `pyproject.toml` is located)

### Method 2: Environment Variables (Recommended for CI/CD)

Environment variables are the standard method for CI/CD pipelines and production deployments.

**Setup:**
```bash
# In your shell:
export GEMINI_API_KEY="your_key_here"
# or
export GOOGLE_API_KEY="your_key_here"

# To make it persistent, add to your shell config:
# ~/.bashrc, ~/.zshrc, etc.
echo 'export GEMINI_API_KEY="your_key_here"' >> ~/.zshrc
```

**Benefits:**
- ✅ Standard method for CI/CD
- ✅ Works without additional dependencies
- ✅ Can be set per-session or globally
- ✅ Overrides `.env` file values

### Method 3: Both (Flexible)

You can use both methods together:
- `.env` file for default/local development
- Environment variables for CI/CD or to override defaults

**Priority:** Environment variables always override `.env` file values.

## Key Selection

If both `GEMINI_API_KEY` and `GOOGLE_API_KEY` are set:
- `GEMINI_API_KEY` takes precedence
- A message is shown in verbose mode indicating which key is being used

## Security Best Practices

1. **Never commit API keys to version control**
   - `.env` is already in `.gitignore`
   - Never add API keys to code or commit them

2. **Use different keys for different environments**
   - Development key for local work
   - Production key for CI/CD (stored as secrets)

3. **Rotate keys regularly**
   - Update keys if they're exposed
   - Use key restrictions in Google Cloud Console

4. **Use least privilege**
   - Create API keys with minimal required permissions
   - Use separate keys for different projects if needed

## Integration Testing

For integration tests that optionally use the real API:

```python
from tests.integration_helpers import skip_if_no_api_key, has_api_key

def test_real_gemini_integration():
    skip_if_no_api_key()  # Skips if no key available
    # Your integration test code here...
```

Or use the fixture:
```python
def test_real_gemini_integration(gemini_api_key_available):
    if not gemini_api_key_available:
        pytest.skip("No API key")
    # Your integration test code here...
```

## Troubleshooting

### Key not found
- Check that the key is set: `echo $GEMINI_API_KEY`
- Verify `.env` file exists and has the key (if using dotenv)
- Check that python-dotenv is installed if using `.env` files

### Wrong key being used
- Check which keys are set: `env | grep -i gemini`
- Remember: `GEMINI_API_KEY` takes precedence over `GOOGLE_API_KEY`
- Environment variables override `.env` file values

### .env file not loading
- Ensure python-dotenv is installed: `pip install python-dotenv`
- Check that `.env` file is in the correct location
- Verify file format (no spaces around `=`, one key per line)

## Examples

### Local Development Setup
```bash
# Install dotenv support
pip install python-dotenv

# Create .env file
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key

# Now pianist will automatically use the key
./pianist analyze -i song.mid --gemini --instructions "..." -o out.json
```

### CI/CD Setup (GitHub Actions example)
```yaml
- name: Run tests
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: pytest
```

### Temporary Override
```bash
# Override .env file for this session
export GEMINI_API_KEY="different_key"
./pianist iterate -i seed.json --gemini --instructions "..." -o out.json
```

