from __future__ import annotations


def test_public_api_exports_are_importable() -> None:
    from pianist import Composition, parse_composition_from_text  # noqa: F401

    assert Composition is not None
    assert callable(parse_composition_from_text)

