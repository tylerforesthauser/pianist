"""Pytest configuration for pianist tests.

This ensures the src directory is in the Python path so tests can import the pianist package.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path
# This is needed because Python 3.14+ may not process .pth files correctly in some cases
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import after path is set up
from pianist.musical_analysis import MUSIC21_AVAILABLE, _composition_to_music21_stream
from pianist.schema import Composition, NoteEvent, Track


@pytest.fixture(scope="module")
def simple_composition() -> Composition:
    """A simple test composition that can be reused across tests.

    Module-scoped to avoid recreating for every test, since Composition objects are immutable.
    """
    return Composition(
        title="Test",
        bpm=120,
        key_signature="C",
        tracks=[
            Track(
                events=[
                    NoteEvent(start=0, duration=1, pitches=[60, 64, 67], velocity=80),  # C major
                    NoteEvent(start=1, duration=1, pitches=[62, 65, 69], velocity=80),  # D minor
                    NoteEvent(start=2, duration=1, pitches=[64, 67, 71], velocity=80),  # E minor
                    NoteEvent(start=3, duration=1, pitches=[65, 69, 72], velocity=80),  # F major
                ]
            )
        ],
    )


@pytest.fixture(scope="module")
def simple_composition_stream(simple_composition: Composition):
    """Pre-converted music21 stream for simple_composition (cached to avoid re-conversion).

    Module-scoped to cache the expensive music21 conversion across tests in the same module.
    """
    if not MUSIC21_AVAILABLE:
        pytest.skip("music21 not installed")
    try:
        return _composition_to_music21_stream(simple_composition)
    except Exception as e:
        pytest.skip(f"Failed to convert composition to music21 stream: {e}")


@pytest.fixture(scope="module")
def motif_test_composition() -> Composition:
    """A composition designed for motif detection tests.

    Module-scoped to avoid recreating for every test, since Composition objects are immutable.
    """
    return Composition(
        title="Test",
        bpm=120,
        tracks=[
            Track(
                events=[
                    # Repeating pattern: C-E-G
                    NoteEvent(start=0, duration=0.5, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=0.5, duration=0.5, pitches=[62, 65, 69], velocity=80),
                    NoteEvent(start=1, duration=0.5, pitches=[64, 67, 71], velocity=80),
                    # Repeat the pattern
                    NoteEvent(start=4, duration=0.5, pitches=[60, 64, 67], velocity=80),
                    NoteEvent(start=4.5, duration=0.5, pitches=[62, 65, 69], velocity=80),
                    NoteEvent(start=5, duration=0.5, pitches=[64, 67, 71], velocity=80),
                ]
            )
        ],
    )


@pytest.fixture(scope="module")
def motif_test_composition_stream(motif_test_composition: Composition):
    """Pre-converted music21 stream for motif_test_composition.

    Module-scoped to cache the expensive music21 conversion across tests in the same module.
    """
    if not MUSIC21_AVAILABLE:
        pytest.skip("music21 not installed")
    try:
        return _composition_to_music21_stream(motif_test_composition)
    except Exception as e:
        pytest.skip(f"Failed to convert composition to music21 stream: {e}")


def valid_composition_json() -> str:
    """Return minimal valid Pianist composition JSON string.

    This is a shared helper function used across multiple test files.
    Returns a JSON string representing a minimal valid composition.
    """
    return (
        "{"
        '"title":"Test",'
        '"bpm":120,'
        '"time_signature":{"numerator":4,"denominator":4},'
        '"ppq":480,'
        '"tracks":[{"name":"Piano","channel":0,"program":0,"events":['
        '{"type":"note","start":0,"duration":1,"pitches":[60],"velocity":80}'
        "]}]"
        "}"
    )


# ============================================================================
# Environment Variable Fixtures
# ============================================================================


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Fixture that sets up mock API keys for UNIT TESTS ONLY.

    ⚠️ DO NOT USE IN INTEGRATION TESTS ⚠️

    Integration tests must use REAL API keys and make REAL API calls.
    Use `skip_if_no_provider()` from integration_helpers for integration tests.

    This fixture is ONLY for unit tests that:
    - Test environment variable reading logic
    - Test key preference/fallback logic
    - Mock the actual API client (not make real calls)

    Example (UNIT TEST):
        def test_key_preference(mock_api_keys):
            # Mock API client too - this is a unit test
            with patch(...):
                # Test code that mocks API calls...

    Example (INTEGRATION TEST - CORRECT):
        @pytest.mark.integration
        def test_real_api():
            skip_if_no_provider("openrouter")  # Uses REAL key
            result = generate_text_unified(...)  # REAL API call
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    # Note: monkeypatch automatically cleans up after test


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture that clears all API key environment variables.

    Use this fixture when you need to test behavior when no API keys
    are set, or to ensure a clean environment for a test.

    Example:
        def test_no_api_key(clean_env):
            # All API keys are cleared
            # Test code that should handle missing keys...
    """
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    # Note: monkeypatch automatically restores original values after test
