"""
Annotation utilities for marking musical intent.
"""

from __future__ import annotations

from .schema import Composition, ExpansionPoint, KeyIdea, MusicalIntent


def add_key_idea(
    comp: Composition,
    idea_id: str,
    idea_type: str,
    start: float,
    duration: float,
    description: str,
    importance: str = "medium",
    development_direction: str | None = None,
) -> Composition:
    """
    Add a key idea annotation to a composition.

    Returns a new Composition with the annotation added.
    """
    # Get or create musical intent
    if comp.musical_intent is None:
        intent = MusicalIntent()
    else:
        # Create a copy to avoid mutating the original
        intent = MusicalIntent(
            key_ideas=list(comp.musical_intent.key_ideas),
            expansion_points=list(comp.musical_intent.expansion_points),
            preserve=list(comp.musical_intent.preserve),
            development_direction=comp.musical_intent.development_direction,
        )

    # Check if idea ID already exists
    existing_ids = {idea.id for idea in intent.key_ideas}
    if idea_id in existing_ids:
        raise ValueError(f"Key idea with ID '{idea_id}' already exists.")

    # Add new key idea
    new_idea = KeyIdea(
        id=idea_id,
        type=idea_type,  # type: ignore
        start=start,
        duration=duration,
        description=description,
        importance=importance,  # type: ignore
        development_direction=development_direction,
    )
    intent.key_ideas.append(new_idea)

    # Create new composition with updated intent
    comp_dict = comp.model_dump()
    comp_dict["musical_intent"] = intent.model_dump()
    return Composition.model_validate(comp_dict)


def add_expansion_point(
    comp: Composition,
    section: str,
    current_length: float,
    suggested_length: float,
    development_strategy: str,
    preserve: list[str] | None = None,
) -> Composition:
    """
    Add an expansion point annotation to a composition.

    Returns a new Composition with the annotation added.
    """
    # Get or create musical intent
    if comp.musical_intent is None:
        intent = MusicalIntent()
    else:
        # Create a copy
        intent = MusicalIntent(
            key_ideas=list(comp.musical_intent.key_ideas),
            expansion_points=list(comp.musical_intent.expansion_points),
            preserve=list(comp.musical_intent.preserve),
            development_direction=comp.musical_intent.development_direction,
        )

    # Add new expansion point
    new_point = ExpansionPoint(
        section=section,
        current_length=current_length,
        suggested_length=suggested_length,
        development_strategy=development_strategy,
        preserve=preserve or [],
    )
    intent.expansion_points.append(new_point)

    # Create new composition with updated intent
    comp_dict = comp.model_dump()
    comp_dict["musical_intent"] = intent.model_dump()
    return Composition.model_validate(comp_dict)


def set_development_direction(comp: Composition, direction: str) -> Composition:
    """
    Set the overall development direction for a composition.

    Returns a new Composition with the direction set.
    """
    # Get or create musical intent
    if comp.musical_intent is None:
        intent = MusicalIntent(development_direction=direction)
    else:
        intent = MusicalIntent(
            key_ideas=list(comp.musical_intent.key_ideas),
            expansion_points=list(comp.musical_intent.expansion_points),
            preserve=list(comp.musical_intent.preserve),
            development_direction=direction,
        )

    # Create new composition with updated intent
    comp_dict = comp.model_dump()
    comp_dict["musical_intent"] = intent.model_dump()
    return Composition.model_validate(comp_dict)


def add_to_preserve_list(comp: Composition, items: list[str]) -> Composition:
    """
    Add items to the preserve list.

    Returns a new Composition with the items added.
    """
    # Get or create musical intent
    if comp.musical_intent is None:
        intent = MusicalIntent(preserve=items)
    else:
        # Merge with existing preserve list
        existing = set(comp.musical_intent.preserve)
        new_items = existing.union(items)
        intent = MusicalIntent(
            key_ideas=list(comp.musical_intent.key_ideas),
            expansion_points=list(comp.musical_intent.expansion_points),
            preserve=list(new_items),
            development_direction=comp.musical_intent.development_direction,
        )

    # Create new composition with updated intent
    comp_dict = comp.model_dump()
    comp_dict["musical_intent"] = intent.model_dump()
    return Composition.model_validate(comp_dict)
