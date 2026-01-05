# Schema Generation for Structured Output

This document explains how to generate OpenAPI/JSON Schema files for use with AI models that support structured output.

## Overview

The `generate_openapi_schema.py` script generates three schema formats from the Pydantic models:

1. **OpenAPI Schema** (`schema.openapi.json`): Full OpenAPI 3.1.0 specification
2. **JSON Schema** (`schema.json`): Pure JSON Schema (often preferred by AI models)
3. **Gemini-compatible Schema** (`schema.gemini.json`): JSON Schema optimized for Google Gemini's structured output

## Generating the Schemas

### Prerequisites

It's recommended to use a Python virtual environment to isolate dependencies:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install pianist in development mode
python3 -m pip install -e ".[dev]"
```

### Running the Generator

The recommended way to generate schemas is using the CLI command:

```bash
./pianist generate-schema
```

**Alternative:** You can also use the Python module directly:

```bash
python3 -m pianist generate-schema
```

**Note:** Use `./pianist` (recommended) or `python3 -m pianist` instead of `pianist` for maximum compatibility with editable installs.

By default, this generates:
- `schema.openapi.json` - Full OpenAPI specification
- `schema.json` - JSON Schema only (most commonly used)

To generate all three schema formats (including the Gemini-compatible schema):

```bash
./pianist generate-schema --format all
```

This will generate:
- `schema.openapi.json` - Full OpenAPI specification
- `schema.json` - JSON Schema only (most commonly used)
- `schema.gemini.json` - Gemini-compatible JSON Schema (removes OpenAPI-specific features)

You can also generate individual formats:

```bash
# Generate only OpenAPI schema
./pianist generate-schema --format openapi

# Generate only JSON schema
./pianist generate-schema --format json

# Generate only Gemini-compatible schema
./pianist generate-schema --format gemini
```

Alternatively, you can use the Python module directly:

```bash
python3 -m pianist.generate_openapi_schema
```

This will generate all three schema formats.

## Using with AI Models

### OpenAI (Function Calling / Structured Outputs)

For OpenAI's structured outputs, use the JSON Schema directly:

```python
from openai import OpenAI

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a music composition assistant."},
        {"role": "user", "content": "Create a piano piece in C major, 64 beats long."}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "composition",
            "strict": True,
            "schema": <load schema.json here>,
            "description": "A piano composition specification"
        }
    }
)
```

### Anthropic (Structured Outputs)

For Anthropic's structured outputs:

```python
from anthropic import Anthropic

client = Anthropic()

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Create a piano piece in C major, 64 beats long."}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "composition",
            "strict": True,
            "schema": <load schema.json here>
        }
    }
)
```

### Google Gemini (Structured Outputs)

**Important**: Gemini supports only a subset of JSON Schema and does not support OpenAPI-specific features like `discriminator` or the `default` keyword. Use the **Gemini-compatible schema** (`schema.gemini.json`) for Gemini.

The Gemini-compatible schema:
- Removes `discriminator` fields (OpenAPI-specific, not supported by Gemini)
- Removes `default` fields (not supported by Gemini's JSON Schema subset)
- Converts `$defs` to `definitions` for better compatibility (JSON Schema Draft 7)
- Updates all `$ref` references accordingly

Example usage with Gemini:

```python
import json
import google.generativeai as genai

# Load the Gemini-compatible schema
with open("schema.gemini.json", "r") as f:
    schema = json.load(f)

# Configure the model
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": schema,
    }
)

response = model.generate_content(
    "Create a piano piece in C major, 64 beats long."
)
```

### Other Models

Most AI models that support structured output accept JSON Schema in a similar format. The `schema.json` file can be loaded and used directly:

```python
import json

with open("schema.json", "r") as f:
    schema = json.load(f)

# Use schema with your AI model's structured output API
```

## Schema Contents

The generated schema includes:

- **Composition**: Top-level structure with title, bpm, time_signature, tracks, etc.
- **Track**: Track definition with name, channel, program, and events
- **Event Types**: Discriminated union of:
  - `NoteEvent`: Notes with pitch, timing, velocity, and hand/voice labels
  - `PedalEvent`: Sustain pedal events
  - `TempoEvent`: Tempo changes (instant or gradual)
- **TimeSignature**: Time signature with numerator and denominator
- **LabeledNote** and **NoteGroup**: Structures for hand/voice labeling

All constraints from the Pydantic models (field types, ranges, required fields, etc.) are preserved in the generated schema.

## Notes

- The schema uses `mode="serialization"` to ensure it matches how data is serialized to JSON
- Field validators and model validators are represented as constraints in the schema
- Discriminated unions (like the Event type) are represented using `oneOf`:
  - Standard schema (`schema.json`): Uses `oneOf` with `discriminator` (OpenAPI-specific)
  - Gemini schema (`schema.gemini.json`): Uses `oneOf` without `discriminator` (pure JSON Schema)
- Default values are included in the schema

## Gemini Compatibility

Gemini's structured output supports a subset of JSON Schema. The main differences in the Gemini-compatible schema:

1. **No `discriminator` fields**: Removed as they are OpenAPI-specific
2. **No `default` fields**: Gemini doesn't support the `default` keyword in JSON Schema
3. **`definitions` instead of `$defs`**: Uses JSON Schema Draft 7 format for better compatibility
4. **Pure JSON Schema**: All OpenAPI-specific features are removed

The `make_gemini_compatible()` function in `generate_openapi_schema.py` handles these conversions automatically.

## Updating the Schema

Whenever you modify the Pydantic models in `schema.py`, regenerate the schema files by running:

```bash
# Generate standard schemas (openapi + json)
./pianist generate-schema

# Or generate all schemas including Gemini-compatible
./pianist generate-schema --format all
```

