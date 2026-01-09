# Integration Testing Best Practices

## Overview

Integration tests make real API calls to external services (like Gemini, OpenRouter, Ollama) to verify that the entire system works end-to-end. They complement unit tests, which use mocks to test individual components in isolation.

**Current Coverage:**
- **35 integration tests** across provider APIs and CLI commands
- **24 free-tier tests** (safe for frequent CI runs)
- **11 expensive tests** (may hit rate limits, use sparingly)

## When to Use Integration Tests

### ✅ Good Use Cases

1. **Verify API compatibility**: Ensure the code works with the actual API, not just mocks
2. **Test real-world scenarios**: Verify behavior with actual network conditions
3. **Catch API changes**: Detect when external APIs change behavior
4. **Validate end-to-end flows**: Test complete workflows from input to output
5. **Performance testing**: Measure actual response times and throughput

### ❌ Avoid Integration Tests For

1. **Fast feedback loops**: Unit tests are faster for development
2. **CI/CD pipelines**: Unless specifically configured, they add time and dependencies
3. **Testing error handling**: Mocks are better for testing specific error conditions
4. **Testing edge cases**: Unit tests with mocks are more reliable and faster

## Best Practices

### 1. Mark Tests Appropriately

Use pytest markers to categorize tests:

```python
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free  # For free-tier APIs (OpenRouter free models)
def test_real_api_call():
    """Test that makes real API calls."""
    skip_if_no_provider("openrouter")
    # Test code...

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.expensive  # For APIs with rate limits (Gemini free tier)
def test_gemini_api_call():
    """Test that may hit rate limits."""
    skip_if_no_provider("gemini")
    # Test code...
```

**Available Markers:**
- `@pytest.mark.integration` - Marks integration tests (required)
- `@pytest.mark.slow` - Marks slow tests
- `@pytest.mark.free` - Marks free-tier tests (safe for CI)
- `@pytest.mark.expensive` - Marks tests that may hit rate limits or incur costs

### 2. Make Tests Optional

Integration tests should gracefully skip when:
- No API key is available
- Network is unavailable
- Running in CI without integration test configuration

**Setting Up API Keys:**

Integration tests require real API keys. Set them via:
- **Environment variables** (recommended): `export OPENROUTER_API_KEY='your-key'`
- **`.env` file**: Create `.env` in project root (automatically loaded if `python-dotenv` installed)
- **CI/CD secrets**: Use GitHub Secrets or your CI platform's secret management

**Required Environment Variables:**
- `OPENROUTER_API_KEY` - For OpenRouter tests (free tier available)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - For Gemini tests
- `OLLAMA_URL` - Optional, defaults to `http://localhost:11434` for Ollama tests

**Check API Keys Before Running:**

```bash
# Check which providers are available
./scripts/check_test_keys.sh
```

**In Test Code:**

```python
from integration_helpers import skip_if_no_provider, skip_if_no_providers

@pytest.mark.integration
@pytest.mark.free
def test_with_openrouter():
    skip_if_no_provider("openrouter")  # Skips if OpenRouter not available
    # Test code...

@pytest.mark.integration
def test_with_any_provider():
    skip_if_no_providers(["gemini", "openrouter", "ollama"])  # Skips if none available
    # Test code...
```

**Available Helper Functions:**
- `skip_if_no_provider(provider)` - Skip if specific provider unavailable
- `skip_if_no_providers([...])` - Skip if none of the providers available
- `has_provider_available(provider)` - Check if provider is available
- Fixtures: `require_gemini`, `require_openrouter`, `require_ollama`

### 3. Keep Tests Separate

- Store in separate files: `test_*_integration.py`
- Use markers to run separately: `pytest -m integration`
- Exclude from default runs: `pytest -m "not integration"`

### 4. Use Timeouts

Network calls can hang. Always use timeouts:

```python
import signal

@pytest.mark.integration
def test_with_timeout():
    skip_if_no_api_key()

    def timeout_handler(signum, frame):
        raise TimeoutError("Test timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout

    try:
        result = generate_text(...)
        assert result
    finally:
        signal.alarm(0)  # Cancel timeout
```

