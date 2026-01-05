# Gemini Schema Compatibility

## Issue

The current JSON Schema implementation uses the `discriminator` keyword for discriminated unions (the `Event` type). While this is valid JSON Schema Draft 2019-09+, **Google Gemini's structured output only supports a subset of JSON Schema** and does not support the `discriminator` keyword.

## Solution

We've added a Gemini-compatible schema generator that:

1. **Removes the `discriminator` keyword** - This is not supported by Gemini
2. **Preserves functionality** - Each event type (`NoteEvent`, `PedalEvent`, `TempoEvent`) already has a `type` field with a `const` value, so the `oneOf` pattern works correctly without the discriminator
3. **Maintains all other schema features** - Constraints, types, descriptions, etc. are all preserved

## Usage

### Generate Gemini-Compatible Schema

```bash
# Generate all schemas (including Gemini-compatible)
pianist generate-schema

# Or generate only the Gemini schema
pianist generate-schema --format gemini

# Or use the Python module directly
python -m pianist.generate_openapi_schema
```

This generates:
- `schema.json` - Standard JSON Schema (for OpenAI, Anthropic, etc.)
- `schema.gemini.json` - Gemini-compatible schema (discriminator removed)
- `schema.openapi.json` - Full OpenAPI specification

### Use with Gemini API

```python
from google import genai
import json

client = genai.Client()

# Load the Gemini-compatible schema
with open("schema.gemini.json", "r") as f:
    schema = json.load(f)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Create a piano piece in C major, 64 beats long.",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": schema,
    },
)

composition = json.loads(response.text)
```

## Technical Details

### What Was Changed

The `make_gemini_compatible()` function recursively traverses the schema and removes any `discriminator` keywords. The schema structure remains otherwise identical.

### Why This Works

The original schema used:
```json
{
  "oneOf": [...],
  "discriminator": {
    "propertyName": "type",
    "mapping": {...}
  }
}
```

The Gemini-compatible schema uses:
```json
{
  "oneOf": [...]
}
```

Since each event type in the `oneOf` array has a `type` field with a `const` value:
- `NoteEvent`: `"type": {"const": "note"}`
- `PedalEvent`: `"type": {"const": "pedal"}`
- `TempoEvent`: `"type": {"const": "tempo"}`

Gemini can still correctly determine which schema variant to use based on the `type` field value, even without the discriminator.

## Limitations

According to Gemini's documentation:
- **Schema subset**: Not all JSON Schema features are supported (unsupported properties are ignored)
- **Schema complexity**: Very large or deeply nested schemas may be rejected

Our schema should work fine, but if you encounter issues, consider:
- Simplifying property names
- Reducing nesting depth
- Limiting the number of constraints

## References

- [Gemini Structured Output Documentation](https://ai.google.dev/gemini-api/docs/structured-output?example=recipe#json_schema_support)
- [JSON Schema Specification](https://json-schema.org/)
