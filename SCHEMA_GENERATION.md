# Schema Generation for Structured Output

This document explains how to generate OpenAPI/JSON Schema files for use with AI models that support structured output.

## Overview

The `generate_openapi_schema.py` script generates two schema formats from the Pydantic models:

1. **OpenAPI Schema** (`schema.openapi.json`): Full OpenAPI 3.1.0 specification
2. **JSON Schema** (`schema.json`): Pure JSON Schema (often preferred by AI models)

## Generating the Schemas

### Prerequisites

Ensure you have the project dependencies installed:

```bash
pip install -e .
```

### Running the Generator

```bash
python -m pianist.generate_openapi_schema
```

Or if running from the project root:

```bash
python -m src.pianist.generate_openapi_schema
```

This will generate:
- `schema.openapi.json` - Full OpenAPI specification
- `schema.json` - JSON Schema only (most commonly used)

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
- Discriminated unions (like the Event type) are properly represented using `oneOf` with discriminator
- Default values are included in the schema

## Updating the Schema

Whenever you modify the Pydantic models in `schema.py`, regenerate the schema files by running the generator script again.

