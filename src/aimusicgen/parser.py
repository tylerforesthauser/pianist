from __future__ import annotations

import json
import re
from typing import Any

from json_repair import repair_json

from .schema import Composition, validate_composition_dict


_FENCED_JSON_RE = re.compile(
    r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE | re.MULTILINE
)


def _extract_candidate_json(text: str) -> str:
    """
    Extract the most likely JSON object from an LLM response.

    Strategy:
    - Prefer fenced ```json blocks
    - Otherwise, take the first top-level {...} block by brace matching
    """
    m = _FENCED_JSON_RE.search(text)
    if m:
        return m.group(1).strip()

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found (missing '{').")

    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1].strip()

    raise ValueError("Unterminated JSON object (brace matching failed).")


def _loads_lenient(candidate: str) -> dict[str, Any]:
    """
    Parse JSON strictly, then fall back to JSON repair for common LLM issues.
    """
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        repaired = repair_json(candidate)
        obj = json.loads(repaired)

    if not isinstance(obj, dict):
        raise ValueError("Top-level JSON must be an object.")
    return obj


def parse_composition_from_text(text: str) -> Composition:
    """
    Parse a Composition from raw model output (free-form text).
    """
    candidate = _extract_candidate_json(text)
    data = _loads_lenient(candidate)
    return validate_composition_dict(data)

