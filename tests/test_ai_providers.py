"""Tests for AI provider functionality including Ollama and unified interface.

This test file covers:
- Ollama provider (generate_text_ollama)
- Unified interface (generate_text_unified)
- Provider routing and error handling
- Verification that Gemini-specific messages don't appear when using Ollama
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from pianist.ai_providers import (
    GeminiError,
    OllamaError,
    generate_text_ollama,
    generate_text_unified,
)


def _create_mock_requests():
    """Helper to create a mock requests module with exceptions."""
    mock_requests = MagicMock()
    
    # Create exception classes
    class ConnectionError(Exception):
        pass
    
    class Timeout(Exception):
        pass
    
    mock_requests.exceptions = MagicMock()
    mock_requests.exceptions.ConnectionError = ConnectionError
    mock_requests.exceptions.Timeout = Timeout
    
    return mock_requests


def test_generate_text_ollama_requires_requests(monkeypatch) -> None:
    """Test that generate_text_ollama raises error when requests is not available."""
    monkeypatch.setattr("pianist.ai_providers.requests", None, raising=False)
    
    with patch.dict("sys.modules", {"requests": None}):
        with pytest.raises(OllamaError, match="requests library required"):
            generate_text_ollama(model="test-model", prompt="test", verbose=False)


def test_generate_text_ollama_connection_error(monkeypatch) -> None:
    """Test that connection errors are properly handled."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_requests = _create_mock_requests()
    mock_requests.post.side_effect = mock_requests.exceptions.ConnectionError("Connection refused")
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        with pytest.raises(OllamaError, match="Could not connect to Ollama"):
            generate_text_ollama(model="test-model", prompt="test", verbose=False)


def test_generate_text_ollama_timeout(monkeypatch) -> None:
    """Test that timeout errors are properly handled."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_requests = _create_mock_requests()
    mock_requests.post.side_effect = mock_requests.exceptions.Timeout("Request timed out")
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        with pytest.raises(OllamaError, match="timed out after 3600 seconds"):
            generate_text_ollama(model="test-model", prompt="test", verbose=False)


def test_generate_text_ollama_empty_response(monkeypatch) -> None:
    """Test that empty responses raise an error."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": ""}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        with pytest.raises(OllamaError, match="empty response"):
            generate_text_ollama(model="test-model", prompt="test", verbose=False)


def test_generate_text_ollama_success(monkeypatch) -> None:
    """Test successful Ollama request."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Test response from Ollama"}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        result = generate_text_ollama(model="test-model", prompt="test", verbose=False)
        
        assert result == "Test response from Ollama"
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"
        assert call_args[1]["json"]["model"] == "test-model"
        assert call_args[1]["json"]["prompt"] == "test"
        assert call_args[1]["json"]["stream"] is False
        assert call_args[1]["timeout"] == 3600


def test_generate_text_ollama_custom_url(monkeypatch) -> None:
    """Test that custom OLLAMA_URL is used."""
    custom_url = "http://custom-host:8080"
    monkeypatch.setenv("OLLAMA_URL", custom_url)
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Response"}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        generate_text_ollama(model="test-model", prompt="test", verbose=False)
        
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == f"{custom_url}/api/generate"


def test_generate_text_ollama_verbose_output(monkeypatch, capsys) -> None:
    """Test that verbose mode produces output."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Test response"}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}), \
         patch("pianist.ai_providers.time.time", side_effect=[0.0, 1.5]):
        result = generate_text_ollama(model="test-model", prompt="test", verbose=True)
        
        assert result == "Test response"
        captured = capsys.readouterr()
        assert "Sending request to Ollama" in captured.err
        assert "test-model" in captured.err
        assert "Response complete" in captured.err


