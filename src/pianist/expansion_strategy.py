"""
Expansion strategy generation for AI-assisted composition expansion.

This module generates detailed strategies for how AI should expand incomplete compositions,
including motif development techniques, phrase extension methods, and section expansion approaches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .musical_analysis import (
    MUSIC21_AVAILABLE,
    MusicalAnalysis,
    analyze_composition,
)

if TYPE_CHECKING:
    from .schema import Composition


@dataclass
class MotifDevelopment:
    """Strategy for developing a specific motif."""

    motif_id: str | None
    start: float
    duration: float
    pitches: list[int]
    techniques: list[str]  # e.g., ["sequence", "inversion", "augmentation"]
    description: str


@dataclass
class SectionExpansion:
    """Strategy for expanding a specific section."""

    section_name: str
    current_length: float
    target_length: float
    expansion_ratio: float
    techniques: list[str]  # e.g., ["phrase_extension", "new_material", "development"]
    description: str


@dataclass
class ExpansionStrategy:
    """Complete expansion strategy for a composition."""

    motif_developments: list[MotifDevelopment]
    section_expansions: list[SectionExpansion]
    transitions: list[str]  # Suggestions for transitions between sections
    preserve: list[str]  # What to preserve
    overall_approach: str  # High-level strategy description


def generate_expansion_strategy(
    composition: Composition, target_length: float, analysis: MusicalAnalysis | None = None
) -> ExpansionStrategy:
    """
    Generate a detailed expansion strategy for a composition.

    Args:
        composition: The composition to expand
        target_length: Target length in beats
        analysis: Optional pre-computed analysis (will compute if not provided)

    Returns:
        ExpansionStrategy object with detailed expansion guidance
    """
    if not MUSIC21_AVAILABLE:
        raise ImportError(
            "music21 is required for expansion strategy generation. Install it with: pip install music21"
        )

    # Get or compute analysis with pre-converted stream to avoid redundant conversion
    if analysis is None:
        from .musical_analysis import _composition_to_music21_stream

        music21_stream = _composition_to_music21_stream(composition)
        analysis = analyze_composition(composition, music21_stream=music21_stream)

    # Calculate current length
    current_length = 0.0
    for track in composition.tracks:
        for event in track.events:
            event_end = event.start + (getattr(event, "duration", 0.0))
            current_length = max(current_length, event_end)

    expansion_ratio = target_length / current_length if current_length > 0 else 1.0

    # Generate motif developments
    motif_developments: list[MotifDevelopment] = []
    for i, motif in enumerate(analysis.motifs):
        techniques = _suggest_motif_techniques(motif, expansion_ratio)
        motif_developments.append(
            MotifDevelopment(
                motif_id=f"motif_{i + 1}",
                start=motif.start,
                duration=motif.duration,
                pitches=motif.pitches,
                techniques=techniques,
                description=f"Develop motif at {motif.start:.1f}-{motif.start + motif.duration:.1f} beats using: {', '.join(techniques)}",
            )
        )

    # Generate section expansions
    section_expansions: list[SectionExpansion] = []

    # Check for explicit expansion points in musical_intent
    if composition.musical_intent and composition.musical_intent.expansion_points:
        for point in composition.musical_intent.expansion_points:
            section_ratio = (
                point.suggested_length / point.current_length if point.current_length > 0 else 1.0
            )
            techniques = _suggest_section_techniques(point, section_ratio)
            section_expansions.append(
                SectionExpansion(
                    section_name=point.section,
                    current_length=point.current_length,
                    target_length=point.suggested_length,
                    expansion_ratio=section_ratio,
                    techniques=techniques,
                    description=point.development_strategy
                    or f"Expand section {point.section} using: {', '.join(techniques)}",
                )
            )
    # Auto-generate section expansion if no explicit points
    # Divide expansion across detected phrases
    elif analysis.phrases:
        beats_per_phrase = current_length / len(analysis.phrases) if analysis.phrases else 4.0
        target_beats_per_phrase = (
            target_length / len(analysis.phrases)
            if analysis.phrases
            else beats_per_phrase * expansion_ratio
        )

        for i, phrase in enumerate(analysis.phrases):
            phrase_ratio = (
                target_beats_per_phrase / beats_per_phrase
                if beats_per_phrase > 0
                else expansion_ratio
            )
            techniques = _suggest_phrase_techniques(phrase, phrase_ratio)
            section_expansions.append(
                SectionExpansion(
                    section_name=f"phrase_{i + 1}",
                    current_length=phrase.duration,
                    target_length=phrase.duration * phrase_ratio,
                    expansion_ratio=phrase_ratio,
                    techniques=techniques,
                    description=f"Extend phrase at {phrase.start:.1f}-{phrase.start + phrase.duration:.1f} beats using: {', '.join(techniques)}",
                )
            )

    # Generate transition suggestions
    transitions = _suggest_transitions(composition, analysis, expansion_ratio)

    # Determine what to preserve
    preserve = _determine_preserve_list(composition, analysis)

    # Generate overall approach
    overall_approach = _generate_overall_approach(
        composition, analysis, current_length, target_length, expansion_ratio
    )

    return ExpansionStrategy(
        motif_developments=motif_developments,
        section_expansions=section_expansions,
        transitions=transitions,
        preserve=preserve,
        overall_approach=overall_approach,
    )


def _suggest_motif_techniques(motif: Any, expansion_ratio: float) -> list[str]:
    """Suggest development techniques for a motif."""
    techniques: list[str] = []

    # Basic techniques that work for most motifs
    if expansion_ratio > 1.5:
        techniques.append("sequence")  # Repeat motif at different pitch levels
        techniques.append("variation")  # Vary rhythm or intervals
    else:
        techniques.append("subtle_variation")  # Minor variations

    # Add more techniques based on motif characteristics
    if len(motif.pitches) >= 3:
        techniques.append("fragmentation")  # Break into smaller fragments
        techniques.append("inversion")  # Invert intervals

    if expansion_ratio > 2.0:
        techniques.append("augmentation")  # Lengthen note values
        techniques.append("diminution")  # Shorten note values

    return techniques[:3]  # Limit to top 3 techniques


def _suggest_section_techniques(expansion_point: Any, expansion_ratio: float) -> list[str]:
    """Suggest expansion techniques for a section."""
    techniques: list[str] = []

    if expansion_ratio > 1.5:
        techniques.append("phrase_extension")  # Extend existing phrases
        techniques.append("new_material")  # Add new complementary material
    else:
        techniques.append("subtle_extension")  # Minor extensions

    if expansion_ratio > 2.0:
        techniques.append("development")  # Develop existing ideas
        techniques.append("transitional_material")  # Add connecting material

    # Use strategy from expansion point if available
    if hasattr(expansion_point, "development_strategy") and expansion_point.development_strategy:
        # Extract key words from strategy
        strategy_lower = expansion_point.development_strategy.lower()
        if "develop" in strategy_lower:
            techniques.append("development")
        if "extend" in strategy_lower:
            techniques.append("phrase_extension")
        if "new" in strategy_lower or "add" in strategy_lower:
            techniques.append("new_material")

    return techniques[:3] if techniques else ["phrase_extension"]


def _suggest_phrase_techniques(_phrase: Any, expansion_ratio: float) -> list[str]:
    """Suggest extension techniques for a phrase."""
    techniques: list[str] = []

    if expansion_ratio > 1.3:
        techniques.append("phrase_extension")
        techniques.append("complementary_material")
    else:
        techniques.append("subtle_extension")

    if expansion_ratio > 1.8:
        techniques.append("cadential_extension")

    return techniques[:2] if techniques else ["phrase_extension"]


def _suggest_transitions(
    _composition: Composition, analysis: MusicalAnalysis, expansion_ratio: float
) -> list[str]:
    """Suggest how to create transitions between sections."""
    transitions: list[str] = []

    # Check form
    if analysis.form == "ternary":
        transitions.append("Create smooth transition from A to B section")
        transitions.append("Create return transition from B to A' section")
    elif analysis.form == "binary":
        transitions.append("Create connecting passage between A and B sections")

    # Check for multiple phrases
    if len(analysis.phrases) > 1:
        transitions.append("Add connecting material between phrases")

    # If significant expansion, suggest more transitions
    if expansion_ratio > 2.0:
        transitions.append("Add transitional passages to connect expanded sections")

    return transitions


def _determine_preserve_list(composition: Composition, analysis: MusicalAnalysis) -> list[str]:
    """Determine what should be preserved during expansion."""
    preserve: list[str] = []

    # Preserve key ideas from annotations
    if composition.musical_intent:
        if composition.musical_intent.preserve:
            preserve.extend(composition.musical_intent.preserve)

        # Preserve high-importance key ideas
        for idea in composition.musical_intent.key_ideas:
            if idea.importance == "high":
                preserve.append(f"key_idea:{idea.id}")

    # Preserve detected motifs
    if analysis.motifs:
        preserve.append(f"motifs ({len(analysis.motifs)} detected)")

    # Preserve harmonic character
    if analysis.harmonic_progression and analysis.harmonic_progression.key:
        preserve.append(f"key_signature:{analysis.harmonic_progression.key}")

    # Preserve form
    if analysis.form:
        preserve.append(f"form:{analysis.form}")

    return preserve


def _generate_overall_approach(
    composition: Composition,
    analysis: MusicalAnalysis,
    _current_length: float,
    _target_length: float,
    expansion_ratio: float,
) -> str:
    """Generate a high-level description of the expansion approach."""
    parts: list[str] = []

    # Overall strategy
    if expansion_ratio < 1.5:
        parts.append("Subtle expansion: extend phrases and add complementary material")
    elif expansion_ratio < 2.5:
        parts.append("Moderate expansion: develop motifs, extend phrases, and add new material")
    else:
        parts.append(
            "Significant expansion: develop motifs extensively, add new sections, and create transitions"
        )

    # Specific guidance based on analysis
    if analysis.motifs:
        parts.append(f"Focus on developing {len(analysis.motifs)} detected motif(s)")

    if analysis.phrases:
        parts.append(f"Extend {len(analysis.phrases)} detected phrase(s)")

    if analysis.harmonic_progression and analysis.harmonic_progression.chords:
        parts.append("Maintain harmonic coherence throughout")

    if composition.musical_intent and composition.musical_intent.development_direction:
        parts.append(
            f"Follow overall direction: {composition.musical_intent.development_direction}"
        )

    return ". ".join(parts) + "."


def suggest_motif_development(motif: Any, target_length: float) -> str:
    """
    Suggest how to develop a specific motif.

    Args:
        motif: Motif object from analysis
        target_length: Target length for the expanded composition

    Returns:
        String description of development strategy
    """
    expansion_ratio = (
        target_length / (motif.start + motif.duration)
        if (motif.start + motif.duration) > 0
        else 1.0
    )
    techniques = _suggest_motif_techniques(motif, expansion_ratio)

    return f"Develop motif at {motif.start:.1f}-{motif.start + motif.duration:.1f} beats using: {', '.join(techniques)}"


def suggest_phrase_extension(phrase: Any, target_length: float) -> str:
    """
    Suggest how to extend a phrase.

    Args:
        phrase: Phrase object from analysis
        target_length: Target length for the expanded composition

    Returns:
        String description of extension strategy
    """
    expansion_ratio = (
        target_length / (phrase.start + phrase.duration)
        if (phrase.start + phrase.duration) > 0
        else 1.0
    )
    techniques = _suggest_phrase_techniques(phrase, expansion_ratio)

    return f"Extend phrase at {phrase.start:.1f}-{phrase.start + phrase.duration:.1f} beats using: {', '.join(techniques)}"


def suggest_section_expansion(section: str, current_length: float, target_length: float) -> str:
    """
    Suggest how to expand a section.

    Args:
        section: Section name
        current_length: Current length in beats
        target_length: Target length in beats

    Returns:
        String description of expansion strategy
    """
    expansion_ratio = target_length / current_length if current_length > 0 else 1.0

    if expansion_ratio < 1.5:
        return f"Subtly expand section '{section}' by extending phrases and adding complementary material"
    elif expansion_ratio < 2.5:
        return f"Moderately expand section '{section}' by developing motifs, extending phrases, and adding new material"
    else:
        return f"Significantly expand section '{section}' by extensive development, new material, and transitions"
