from __future__ import annotations

import copy
import json
import re
from typing import Any

from json_repair import repair_json

from .schema import Composition, validate_composition_dict


_FENCED_BLOCK_RE = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE | re.MULTILINE
)


def _extract_first_json_object(text: str) -> str:
    if not text.strip():
        raise ValueError("Input is empty or contains only whitespace.")
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


def _extract_candidate_json(text: str) -> str:
    """
    Extract the most likely JSON object from an LLM response.

    Strategy:
    - Prefer fenced ```json blocks
    - Otherwise, take the first top-level {...} block by brace matching
    """
    m = _FENCED_BLOCK_RE.search(text)
    if m:
        fenced = m.group(1)
        return _extract_first_json_object(fenced)
    return _extract_first_json_object(text)


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


def _normalize_timing_units(data: dict[str, Any]) -> dict[str, Any]:
    """
    Detect and fix cases where the model outputs start/duration in ticks instead of beats.
    
    Heuristic: If start/duration values are suspiciously large (>1000) and are multiples
    of the ppq value, assume they're in ticks and convert to beats by dividing by ppq.
    """
    ppq = data.get("ppq", 480)
    
    # Check if we have suspiciously large timing values that are multiples of ppq
    has_tick_values = False
    for track in data.get("tracks", []):
        for ev in track.get("events", []):
            start = ev.get("start")
            duration = ev.get("duration")
            
            # Check if start is suspiciously large and a multiple of ppq
            if isinstance(start, (int, float)) and start > 1000:
                # Check if it's a multiple of ppq (within rounding tolerance)
                remainder = start % ppq
                if remainder < 0.01 or remainder > (ppq - 0.01):
                    has_tick_values = True
                    break
            
            # Check duration too
            if isinstance(duration, (int, float)) and duration > 1000:
                remainder = duration % ppq
                if remainder < 0.01 or remainder > (ppq - 0.01):
                    has_tick_values = True
                    break
        
        if has_tick_values:
            break
    
    # If we detected tick values, convert all timing values to beats
    if has_tick_values:
        # Create a deep copy to avoid mutating the original
        data = copy.deepcopy(data)
        
        for track in data.get("tracks", []):
            for ev in track.get("events", []):
                if "start" in ev and isinstance(ev["start"], (int, float)):
                    ev["start"] = ev["start"] / ppq
                if "duration" in ev and isinstance(ev["duration"], (int, float)):
                    ev["duration"] = ev["duration"] / ppq
    
    return data


def parse_composition_from_text(text: str) -> Composition:
    """
    Parse a Composition from raw model output (free-form text).
    """
    if not text.strip():
        raise ValueError("Input is empty or contains only whitespace.")
    candidate = _extract_candidate_json(text)
    data = _loads_lenient(candidate)
    # Normalize timing units (fix cases where model outputs ticks instead of beats)
    data = _normalize_timing_units(data)
    return validate_composition_dict(data)

