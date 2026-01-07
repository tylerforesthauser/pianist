"""Helper utilities for optional integration tests with real Gemini API.

These helpers allow tests to optionally use the real Gemini API if an API key
is available, while gracefully skipping if not.

Best Practices for Integration Tests:
1. Mark tests with @pytest.mark.integration
2. Use skip_if_no_api_key() or the gemini_api_key_available fixture
3. Keep integration tests separate from unit tests
4. Run integration tests separately: pytest -m integration
5. Exclude from CI by default: pytest -m "not integration"
6. Use timeouts for network calls
7. Test real-world scenarios, not just happy paths
"""
from __future__ import annotations

import os
import pytest

from pianist.ai_providers import GeminiError, generate_text


def skip_if_no_api_key() -> None:
    """Skip the test if no Gemini API key is available.
    
    Use this at the start of integration tests that require a real API key.
    This should be used in combination with @pytest.mark.integration.
    
    Example:
        @pytest.mark.integration
        def test_real_gemini_call():
            skip_if_no_api_key()
            result = generate_text(model="gemini-flash-latest", prompt="Hello")
            assert len(result) > 0
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip(
            "No Gemini API key available. Set GEMINI_API_KEY or GOOGLE_API_KEY "
            "to run integration tests."
        )


def has_api_key() -> bool:
    """Check if a Gemini API key is available.
    
    Returns:
        True if GEMINI_API_KEY or GOOGLE_API_KEY is set, False otherwise.
    """
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


@pytest.fixture
def gemini_api_key_available() -> bool:
    """Pytest fixture that checks if API key is available.
    
    Use this fixture in tests that need to conditionally run based on API key availability.
    This is useful when you want to test different behavior with/without API keys.
    
    Example:
        @pytest.mark.integration
        def test_something(gemini_api_key_available):
            if not gemini_api_key_available:
                pytest.skip("No API key")
            # Test code that requires real API...
    """
    return has_api_key()


@pytest.fixture
def require_api_key() -> None:
    """Fixture that skips the test if no API key is available.
    
    Use this fixture when the entire test requires an API key.
    
    Example:
        @pytest.mark.integration
        def test_real_api_call(require_api_key):
            # Test automatically skipped if no API key
            result = generate_text(model="gemini-flash-latest", prompt="test")
            assert result
    """
    skip_if_no_api_key()

