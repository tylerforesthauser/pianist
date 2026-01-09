"""Integration tests for OpenRouter API functionality.

These tests make real API calls to OpenRouter and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API key is available

To run these tests:
    pytest -m integration tests/test_ai_providers_openrouter_integration.py

To run all tests except integration:
    pytest -m "not integration"
"""

from __future__ import annotations

import pytest
from integration_helpers import skip_if_no_provider

from pianist.ai_providers import OpenRouterError, generate_text_unified


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_openrouter_basic() -> None:
    """Test that generate_text_unified works with real OpenRouter API."""
    skip_if_no_provider("openrouter")

    # Simple test that should work reliably with free model
    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="Say 'Hello, World!' and nothing else.",
        verbose=False,
    )

    # Verify we got a response
    assert result
    assert len(result) > 0
    # Should contain "Hello" or "World" (case-insensitive)
    assert "hello" in result.lower() or "world" in result.lower()


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_unified_openrouter_verbose() -> None:
    """Test verbose mode with real OpenRouter API call."""
    skip_if_no_provider("openrouter")

    import sys
    from io import StringIO

    # Capture stderr to verify verbose output
    old_stderr = sys.stderr
    sys.stderr = captured = StringIO()

    try:
        result = generate_text_unified(
            provider="openrouter",
            model="mistralai/devstral-2512:free",
            prompt="Say 'test' and nothing else.",
            verbose=True,
        )

        # Verify response
        assert result
        assert len(result) > 0

        # Verify verbose output was produced
        stderr_output = captured.getvalue()
        assert (
            "Sending request to OpenRouter" in stderr_output or "Response complete" in stderr_output
        )
    finally:
        sys.stderr = old_stderr


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_openrouter_free_model() -> None:
    """Test that free OpenRouter models work correctly."""
    skip_if_no_provider("openrouter")

    # Test with a free model (devstral is recommended free model)
    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="What is 2+2? Answer with just the number.",
        verbose=False,
    )

    # Verify we got a response
    assert result
    assert len(result) > 0
    # Should contain "4" (the answer)
    assert "4" in result


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_openrouter_error_handling() -> None:
    """Test error handling with real OpenRouter API (invalid model)."""
    skip_if_no_provider("openrouter")

    # Try with an invalid model name
    with pytest.raises(OpenRouterError, match="OpenRouter"):
        generate_text_unified(
            provider="openrouter",
            model="invalid-model-name-12345",
            prompt="test",
            verbose=False,
        )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_openrouter_long_prompt() -> None:
    """Test that longer prompts work correctly with OpenRouter."""
    skip_if_no_provider("openrouter")

    # Create a longer prompt
    long_prompt = " ".join(["word"] * 100) + " What is the sum of 2+2?"

    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt=long_prompt,
        verbose=False,
    )

    # Should get a response
    assert result
    assert len(result) > 0
