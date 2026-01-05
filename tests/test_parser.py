from __future__ import annotations

import pytest

from pianist.parser import parse_composition_from_text


def test_parser_accepts_fenced_json() -> None:
    text = """here you go

```json
{ "title": "x", "bpm": 120, "time_signature": {"numerator": 4, "denominator": 4}, "tracks": [{"events": []}] }
```
"""
    comp = parse_composition_from_text(text)
    assert comp.title == "x"


def test_parser_errors_without_json() -> None:
    with pytest.raises(ValueError):
        parse_composition_from_text("no braces here")

