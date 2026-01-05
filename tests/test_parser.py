from __future__ import annotations

from aimusicgen.parser import parse_composition_from_text


def test_parser_handles_fenced_json_with_nested_objects() -> None:
    text = """
Some preface.

```json
{
  "title": "Nested Test",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "ppq": 480,
  "analysis": {"a": {"b": 1}},
  "tracks": [
    {"name": "Piano", "events": [{"type":"note","start":0,"duration":1,"pitch":"C4"}]}
  ]
}
```
Some suffix.
"""
    comp = parse_composition_from_text(text)
    assert comp.title == "Nested Test"


def test_parser_handles_unfenced_json_embedded_in_text() -> None:
    text = (
        "hello\n"
        '{"title":"Unfenced","bpm":120,"time_signature":{"numerator":4,"denominator":4},"ppq":480,'
        '"tracks":[{"events":[{"type":"note","start":0,"duration":1,"pitch":"C4"}]}]}\n'
        "goodbye\n"
    )
    comp = parse_composition_from_text(text)
    assert comp.title == "Unfenced"


def test_parser_repairs_common_llm_json_issues() -> None:
    text = """
```json
{
  "title": "Repaired",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "ppq": 480,
  "tracks": [
    {
      "events": [
        // comment
        {"type":"note","start":0,"duration":1,"pitch":"C4",},
      ],
    },
  ],
}
```
"""
    comp = parse_composition_from_text(text)
    assert comp.title == "Repaired"

