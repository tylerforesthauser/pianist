from __future__ import annotations

import pytest

from pianist.parser import parse_composition_from_text


def test_parser_accepts_fenced_json() -> None:
    text = """here you go

```json
{
  "title": "x",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {"events": [{"type": "note", "start": 0, "duration": 1, "pitches": ["C4"]}]}
  ]
}
```
"""
    comp = parse_composition_from_text(text)
    assert comp.title == "x"


def test_parser_errors_without_json() -> None:
    with pytest.raises(ValueError):
        parse_composition_from_text("no braces here")


def test_parser_repairs_common_llm_json_issues() -> None:
    # Trailing commas are a common failure mode for LLM-generated JSON.
    text = """```json
{
  "title": "x",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [{"events": [{"type": "note", "start": 0, "duration": 1, "pitches": ["C4"]}]}],
}
```"""
    comp = parse_composition_from_text(text)
    assert comp.title == "x"


def test_parser_converts_ticks_to_beats() -> None:
    """Test that parser detects and converts tick values to beats."""
    # Simulate a case where the model outputs ticks instead of beats
    # ppq=480, so 1920 ticks = 4 beats, 3840 ticks = 8 beats
    text = """{
  "title": "Test",
  "bpm": 120,
  "ppq": 480,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "events": [
        {"type": "note", "start": 1920, "duration": 1920, "pitches": ["C4"]},
        {"type": "note", "start": 3840, "duration": 960, "pitches": ["D4"]}
      ]
    }
  ]
}"""
    comp = parse_composition_from_text(text)
    # After conversion, start values should be in beats
    events = comp.tracks[0].events
    assert events[0].start == 4.0  # 1920 / 480 = 4
    assert events[0].duration == 4.0  # 1920 / 480 = 4
    assert events[1].start == 8.0  # 3840 / 480 = 8
    assert events[1].duration == 2.0  # 960 / 480 = 2


def test_parser_does_not_convert_legitimate_beats() -> None:
    """Test that parser doesn't convert values that are already in beats."""
    # Values that are already in beats (small, not multiples of ppq)
    text = """{
  "title": "Test",
  "bpm": 120,
  "ppq": 480,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [
    {
      "events": [
        {"type": "note", "start": 0, "duration": 1, "pitches": ["C4"]},
        {"type": "note", "start": 4, "duration": 2, "pitches": ["D4"]}
      ]
    }
  ]
}"""
    comp = parse_composition_from_text(text)
    # Values should remain unchanged
    events = comp.tracks[0].events
    assert events[0].start == 0.0
    assert events[0].duration == 1.0
    assert events[1].start == 4.0
    assert events[1].duration == 2.0

