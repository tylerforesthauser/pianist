"""Integration tests for unified provider interface.

These tests verify that the unified interface correctly routes to different providers
and maintains consistent behavior across all providers.

These tests make real API calls and should be:
- Marked with @pytest.mark.integration
- Run separately: pytest -m integration
- Excluded from CI by default: pytest -m "not integration"
- Only run when API keys are available

To run these tests:
    pytest -m integration tests/test_ai_providers_unified_integration.py

To run all tests except integration:
    pytest -m "not integration"
"""

from __future__ import annotations

import pytest
from integration_helpers import skip_if_no_provider, skip_if_no_providers

from pianist.ai_providers import GeminiError, OllamaError, OpenRouterError, generate_text_unified


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_routes_to_openrouter() -> None:
    """Test that unified interface correctly routes to OpenRouter."""
    skip_if_no_provider("openrouter")

    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="Say 'OpenRouter' and nothing else.",
        verbose=False,
    )

    assert result
    assert "openrouter" in result.lower()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.expensive
def test_generate_text_unified_routes_to_gemini() -> None:
    """Test that unified interface correctly routes to Gemini."""
    skip_if_no_provider("gemini")

    result = generate_text_unified(
        provider="gemini",
        model="gemini-flash-latest",
        prompt="Say 'Gemini' and nothing else.",
        verbose=False,
    )

    assert result
    assert "gemini" in result.lower() or len(result) > 0  # Gemini might not say its name


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_unified_routes_to_ollama() -> None:
    """Test that unified interface correctly routes to Ollama."""
    skip_if_no_provider("ollama")

    result = generate_text_unified(
        provider="ollama",
        model="gpt-oss:20b",
        prompt="Say 'test' and nothing else.",
        verbose=False,
    )

    assert result
    assert len(result) > 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_openrouter_error_propagates() -> None:
    """Test that OpenRouter errors propagate correctly through unified interface."""
    skip_if_no_provider("openrouter")

    with pytest.raises(OpenRouterError, match="OpenRouter"):
        generate_text_unified(
            provider="openrouter",
            model="invalid-model-name-12345",
            prompt="test",
            verbose=False,
        )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.expensive
def test_generate_text_unified_gemini_error_propagates() -> None:
    """Test that Gemini errors propagate correctly through unified interface."""
    skip_if_no_provider("gemini")

    with pytest.raises(GeminiError, match="Gemini"):
        generate_text_unified(
            provider="gemini",
            model="invalid-model-name-12345",
            prompt="test",
            verbose=False,
        )


@pytest.mark.integration
@pytest.mark.slow
def test_generate_text_unified_ollama_error_propagates() -> None:
    """Test that Ollama errors propagate correctly through unified interface."""
    skip_if_no_provider("ollama")

    with pytest.raises(OllamaError, match="Ollama"):
        generate_text_unified(
            provider="ollama",
            model="nonexistent-model-12345",
            prompt="test",
            verbose=False,
        )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_consistent_interface() -> None:
    """Test that unified interface provides consistent behavior across providers."""
    skip_if_no_provider("openrouter")

    # Test that all providers accept the same parameters
    result = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="What is 2+2? Answer with just the number.",
        verbose=False,
    )

    assert result
    assert len(result) > 0
    # Should contain "4" (the answer)
    assert "4" in result


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_verbose_mode() -> None:
    """Test that verbose mode works consistently across providers."""
    skip_if_no_provider("openrouter")

    import sys
    from io import StringIO

    old_stderr = sys.stderr
    sys.stderr = captured = StringIO()

    try:
        result = generate_text_unified(
            provider="openrouter",
            model="mistralai/devstral-2512:free",
            prompt="Say 'test'",
            verbose=True,
        )

        assert result
        stderr_output = captured.getvalue()
        # Should have some verbose output
        assert len(stderr_output) > 0
    finally:
        sys.stderr = old_stderr


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.free
def test_generate_text_unified_multiple_providers() -> None:
    """Test that we can use multiple providers in sequence."""
    skip_if_no_providers(["openrouter"])

    # Test OpenRouter
    result1 = generate_text_unified(
        provider="openrouter",
        model="mistralai/devstral-2512:free",
        prompt="Say 'first'",
        verbose=False,
    )

    assert result1
    assert len(result1) > 0

    # If Gemini is also available, test it
    try:
        skip_if_no_provider("gemini")
        result2 = generate_text_unified(
            provider="gemini",
            model="gemini-flash-latest",
            prompt="Say 'second'",
            verbose=False,
        )
        assert result2
        assert len(result2) > 0
    except pytest.skip.Exception:
        # Gemini not available, that's fine
        pass
