"""Integration tests for Gemini API functionality.

These tests make real API calls to Gemini and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API key is available

To run these tests:
    pytest -m integration tests/test_gemini_integration.py

To run all tests except integration:
    pytest -m "not integration"
"""

from __future__ import annotations

import pytest
from integration_helpers import skip_if_no_api_key

from pianist.ai_providers import GeminiError, generate_text


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api_call() -> None:
    """Test that generate_text works with real Gemini API."""
    skip_if_no_api_key()

    # Simple test that should work reliably
    result = generate_text(
        model="gemini-flash-latest", prompt="Say 'Hello, World!' and nothing else.", verbose=False
    )

    # Verify we got a response
    assert result
    assert len(result) > 0
    # Should contain "Hello" or "World" (case-insensitive)
    assert "hello" in result.lower() or "world" in result.lower()


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api_verbose() -> None:
    """Test verbose mode with real API call."""
    skip_if_no_api_key()

    import sys
    from io import StringIO

    # Capture stderr to verify verbose output
    old_stderr = sys.stderr
    sys.stderr = captured = StringIO()

    try:
        result = generate_text(
            model="gemini-flash-latest", prompt="Say 'test' and nothing else.", verbose=True
        )

        # Verify response
        assert result
        assert len(result) > 0

        # Verify verbose output was produced
        stderr_output = captured.getvalue()
        assert "Sending request to Gemini" in stderr_output
        assert "streaming enabled" in stderr_output or "Response complete" in stderr_output
    finally:
        sys.stderr = old_stderr


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api_streaming() -> None:
    """Test that streaming works with real API."""
    skip_if_no_api_key()

    # Use a prompt that will generate multiple chunks
    result = generate_text(
        model="gemini-flash-latest", prompt="Count from 1 to 5, one number per line.", verbose=False
    )

    # Verify we got a response with multiple lines
    assert result
    lines = result.strip().split("\n")
    # Should have at least a few lines
    assert len(lines) >= 2


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api_error_handling() -> None:
    """Test error handling with real API (invalid model)."""
    skip_if_no_api_key()

    # Try with an invalid model name
    with pytest.raises(GeminiError, match="Gemini request failed"):
        generate_text(model="invalid-model-name-12345", prompt="test", verbose=False)


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api_empty_prompt() -> None:
    """Test that empty prompts are handled correctly by the API."""
    skip_if_no_api_key()

    # Empty prompt might return an error or empty response
    # The API behavior may vary, so we just check it doesn't crash
    try:
        generate_text(model="gemini-flash-latest", prompt="", verbose=False)
        # If it succeeds, result might be empty or have content
        # Both are acceptable behaviors
    except GeminiError:
        # API rejecting empty prompt is also acceptable
        pass


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_real_api_long_prompt() -> None:
    """Test that longer prompts work correctly."""
    skip_if_no_api_key()

    # Create a longer prompt
    long_prompt = " ".join(["word"] * 100) + " What is the sum of 2+2?"

    result = generate_text(model="gemini-flash-latest", prompt=long_prompt, verbose=False)

    # Should get a response
    assert result
    assert len(result) > 0
