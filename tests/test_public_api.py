from __future__ import annotations


def test_public_api_exports_are_importable() -> None:
    from pianist import (
        Composition,
        composition_from_midi,
        composition_to_canonical_json,
        iteration_prompt_template,
        parse_composition_from_text,
        transpose_composition,
    )

    assert Composition is not None
    assert callable(parse_composition_from_text)
    assert callable(composition_from_midi)
    assert callable(composition_to_canonical_json)
    assert callable(iteration_prompt_template)
    assert callable(transpose_composition)
