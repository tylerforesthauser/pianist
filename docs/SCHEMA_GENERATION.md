# Schema Generation for Structured Output

This document explains how to generate OpenAPI/JSON Schema files for use with AI models that support structured output.

## Overview

The schema generation creates two schema formats from the Pydantic models:

1. **OpenAPI Schema** (`schemas/schema.openapi.json`): Full OpenAPI 3.1.0 specification for general use
2. **Gemini-compatible Schema** (`schemas/schema.gemini.json`): JSON Schema optimized for Google Gemini's structured output UI (all references inlined)

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

By default, this generates both:
- `schemas/schema.openapi.json` - Full OpenAPI specification
- `schemas/schema.gemini.json` - Gemini-compatible schema (inlined, ready for UI)

You can also generate individual formats:

```bash
# Generate only OpenAPI schema
./pianist generate-schema --format openapi

# Generate only Gemini-compatible schema
./pianist generate-schema --format gemini
```

Alternatively, you can use the Python module directly:

```bash
python3 -m pianist.generate_openapi_schema
```

This will generate both schema formats.

## Using with AI Models

### OpenAI (Function Calling / Structured Outputs)

For OpenAI's structured outputs, extract the JSON Schema from the OpenAPI schema:

```python
from openai import OpenAI
import json

client = OpenAI()

# Load the OpenAPI schema and extract the Composition schema
with open("schemas/schema.openapi.json", "r") as f:
    openapi_schema = json.load(f)
    composition_schema = openapi_schema["components"]["schemas"]["Composition"]

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
            "schema": composition_schema,
            "description": "A piano composition specification"
        }
    }
)
```

### Anthropic (Structured Outputs)

For Anthropic's structured outputs, extract the JSON Schema from the OpenAPI schema:

```python
from anthropic import Anthropic
import json

client = Anthropic()

# Load the OpenAPI schema and extract the Composition schema
with open("schemas/schema.openapi.json", "r") as f:
    openapi_schema = json.load(f)
    composition_schema = openapi_schema["components"]["schemas"]["Composition"]

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
            "schema": composition_schema
        }
    }
)
```

### Google Gemini (Structured Outputs)

**Important**: Use the **Gemini-compatible schema** (`schemas/schema.gemini.json`) for Gemini. This schema is optimized for Gemini's UI and has all `$ref` references inlined.

The Gemini-compatible schema:
- Removes OpenAPI-specific features (`discriminator`, `default`, `title`, `const`)
- Converts array type syntax to single types (Gemini UI doesn't support `["string", "null"]`)
- Converts numeric enums to string enums
- Replaces `oneOf` with common properties (`type` and `start` for events)
- Inlines all `$ref` references for UI compatibility
- Ensures all object types have non-empty properties

**Note on discriminated unions**: The schema replaces `oneOf` for event types with a generic object type containing common properties (`type` and `start`). While this loses schema-level type discrimination, validation still occurs in the Python code to ensure only valid event types (NoteEvent, PedalEvent, TempoEvent) are accepted.

Example usage with Gemini:

```python
import json
import google.generativeai as genai

# Load the Gemini-compatible schema
with open("schemas/schema.gemini.json", "r") as f:
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

For Gemini's UI, paste the contents of `schemas/schema.gemini.json` directly into the schema field.

### Other Models

Most AI models that support structured output accept JSON Schema. Extract the Composition schema from the OpenAPI schema:

```python
import json

with open("schemas/schema.openapi.json", "r") as f:
    openapi_schema = json.load(f)
    composition_schema = openapi_schema["components"]["schemas"]["Composition"]

# Use composition_schema with your AI model's structured output API
```

## Schema Contents

The generated schema includes:

- **Composition**: Top-level structure with title, bpm, time_signature, tracks, etc.
- **Track**: Track definition with name, channel, program, and events
- **Event Types**: Union of:
  - `NoteEvent`: Notes with pitch, timing, velocity, and hand/voice labels
  - `PedalEvent`: Sustain pedal events
  - `TempoEvent`: Tempo changes (instant or gradual)
- **TimeSignature**: Time signature with numerator and denominator
- **LabeledNote** and **NoteGroup**: Structures for hand/voice labeling

All constraints from the Pydantic models (field types, ranges, required fields, etc.) are preserved in the generated schema.

## Notes

- The schema uses `mode="serialization"` to ensure it matches how data is serialized to JSON
- Field validators and model validators are represented as constraints in the schema
- Discriminated unions (like the Event type) are represented using `oneOf` in the standard schema
- The Gemini schema replaces `oneOf` with common properties for UI compatibility

## Updating the Schema

Whenever you modify the Pydantic models in `schema.py`, regenerate the schema files by running:

```bash
./pianist generate-schema
```

This will regenerate both `schemas/schema.openapi.json` and `schemas/schema.gemini.json`.
