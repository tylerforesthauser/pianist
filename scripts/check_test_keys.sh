#!/bin/bash
# Check if API keys are set for integration tests

set -e

echo "Checking API keys for integration tests..."
echo ""

# Check Gemini
if [ -n "$GEMINI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ]; then
    if [ -n "$GEMINI_API_KEY" ] && [ -n "$GOOGLE_API_KEY" ]; then
        echo "✅ Gemini: GEMINI_API_KEY and GOOGLE_API_KEY both set (GEMINI_API_KEY will be used)"
    elif [ -n "$GEMINI_API_KEY" ]; then
        echo "✅ Gemini: GEMINI_API_KEY set"
    else
        echo "✅ Gemini: GOOGLE_API_KEY set"
    fi
else
    echo "❌ Gemini: GEMINI_API_KEY or GOOGLE_API_KEY not set"
fi

# Check OpenRouter
if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "✅ OpenRouter: OPENROUTER_API_KEY set"
else
    echo "❌ OpenRouter: OPENROUTER_API_KEY not set"
fi

# Check Ollama
if [ -n "$OLLAMA_URL" ]; then
    echo "✅ Ollama: OLLAMA_URL set to $OLLAMA_URL"
else
    echo "⚠️  Ollama: OLLAMA_URL not set (defaults to http://localhost:11434)"

    # Try to check if Ollama is running
    if command -v curl &> /dev/null; then
        if curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "   ✅ Ollama appears to be running at http://localhost:11434"
        else
            echo "   ❌ Ollama does not appear to be running at http://localhost:11434"
        fi
    fi
fi

echo ""
echo "Summary:"
echo "--------"

# Count available providers
available=0
if [ -n "$GEMINI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ]; then
    available=$((available + 1))
fi
if [ -n "$OPENROUTER_API_KEY" ]; then
    available=$((available + 1))
fi
if [ -n "$OLLAMA_URL" ] || curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
    available=$((available + 1))
fi

if [ $available -eq 0 ]; then
    echo "❌ No providers available. Integration tests will be skipped."
    echo ""
    echo "To set up API keys:"
    echo "  export OPENROUTER_API_KEY='your-key'  # Recommended: free tier available"
    echo "  export GEMINI_API_KEY='your-key'      # Optional"
    echo "  # Or create a .env file with these variables"
    exit 1
elif [ $available -eq 1 ]; then
    echo "⚠️  Only 1 provider available. Some integration tests may be skipped."
    exit 0
else
    echo "✅ $available providers available. Integration tests should run."
    exit 0
fi