### 5. Test Real-World Scenarios

Focus on scenarios users will actually encounter:

```python
@pytest.mark.integration
def test_real_user_workflow():
    """Test a complete user workflow."""
    skip_if_no_api_key()

    # 1. Analyze a MIDI file
    analysis = analyze_midi("test.mid")

    # 2. Send to Gemini
    result = generate_text(
        model="gemini-flash-latest",
        prompt=create_prompt(analysis, "Make it faster"),
        verbose=True
    )

    # 3. Parse response
    composition = parse_composition_from_text(result)

    # 4. Render to MIDI
    render_midi(composition, "output.mid")

    # Verify output
    assert Path("output.mid").exists()
```

### 6. Handle Rate Limits

External APIs have rate limits. Design tests to be resilient:

```python
import time

@pytest.mark.integration
def test_with_rate_limiting():
    skip_if_no_api_key()

    # Make multiple calls with delays
    for i in range(3):
        result = generate_text(...)
        assert result
        if i < 2:  # Don't delay after last call
            time.sleep(1)  # Rate limit protection
```

### 7. Use Fixtures for Setup

Create fixtures for common integration test setup:

```python
from tests.integration_helpers import require_gemini, require_openrouter

@pytest.mark.integration
def test_with_gemini(require_gemini):
    # Test automatically skipped if Gemini not available
    result = generate_text_unified(
        provider="gemini",
        model="gemini-flash-latest",
        prompt="test"
    )
    assert result

@pytest.mark.integration
def test_with_openrouter(require_openrouter):
    # Test automatically skipped if OpenRouter not available
    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="test"
    )
    assert result
```

## Running Integration Tests

### Check API Keys First

Before running integration tests, check which providers are available:

```bash
./scripts/check_test_keys.sh
```

This script checks for:
- Gemini API keys (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)
- OpenRouter API key (`OPENROUTER_API_KEY`)
- Ollama service availability (`OLLAMA_URL` or default localhost)

### Run Only Integration Tests

```bash
# All integration tests
pytest -m integration

# Only free-tier tests (recommended for CI)
pytest -m "integration and free"

# Exclude expensive tests (avoid rate limits)
pytest -m "integration and not expensive"

# Only expensive tests (use sparingly)
pytest -m "integration and expensive"
```

### Run All Tests Except Integration

```bash
# Parallel execution (faster, recommended)
pytest -m "not integration" -n auto

# Sequential execution (slower)
pytest -m "not integration"
```

**Performance Note:** The test suite uses `pytest-xdist` for parallel execution. Use `-n auto` to automatically use all CPU cores, which can significantly reduce test runtime. Module-scoped fixtures cache expensive operations like music21 stream conversions.

### Run Specific Integration Test Files

```bash
# Provider-specific tests
pytest tests/test_ai_providers_openrouter_integration.py
pytest tests/test_ai_providers_gemini_integration.py
pytest tests/test_ai_providers_unified_integration.py

# CLI command tests
pytest tests/test_cli_generate_integration.py
pytest tests/test_cli_modify_integration.py
pytest tests/test_cli_expand_integration.py
pytest tests/test_cli_analyze_integration.py
```

### Run with Verbose Output

```bash
pytest -m integration -v
```

### Run Only Failed Tests

During development, rerun only failed tests for faster iteration:

```bash
pytest -m "not integration" --lf
pytest -m integration --lf  # For integration tests
```

## CI/CD Configuration

### Option 1: Skip Integration Tests by Default

Most CI systems should skip integration tests by default:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest -m "not integration"
```

### Option 2: Run Integration Tests Conditionally (Recommended)

Run free-tier integration tests in CI, expensive tests only on main branch:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest -m "not integration" -n auto

- name: Run free integration tests
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: pytest -m "integration and free" -n auto

- name: Run expensive integration tests
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: pytest -m "integration and expensive" -n auto
```

### Option 3: Separate Integration Test Job

