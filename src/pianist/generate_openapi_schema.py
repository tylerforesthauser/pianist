"""
Generate OpenAPI schema from Pydantic models for structured output.

This script generates a JSON Schema/OpenAPI schema that can be used with
AI models that support structured output (e.g., OpenAI function calling,
Anthropic structured outputs, Gemini structured outputs, etc.).
"""

from __future__ import annotations

import json
from pathlib import Path

from pianist.schema import Composition


def make_gemini_compatible(schema: dict) -> dict:
    """
    Convert a JSON Schema to be compatible with Gemini's structured output UI.
    
    Gemini's UI has strict requirements:
    - No OpenAPI-specific features (discriminator, default, title, const)
    - No array type syntax (["string", "null"] must become "string")
    - No numeric enums (must be strings)
    - No oneOf (replaced with common properties)
    - All object types must have non-empty properties
    - All $ref references must be inlined
    
    Args:
        schema: The JSON Schema dictionary to convert
        
    Returns:
        A Gemini-compatible JSON Schema dictionary with all references inlined
    """
    # Deep copy
    result = json.loads(json.dumps(schema))
    
    # Convert $defs to definitions for Draft 7 compatibility
    if "$defs" in result:
        result["definitions"] = result.pop("$defs")
        old_ref_prefix = "#/$defs/"
        new_ref_prefix = "#/definitions/"
    else:
        old_ref_prefix = "#/$defs/"
        new_ref_prefix = "#/definitions/"
    
    def convert_anyof_to_single_type(obj: dict) -> dict:
        """Convert anyOf to single type, preferring most permissive type."""
        if "anyOf" not in obj or not isinstance(obj.get("anyOf"), list):
            return obj
        
        anyof_items = obj["anyOf"]
        if not anyof_items:
            return obj
        
        # Collect types (excluding null)
        types = []
        for item in anyof_items:
            if isinstance(item, dict) and "type" in item and item["type"] != "null":
                types.append(item["type"])
        
        if types:
            # Choose most permissive type
            type_priority = {"string": 0, "number": 1, "integer": 2, "array": 3, "object": 4, "boolean": 5}
            sorted_types = sorted(types, key=lambda t: type_priority.get(t, 99))
            obj = {k: v for k, v in obj.items() if k != "anyOf"}
            obj["type"] = sorted_types[0]
        
        return obj
    
    def process_schema(obj: dict | list | str | int | float | bool | None) -> dict | list | str | int | float | bool | None:
        """Recursively process schema to make it Gemini-compatible."""
        if isinstance(obj, dict):
            # Convert anyOf to single type
            obj = convert_anyof_to_single_type(obj)
            
            # Convert array type syntax to single type
            if "type" in obj and isinstance(obj["type"], list):
                type_array = obj["type"]
                non_null_types = [t for t in type_array if t != "null"]
                if non_null_types:
                    type_priority = {"string": 0, "number": 1, "integer": 2, "array": 3, "object": 4, "boolean": 5}
                    sorted_types = sorted(non_null_types, key=lambda t: type_priority.get(t, 99))
                    obj["type"] = sorted_types[0]
                else:
                    obj["type"] = "string"
            
            # Convert numeric enums to string enums
            if "enum" in obj and isinstance(obj["enum"], list):
                if obj["enum"] and all(isinstance(v, (int, float)) for v in obj["enum"]):
                    obj["enum"] = [str(v) for v in obj["enum"]]
                    if obj.get("type") in ("integer", "number"):
                        obj["type"] = "string"
            
            # Remove unsupported fields
            unsupported = ("discriminator", "default", "title", "exclusiveMaximum", 
                          "exclusiveMinimum", "const", "anyOf")
            obj = {k: v for k, v in obj.items() if k not in unsupported}
            
            # Replace oneOf with common properties (type and start for events)
            if "oneOf" in obj:
                new_obj = {k: v for k, v in obj.items() if k != "oneOf"}
                if "type" not in new_obj:
                    new_obj["type"] = "object"
                if new_obj.get("type") == "object" and "properties" not in new_obj:
                    new_obj["properties"] = {
                        "type": {"type": "string"},
                        "start": {"type": "number", "minimum": 0}
                    }
                    new_obj["required"] = ["type", "start"]
                obj = new_obj
            
            # Ensure all object types have non-empty properties
            if obj.get("type") == "object":
                if "properties" not in obj or not obj["properties"]:
                    obj["properties"] = {"type": {"type": "string"}}
            
            # Update $ref references
            if "$ref" in obj and isinstance(obj["$ref"], str):
                if obj["$ref"].startswith(old_ref_prefix):
                    obj["$ref"] = obj["$ref"].replace(old_ref_prefix, new_ref_prefix)
            
            # Recursively process all values
            return {k: process_schema(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [process_schema(item) for item in obj]
        else:
            return obj
    
    result = process_schema(result)
    
    # Inline all $ref references
    def inline_refs(schema: dict, definitions: dict) -> dict:
        """Recursively inline all $ref references."""
        def resolve(obj: dict | list | str | int | float | bool | None) -> dict | list | str | int | float | bool | None:
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref_path = obj["$ref"]
                    if ref_path.startswith("#/definitions/"):
                        schema_name = ref_path.replace("#/definitions/", "")
                        if schema_name in definitions:
                            resolved = resolve(definitions[schema_name])
                            if isinstance(resolved, dict):
                                return {k: resolve(v) for k, v in resolved.items()}
                            return resolved
                    return obj
                return {k: resolve(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve(item) for item in obj]
            else:
                return obj
        return resolve(schema)
    
    # Get definitions and inline
    definitions = result.pop("definitions", {})
    result = inline_refs(result, definitions)
    
    # Final pass to ensure all object types have properties after inlining
    def ensure_properties(obj: dict | list | str | int | float | bool | None) -> dict | list | str | int | float | bool | None:
        if isinstance(obj, dict):
            if obj.get("type") == "object":
                if "properties" not in obj or not obj["properties"]:
                    obj["properties"] = {"type": {"type": "string"}}
            return {k: ensure_properties(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ensure_properties(item) for item in obj]
        else:
            return obj
    
    result = ensure_properties(result)
    return result


def generate_openapi_schema() -> dict:
    """
    Generate an OpenAPI schema object from the Composition Pydantic model.
    
    Returns a dictionary containing the OpenAPI schema that can be used
    with AI models supporting structured output.
    """
    json_schema = Composition.model_json_schema(mode="serialization", by_alias=False)
    
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Pianist Composition Schema",
            "description": "Schema for piano composition specifications generated by AI models",
            "version": "1.0.0",
        },
        "components": {
            "schemas": {
                "Composition": json_schema,
            },
        },
    }


def generate_gemini_schema() -> dict:
    """
    Generate a Gemini-compatible schema with all references inlined.
    
    This schema is optimized for Gemini's UI and has all $ref references
    resolved, making it self-contained and ready to use.
    """
    json_schema = Composition.model_json_schema(mode="serialization", by_alias=False)
    return make_gemini_compatible(json_schema)


def main() -> None:
    """Generate and save both OpenAPI and Gemini-compatible schemas."""
    project_root = Path(__file__).parent.parent.parent
    schemas_dir = project_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate schemas
    openapi_schema = generate_openapi_schema()
    gemini_schema = generate_gemini_schema()
    
    # Save OpenAPI schema
    openapi_path = schemas_dir / "schema.openapi.json"
    with open(openapi_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Generated OpenAPI schema: {openapi_path}")
    
    # Save Gemini-compatible schema
    gemini_path = schemas_dir / "schema.gemini.json"
    with open(gemini_path, "w") as f:
        json.dump(gemini_schema, f, indent=2)
    print(f"Generated Gemini-compatible schema: {gemini_path}")


if __name__ == "__main__":
    main()
