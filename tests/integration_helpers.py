"""Helper utilities for optional integration tests with real AI providers.

These helpers allow tests to optionally use real AI providers (Gemini, Ollama, OpenRouter)
if API keys/services are available, while gracefully skipping if not.

Best Practices for Integration Tests:
1. Mark tests with @pytest.mark.integration
2. Use provider-specific skip functions or fixtures
3. Keep integration tests separate from unit tests
4. Run integration tests separately: pytest -m integration
5. Exclude from CI by default: pytest -m "not integration"
6. Use timeouts for network calls
7. Test real-world scenarios, not just happy paths
8. Support multiple providers for better coverage
"""

from __future__ import annotations

import os

import pytest

# ============================================================================
# Provider Detection Functions
# ============================================================================


def has_gemini_api_key() -> bool:
    """Check if a Gemini API key is available.

    Returns:
        True if GEMINI_API_KEY or GOOGLE_API_KEY is set, False otherwise.
    """
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def has_openrouter_api_key() -> bool:
    """Check if an OpenRouter API key is available.

    Returns:
        True if OPENROUTER_API_KEY is set, False otherwise.
    """
    return bool(os.getenv("OPENROUTER_API_KEY"))


def has_ollama_available() -> bool:
    """Check if Ollama is available (checks if service is reachable).

    Returns:
        True if Ollama service appears to be available, False otherwise.
    """
    try:
        import requests
    except ImportError:
        return False

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        # Quick health check
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def has_provider_available(provider: str) -> bool:
    """Check if a specific provider is available.

    Args:
        provider: Provider name ("gemini", "ollama", or "openrouter")

    Returns:
        True if provider is available, False otherwise.
    """
    if provider == "gemini":
        return has_gemini_api_key()
    elif provider == "openrouter":
        return has_openrouter_api_key()
    elif provider == "ollama":
        return has_ollama_available()
    else:
        return False


# ============================================================================
# Skip Functions (Legacy and Provider-Specific)
# ============================================================================


def skip_if_no_api_key() -> None:
    """Skip the test if no Gemini API key is available.

    DEPRECATED: Use skip_if_no_provider() instead for provider-agnostic tests.

    Use this at the start of integration tests that require a real API key.
    This should be used in combination with @pytest.mark.integration.

    Example:
        @pytest.mark.integration
        def test_real_gemini_call():
            skip_if_no_api_key()
            result = generate_text(model="gemini-flash-latest", prompt="Hello")
            assert len(result) > 0
    """
    if not has_gemini_api_key():
        pytest.skip(
            "No Gemini API key available. Set GEMINI_API_KEY or GOOGLE_API_KEY "
            "to run integration tests."
        )


def skip_if_no_provider(provider: str) -> None:
    """Skip the test if the specified provider is not available.

    Args:
        provider: Provider name ("gemini", "ollama", or "openrouter")

    Example:
        @pytest.mark.integration
        def test_with_openrouter():
            skip_if_no_provider("openrouter")
            result = generate_text_unified(
                provider="openrouter",
                model="mistralai/devstral-2512:free",
                prompt="Hello"
            )
            assert len(result) > 0
    """
    if not has_provider_available(provider):
        if provider == "gemini":
            pytest.skip(
                "No Gemini API key available. Set GEMINI_API_KEY or GOOGLE_API_KEY "
                "to run integration tests."
            )
        elif provider == "openrouter":
            pytest.skip(
                "No OpenRouter API key available. Set OPENROUTER_API_KEY to run integration tests."
            )
        elif provider == "ollama":
            pytest.skip(
                "Ollama is not available. Make sure Ollama is installed and running. "
                "See: https://ollama.ai"
            )
        else:
            pytest.skip(f"Provider '{provider}' is not available.")


def skip_if_no_providers(providers: list[str]) -> None:
    """Skip the test if none of the specified providers are available.

    Args:
        providers: List of provider names to check

    Example:
        @pytest.mark.integration
        def test_with_any_provider():
            skip_if_no_providers(["gemini", "openrouter", "ollama"])
            # Test will run if at least one provider is available
    """
    available = any(has_provider_available(p) for p in providers)
    if not available:
        provider_list = ", ".join(providers)
        pytest.skip(
            f"None of the required providers are available: {provider_list}. "
            "Set appropriate API keys or start Ollama to run integration tests."
        )


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def gemini_api_key_available() -> bool:
    """Pytest fixture that checks if Gemini API key is available.

    Use this fixture in tests that need to conditionally run based on API key availability.
    This is useful when you want to test different behavior with/without API keys.

    Example:
        @pytest.mark.integration
        def test_something(gemini_api_key_available):
            if not gemini_api_key_available:
                pytest.skip("No API key")
            # Test code that requires real API...
    """
    return has_gemini_api_key()


@pytest.fixture
def openrouter_api_key_available() -> bool:
    """Pytest fixture that checks if OpenRouter API key is available."""
    return has_openrouter_api_key()


@pytest.fixture
def ollama_available() -> bool:
    """Pytest fixture that checks if Ollama service is available."""
    return has_ollama_available()


@pytest.fixture
def require_api_key() -> None:
    """Fixture that skips the test if no Gemini API key is available.

    DEPRECATED: Use require_provider() instead for provider-agnostic tests.

    Use this fixture when the entire test requires an API key.

    Example:
        @pytest.mark.integration
        def test_real_api_call(require_api_key):
            # Test automatically skipped if no API key
            result = generate_text(model="gemini-flash-latest", prompt="test")
            assert result
    """
    skip_if_no_api_key()


@pytest.fixture
def require_gemini() -> None:
    """Fixture that skips the test if Gemini is not available."""
    skip_if_no_provider("gemini")


@pytest.fixture
def require_openrouter() -> None:
    """Fixture that skips the test if OpenRouter is not available."""
    skip_if_no_provider("openrouter")


@pytest.fixture
def require_ollama() -> None:
    """Fixture that skips the test if Ollama is not available."""
    skip_if_no_provider("ollama")


# ============================================================================
# Legacy Aliases (for backwards compatibility)
# ============================================================================

# Keep these for backwards compatibility
has_api_key = has_gemini_api_key