Create separate jobs for different test categories:

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest -m "not integration" -n auto

  integration-free:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run free integration tests
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: pytest -m "integration and free" -n auto

  integration-expensive:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run expensive integration tests
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: pytest -m "integration and expensive" -n auto
```

## Example Integration Tests

### Provider-Specific Test

```python
"""Integration tests for OpenRouter API."""
from __future__ import annotations

import pytest
from integration_helpers import skip_if_no_provider
from pianist.ai_providers import generate_text_unified

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free  # Free-tier test, safe for CI
def test_generate_text_unified_openrouter_basic():
    """Test real API call to OpenRouter."""
    skip_if_no_provider("openrouter")

    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="Say 'Hello, World!'",
        verbose=False
    )

    assert result
    assert "hello" in result.lower() or "world" in result.lower()
```

### CLI Command Test

```python
"""Integration tests for generate command."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from integration_helpers import skip_if_no_provider
from pianist.cli import main

if TYPE_CHECKING:
    from pathlib import Path

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free  # Free-tier test, safe for CI
def test_cli_generate_with_openrouter_creates_composition(tmp_path: Path):
    """Test that generate command creates valid composition."""
    skip_if_no_provider("openrouter")

    output_file = tmp_path / "composition.json"

    rc = main([
        "generate",
        "Title: Test Piece\nForm: binary\nLength: 16 beats",
        "--provider", "openrouter",
        "--model", "mistralai/devstral-2512:free",
        "-o", str(output_file),
    ])

    assert rc == 0
    assert output_file.exists()

    # Verify output is valid
    import json
    data = json.loads(output_file.read_text())
    assert "title" in data
    assert "tracks" in data
```

## Integration Test Files

### Provider Tests
- `test_ai_providers_openrouter_integration.py` - OpenRouter API tests (5 tests, all free-tier)
- `test_ai_providers_gemini_integration.py` - Gemini API tests (6 tests, all expensive)
- `test_ai_providers_unified_integration.py` - Unified interface tests (9 tests, mix of free/expensive)

### CLI Command Tests
- `test_cli_generate_integration.py` - Generate command tests (5 tests, all free-tier)
- `test_cli_modify_integration.py` - Modify command tests (4 tests, all free-tier)
- `test_cli_expand_integration.py` - Expand command tests (3 tests, all free-tier)
- `test_cli_analyze_integration.py` - Analyze command tests (3 tests, all free-tier)

**Total: 35 integration tests**
- 24 free-tier tests (safe for frequent CI runs)
- 11 expensive tests (may hit rate limits, use sparingly)

## Helper Script

### Check API Keys

Before running integration tests, use the helper script to check which providers are available:

```bash
./scripts/check_test_keys.sh
```

This script:
- Checks for Gemini API keys (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)
- Checks for OpenRouter API key (`OPENROUTER_API_KEY`)
- Checks if Ollama is running (tests `OLLAMA_URL` or default localhost)
- Provides clear status messages and setup instructions

**Example Output:**
```
Checking API keys for integration tests...

✅ OpenRouter: OPENROUTER_API_KEY set
❌ Gemini: GEMINI_API_KEY or GOOGLE_API_KEY not set
⚠️  Ollama: OLLAMA_URL not set (defaults to http://localhost:11434)
   ✅ Ollama appears to be running at http://localhost:11434

Summary:
--------
✅ 2 providers available. Integration tests should run.
```

## Summary

- ✅ Use integration tests to verify real API compatibility
- ✅ Mark with `@pytest.mark.integration` and `@pytest.mark.slow`
- ✅ Use `@pytest.mark.free` for free-tier tests (CI-safe)
- ✅ Use `@pytest.mark.expensive` for rate-limited tests
- ✅ Make tests optional with `skip_if_no_provider()`
- ✅ Keep separate from unit tests
- ✅ Run separately: `pytest -m integration`
- ✅ Use `pytest -m "integration and free"` for CI
- ✅ Exclude from CI by default: `pytest -m "not integration"`
- ✅ Check API keys first: `./scripts/check_test_keys.sh`
- ✅ Use timeouts and handle rate limits
- ✅ Test real-world scenarios, not just happy paths