def test_generate_text_ollama_error_includes_timing(monkeypatch) -> None:
    """Test that errors include timing information in verbose mode."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_requests = _create_mock_requests()
    mock_requests.post.side_effect = Exception("Test error")
    
    with patch.dict("sys.modules", {"requests": mock_requests}), \
         patch("pianist.ai_providers.time.time", side_effect=[0.0, 2.5]):
        with pytest.raises(OllamaError, match="after 2.5s"):
            generate_text_ollama(model="test-model", prompt="test", verbose=True)


def test_generate_text_unified_gemini(monkeypatch) -> None:
    """Test unified interface routes to Gemini correctly."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    
    mock_google = MagicMock()
    mock_genai = MagicMock()
    mock_client = MagicMock()
    mock_models = MagicMock()
    
    mock_chunk = MagicMock()
    mock_chunk.text = "Gemini response"
    mock_models.generate_content_stream = MagicMock(return_value=iter([mock_chunk]))
    mock_client.models = mock_models
    mock_genai.Client = MagicMock(return_value=mock_client)
    mock_google.genai = mock_genai
    
    with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai}):
        result = generate_text_unified(
            provider="gemini",
            model="gemini-flash-latest",
            prompt="test",
            verbose=False
        )
        
        assert result == "Gemini response"
        mock_genai.Client.assert_called_once()


def test_generate_text_unified_ollama(monkeypatch) -> None:
    """Test unified interface routes to Ollama correctly."""
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Ollama response"}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        result = generate_text_unified(
            provider="ollama",
            model="test-model",
            prompt="test",
            verbose=False
        )
        
        assert result == "Ollama response"
        mock_requests.post.assert_called_once()


def test_generate_text_unified_invalid_provider() -> None:
    """Test that invalid provider raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        generate_text_unified(
            provider="invalid",
            model="test-model",
            prompt="test",
            verbose=False
        )


def test_generate_text_unified_gemini_error_propagates(monkeypatch) -> None:
    """Test that Gemini errors propagate through unified interface."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    
    with pytest.raises(GeminiError, match="Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set"):
        generate_text_unified(
            provider="gemini",
            model="gemini-flash-latest",
            prompt="test",
            verbose=False
        )


def test_generate_text_unified_ollama_error_propagates(monkeypatch) -> None:
    """Test that Ollama errors propagate through unified interface."""
    try:
        import requests
    except ImportError:
        pytest.skip("requests library not available")
    
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    with patch("pianist.ai_providers.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        with pytest.raises(OllamaError, match="Could not connect to Ollama"):
            generate_text_unified(
                provider="ollama",
                model="test-model",
                prompt="test",
                verbose=False
            )


def test_generate_text_unified_ollama_no_gemini_messages(monkeypatch, capsys) -> None:
    """Test that Gemini API key messages don't appear when using Ollama."""
    # Set both Gemini API keys to ensure they exist
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Ollama response"}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}):
        # Use Ollama provider
        result = generate_text_unified(
            provider="ollama",
            model="test-model",
            prompt="test",
            verbose=False
        )
        
        assert result == "Ollama response"
        
        # Verify no Gemini API key messages appear
        captured = capsys.readouterr()
        assert "GEMINI_API_KEY" not in captured.err
        assert "GOOGLE_API_KEY" not in captured.err
        assert "Both GOOGLE_API_KEY and GEMINI_API_KEY" not in captured.err


def test_generate_text_unified_ollama_verbose_no_gemini_messages(monkeypatch, capsys) -> None:
    """Test that Gemini API key messages don't appear when using Ollama with verbose."""
    # Set both Gemini API keys to ensure they exist
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Ollama response"}
    mock_response.raise_for_status = MagicMock()
    
    mock_requests = _create_mock_requests()
    mock_requests.post.return_value = mock_response
    
    with patch.dict("sys.modules", {"requests": mock_requests}), \
         patch("pianist.ai_providers.time.time", side_effect=[0.0, 1.0]):
        # Use Ollama provider with verbose
        result = generate_text_unified(
            provider="ollama",
            model="test-model",
            prompt="test",
            verbose=True
        )
        
        assert result == "Ollama response"
        
        # Verify no Gemini API key messages appear, even with verbose
        captured = capsys.readouterr()
        assert "GEMINI_API_KEY" not in captured.err
        assert "GOOGLE_API_KEY" not in captured.err
        assert "Both GOOGLE_API_KEY and GEMINI_API_KEY" not in captured.err
        # But Ollama messages should appear
        assert "Sending request to Ollama" in captured.err

