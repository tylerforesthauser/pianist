from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv  # type: ignore
    
    # Load .env file from project root or current directory
    # Look for .env in: current dir, parent dirs up to 3 levels, or project root
    env_paths = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path.cwd().parent.parent / ".env",
        Path(__file__).parent.parent.parent / ".env",  # Project root
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # Don't override existing env vars
            break
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


class GeminiError(RuntimeError):
    pass


class OllamaError(RuntimeError):
    pass


def generate_text(*, model: str, prompt: str, verbose: bool = False) -> str:
    """
    Generate text using Google Gemini via the Google GenAI SDK.

    This is intentionally tiny and CLI-friendly:
    - Reads API key from `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable
      or from a `.env` file (if python-dotenv is installed).
      Prefers `GEMINI_API_KEY` if both are set.
      Environment variables override `.env` file values.
    - Supports streaming to capture partial responses on interruption.
    - Returns response.text (string).
    - Raises GeminiError with actionable messages on failure.

    Args:
        model: The Gemini model name (e.g., "gemini-flash-latest").
        prompt: The prompt text to send to Gemini.
        verbose: If True, print progress indicators and timing information.

    Returns:
        The generated text response from Gemini.
    """
    # Check for API key - prefer GEMINI_API_KEY, but accept GOOGLE_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if api_key and google_api_key:
        if verbose:
            sys.stderr.write("Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GEMINI_API_KEY.\n")
    elif google_api_key and not api_key:
        api_key = google_api_key
        if verbose:
            sys.stderr.write("Using GOOGLE_API_KEY (GEMINI_API_KEY not set).\n")
    
    if not api_key:
        raise GeminiError(
            "Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Export one of them, e.g.:\n"
            "  export GEMINI_API_KEY='...'\n"
            "  # or\n"
            "  export GOOGLE_API_KEY='...'\n"
            "Then retry the command."
        )

    try:
        # Per Gemini API quickstart: pip install -U google-genai; from google import genai
        from google import genai  # type: ignore
    except Exception as e:  # ImportError, ModuleNotFoundError, etc.
        raise GeminiError(
            "Gemini support is not installed. Install the optional extra:\n"
            "  python3 -m pip install -e '.[gemini]'\n"
            "or:\n"
            "  python3 -m pip install 'pianist[gemini]'"
        ) from e

    try:
        start_time = time.time()
        
        if verbose:
            sys.stderr.write(f"Sending request to Gemini ({model})...\n")
            sys.stderr.flush()
        
        # The client reads API key from env automatically (quickstart behavior).
        # The SDK checks GEMINI_API_KEY first, then GOOGLE_API_KEY.
        # We've already validated that at least one is set above.
        client = genai.Client()
        
        # Try streaming first to get partial responses, fallback to non-streaming if not supported
        try:
            if verbose:
                sys.stderr.write("Waiting for response (streaming enabled)...\n")
                sys.stderr.flush()
            
            # Use streaming to capture partial responses
            stream = client.models.generate_content_stream(model=model, contents=prompt)
            
            accumulated_text = ""
            chunk_count = 0
            last_progress_time = start_time
            
            for chunk in stream:
                chunk_count += 1
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    accumulated_text += str(chunk_text)
                    
                    # Show progress every 2 seconds if verbose
                    if verbose:
                        current_time = time.time()
                        if current_time - last_progress_time >= 2.0:
                            elapsed = current_time - start_time
                            sys.stderr.write(f"  Received {chunk_count} chunks, {len(accumulated_text)} chars so far ({elapsed:.1f}s elapsed)...\n")
                            sys.stderr.flush()
                            last_progress_time = current_time
            
            elapsed_time = time.time() - start_time
            
            if not accumulated_text.strip():
                raise GeminiError("Gemini returned an empty response.")
            
            if verbose:
                sys.stderr.write(f"Response complete: {len(accumulated_text)} chars in {elapsed_time:.1f}s ({chunk_count} chunks)\n")
                sys.stderr.flush()
            
            return accumulated_text
            
        except (AttributeError, TypeError) as e:
            # Streaming might not be supported, fallback to regular generate_content
            if verbose:
                sys.stderr.write("Streaming not available, using regular API call...\n")
                sys.stderr.flush()
            
            response = client.models.generate_content(model=model, contents=prompt)
            text = getattr(response, "text", None)
            if text is None or not str(text).strip():
                raise GeminiError("Gemini returned an empty response.")
            
            elapsed_time = time.time() - start_time
            if verbose:
                sys.stderr.write(f"Response complete: {len(text)} chars in {elapsed_time:.1f}s\n")
                sys.stderr.flush()
            
            return str(text)
                    
    except GeminiError:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = f"Gemini request failed: {type(e).__name__}: {e}"
        if verbose and elapsed_time > 0:
            error_msg += f" (after {elapsed_time:.1f}s)"
        raise GeminiError(error_msg) from e


def generate_text_ollama(*, model: str, prompt: str, verbose: bool = False) -> str:
    """
    Generate text using a local Ollama model.
    
    This function calls a local Ollama instance running at http://localhost:11434
    (or the URL specified in OLLAMA_URL environment variable).
    
    Args:
        model: The Ollama model name (e.g., "gpt-oss:20b", "gemma3:4b", "deepseek-r1:8b").
        prompt: The prompt text to send to Ollama.
        verbose: If True, print progress indicators and timing information.
    
    Returns:
        The generated text response from Ollama.
    
    Raises:
        OllamaError: If Ollama is not available, connection fails, or request times out.
    """
    try:
        import requests
    except ImportError:
        raise OllamaError(
            "requests library required for Ollama support. Install with: pip install requests"
        )
    
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    if verbose:
        sys.stderr.write(f"Sending request to Ollama ({model}) at {ollama_url}...\n")
        sys.stderr.flush()
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,  # 2 minute timeout
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "")
        
        elapsed_time = time.time() - start_time
        
        if not response_text.strip():
            raise OllamaError("Ollama returned an empty response.")
        
        if verbose:
            sys.stderr.write(f"Response complete: {len(response_text)} chars in {elapsed_time:.1f}s\n")
            sys.stderr.flush()
        
        return response_text
        
    except requests.exceptions.ConnectionError:
        raise OllamaError(
            f"Could not connect to Ollama at {ollama_url}. "
            "Make sure Ollama is installed and running. See: https://ollama.ai"
        )
    except requests.exceptions.Timeout:
        raise OllamaError(f"Ollama request timed out after 120 seconds")
    except OllamaError:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = f"Ollama request failed: {type(e).__name__}: {e}"
        if verbose and elapsed_time > 0:
            error_msg += f" (after {elapsed_time:.1f}s)"
        raise OllamaError(error_msg) from e


def generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
    """
    Unified interface for generating text from either Gemini or Ollama.
    
    Args:
        provider: Either "gemini" or "ollama"
        model: Model name (provider-specific)
        prompt: The prompt text
        verbose: If True, print progress indicators
    
    Returns:
        Generated text response
    
    Raises:
        GeminiError: For Gemini-specific errors
        OllamaError: For Ollama-specific errors
        ValueError: For unsupported providers
    """
    if provider == "gemini":
        return generate_text(model=model, prompt=prompt, verbose=verbose)
    elif provider == "ollama":
        return generate_text_ollama(model=model, prompt=prompt, verbose=verbose)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'gemini' or 'ollama'.")


