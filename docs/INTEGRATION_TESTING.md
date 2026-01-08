# Integration Testing Best Practices

## Overview

Integration tests make real API calls to external services (like Gemini) to verify that the entire system works end-to-end. They complement unit tests, which use mocks to test individual components in isolation.

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
def test_real_api_call():
    """Test that makes real API calls."""
    skip_if_no_api_key()
    # Test code...
```

### 2. Make Tests Optional

Integration tests should gracefully skip when:
- No API key is available
- Network is unavailable
- Running in CI without integration test configuration

```python
from tests.integration_helpers import skip_if_no_api_key

@pytest.mark.integration
def test_something():
    skip_if_no_api_key()  # Skips if no API key
    # Test code...
```

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
@pytest.fixture
def require_api_key():
    """Fixture that skips test if no API key."""
    skip_if_no_api_key()

@pytest.mark.integration
def test_something(require_api_key):
    # Test automatically skipped if no API key
    result = generate_text(...)
    assert result
```

## Running Integration Tests

### Run Only Integration Tests

```bash
pytest -m integration
```

### Run All Tests Except Integration

```bash
# Sequential execution
pytest -m "not integration"

# Parallel execution (faster, recommended)
pytest -m "not integration" -n auto
```

**Performance Note:** The test suite uses `pytest-xdist` for parallel execution. Use `-n auto` to automatically use all CPU cores, which can significantly reduce test runtime. Module-scoped fixtures cache expensive operations like music21 stream conversions.

### Run Specific Integration Test File

```bash
pytest tests/test_gemini_integration.py
```

### Run with Verbose Output

```bash
pytest -m integration -v
```

### Run Only Failed Tests

During development, rerun only failed tests for faster iteration:

```bash
pytest -m "not integration" --lf
```

## CI/CD Configuration

### Option 1: Skip Integration Tests by Default

Most CI systems should skip integration tests by default:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest -m "not integration"
```

### Option 2: Run Integration Tests Conditionally

Run integration tests only when API keys are available:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest -m "not integration"

- name: Run integration tests
  if: env.GEMINI_API_KEY != ''
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: pytest -m integration
```

### Option 3: Separate Integration Test Job

Create a separate job for integration tests:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest -m "not integration"
  
  integration:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: pytest -m integration
```

## Example Integration Test

```python
"""Integration tests for Gemini API."""
from __future__ import annotations

import pytest
from tests.integration_helpers import skip_if_no_api_key
from pianist.ai_providers import generate_text

@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api():
    """Test real API call to Gemini."""
    skip_if_no_api_key()
    
    result = generate_text(
        model="gemini-flash-latest",
        prompt="Say 'Hello, World!'",
        verbose=False
    )
    
    assert result
    assert "hello" in result.lower() or "world" in result.lower()
```

## Summary

- ✅ Use integration tests to verify real API compatibility
- ✅ Mark with `@pytest.mark.integration` and `@pytest.mark.slow`
- ✅ Make tests optional with `skip_if_no_api_key()`
- ✅ Keep separate from unit tests
- ✅ Run separately: `pytest -m integration`
- ✅ Exclude from CI by default: `pytest -m "not integration"`
- ✅ Use timeouts and handle rate limits
- ✅ Test real-world scenarios, not just happy paths

