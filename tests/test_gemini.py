from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from pianist.ai_providers import GeminiError, generate_text

if TYPE_CHECKING:
    from pathlib import Path


def _create_mock_genai_setup(chunks_with_text: list[str]) -> tuple[MagicMock, MagicMock]:
    """Helper to create a properly structured mock for google.genai.

    Returns:
        Tuple of (mock_google_module, mock_genai_module)
    """
    mock_genai = MagicMock()
    mock_client = MagicMock()
    mock_models = MagicMock()

    # Create mock chunks
    mock_chunks = []
    for text in chunks_with_text:
        mock_chunk = MagicMock()
        mock_chunk.text = text
        mock_chunks.append(mock_chunk)

    # Set up the mock chain: models -> generate_content_stream -> iterator of chunks
    mock_models.generate_content_stream = MagicMock(return_value=iter(mock_chunks))
    mock_client.models = mock_models
    mock_genai.Client = MagicMock(return_value=mock_client)

    # Create mock google module with genai attribute
    mock_google = MagicMock()
    mock_google.genai = mock_genai

    return mock_google, mock_genai


def test_generate_text_requires_api_key(monkeypatch) -> None:
    """Test that generate_text raises an error when neither API key is set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(GeminiError, match="Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set"):
        generate_text(model="gemini-2.5-flash", prompt="test")


def test_generate_text_uses_gemini_api_key(monkeypatch) -> None:
    """Test that GEMINI_API_KEY is preferred when both are set."""
    # Clear any .env loaded keys first
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key-123")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key-456")

    mock_google, mock_genai = _create_mock_genai_setup(["Hello", " World"])

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

    assert result == "Hello World"
    mock_genai.Client.assert_called_once()


def test_generate_text_uses_google_api_key_when_gemini_not_set(monkeypatch) -> None:
    """Test that GOOGLE_API_KEY is used when GEMINI_API_KEY is not set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key-456")

    mock_google, mock_genai = _create_mock_genai_setup(["Response"])

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

    assert result == "Response"
    mock_genai.Client.assert_called_once()


def test_generate_text_streaming_accumulates_chunks(monkeypatch) -> None:
    """Test that streaming properly accumulates text from multiple chunks."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup(["Part ", "1 ", "of ", "response"])

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

    assert result == "Part 1 of response"


def test_generate_text_verbose_output(monkeypatch, capsys) -> None:
    """Test that verbose mode produces progress output."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup(["First chunk", " second chunk"])

    # Mock time to control progress updates
    with patch("pianist.ai_providers.time.time") as mock_time:
        mock_time.side_effect = [0.0, 0.0, 3.0, 5.0]  # start, initial, after 3s, final

        # Patch sys.modules to intercept the import inside the function
        with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
            result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=True)

        assert result == "First chunk second chunk"
        captured = capsys.readouterr()
        assert "Sending request to Gemini" in captured.err
        assert "streaming enabled" in captured.err
        assert "Response complete" in captured.err


def test_generate_text_fallback_to_non_streaming(monkeypatch) -> None:
    """Test that generate_text falls back to non-streaming if streaming fails."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup([])
    mock_client = mock_genai.Client.return_value

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        # Simulate streaming not being available (AttributeError)
        mock_client.models.generate_content_stream.side_effect = AttributeError("No streaming")

        # Mock non-streaming response
        mock_response = MagicMock()
        mock_response.text = "Non-streaming response"
        mock_client.models.generate_content.return_value = mock_response

        result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

        assert result == "Non-streaming response"
        mock_client.models.generate_content.assert_called_once()


def test_generate_text_fallback_to_non_streaming_typeerror(monkeypatch) -> None:
    """Test that generate_text falls back on TypeError as well."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup([])
    mock_client = mock_genai.Client.return_value

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        # Simulate streaming not being available (TypeError)
        mock_client.models.generate_content_stream.side_effect = TypeError("Wrong type")

        # Mock non-streaming response
        mock_response = MagicMock()
        mock_response.text = "Fallback response"
        mock_client.models.generate_content.return_value = mock_response

        result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

        assert result == "Fallback response"


def test_generate_text_empty_response_error(monkeypatch) -> None:
    """Test that empty responses raise an error."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup([])  # Empty chunks
    mock_client = mock_genai.Client.return_value

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        # Empty stream
        mock_client.models.generate_content_stream.return_value = iter([])

        with pytest.raises(GeminiError, match="empty response"):
            generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)


def test_generate_text_empty_text_in_chunks_error(monkeypatch) -> None:
    """Test that chunks with no text raise an error."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup([])
    mock_client = mock_genai.Client.return_value

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        # Chunks with no text attribute or empty text
        mock_chunk1 = MagicMock()
        mock_chunk1.text = None
        mock_chunk2 = MagicMock()
        del mock_chunk2.text  # No text attribute
        mock_stream = iter([mock_chunk1, mock_chunk2])
        mock_client.models.generate_content_stream.return_value = mock_stream

        with pytest.raises(GeminiError, match="empty response"):
            generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)


def test_generate_text_handles_import_error(monkeypatch) -> None:
    """Test that missing google-genai package raises appropriate error."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch.dict("sys.modules", {"google": None, "google.genai": None}):
        with pytest.raises(GeminiError, match="Gemini support is not installed"):
            generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)


def test_generate_text_error_includes_timing_when_verbose(monkeypatch, capsys) -> None:
    """Test that errors include timing information in verbose mode."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup([])
    mock_client = mock_genai.Client.return_value

    # Simulate time passing: start_time (0.0), then error time (5.0)
    # time.time() is called: start_time, then in error handler
    with patch("pianist.ai_providers.time.time") as mock_time:
        mock_time.side_effect = [0.0, 5.0]

        # Simulate an error during streaming (before any chunks are processed)
        mock_client.models.generate_content_stream.side_effect = Exception("Network error")

        # Patch sys.modules to intercept the import inside the function
        with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
            with pytest.raises(GeminiError, match="after 5.0s"):
                generate_text(model="gemini-2.5-flash", prompt="test", verbose=True)


def test_generate_text_verbose_omits_both_keys_message(monkeypatch, capsys) -> None:
    """Test that verbose mode omits message when both keys are set (to reduce noise)."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    mock_google, mock_genai = _create_mock_genai_setup(["Response"])

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        generate_text(model="gemini-2.5-flash", prompt="test", verbose=True)

        captured = capsys.readouterr()
        # Message should NOT appear when verbose is True
        assert "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" not in captured.err
        assert "Using GEMINI_API_KEY" not in captured.err


def test_generate_text_non_verbose_shows_both_keys_message(monkeypatch, capsys) -> None:
    """Test that non-verbose mode shows message when both keys are set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    mock_google, mock_genai = _create_mock_genai_setup(["Response"])

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

        captured = capsys.readouterr()
        # Message should appear when verbose is False
        assert "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" in captured.err
        assert "Using GEMINI_API_KEY" in captured.err


def test_generate_text_verbose_shows_google_key_message(monkeypatch, capsys) -> None:
    """Test that verbose mode shows message when using GOOGLE_API_KEY."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    mock_google, mock_genai = _create_mock_genai_setup(["Response"])

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        generate_text(model="gemini-2.5-flash", prompt="test", verbose=True)

        captured = capsys.readouterr()
        assert "Using GOOGLE_API_KEY" in captured.err
        assert "GEMINI_API_KEY not set" in captured.err


def test_generate_text_chunks_without_text_are_skipped(monkeypatch) -> None:
    """Test that chunks without text are skipped but don't break accumulation."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    mock_google, mock_genai = _create_mock_genai_setup([])
    mock_client = mock_genai.Client.return_value

    # Patch sys.modules to intercept the import inside the function
    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        # Mix of chunks with and without text
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "First"
        mock_chunk2 = MagicMock()
        mock_chunk2.text = None  # No text
        mock_chunk3 = MagicMock()
        mock_chunk3.text = " Second"
        mock_stream = iter([mock_chunk1, mock_chunk2, mock_chunk3])
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

    # Should accumulate only chunks with text
    assert result == "First Second"


def test_generate_text_loads_from_env_file(tmp_path: Path, monkeypatch) -> None:
    """Test that .env file is loaded if python-dotenv is available."""
    # Create a .env file
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=from_env_file\n", encoding="utf-8")

    # Remove from environment to test .env loading
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    mock_google, mock_genai = _create_mock_genai_setup(["Response"])

    # Try to load .env (will only work if python-dotenv is installed)
    try:
        from dotenv import load_dotenv

        # Load the .env file manually for testing
        load_dotenv(env_file, override=False)

        # Verify the key was loaded
        assert os.getenv("GEMINI_API_KEY") == "from_env_file"

        # Patch sys.modules to intercept the import inside the function
        with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
            result = generate_text(model="gemini-2.5-flash", prompt="test", verbose=False)

        assert result == "Response"
    except ImportError:
        # python-dotenv not installed, skip this test
        pytest.skip("python-dotenv not installed")
