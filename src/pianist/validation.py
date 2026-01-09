"""
Quality validation for expanded compositions.

This module validates that expansions are musically sound, preserve original ideas,
and meet quality standards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .musical_analysis import (
    MUSIC21_AVAILABLE,
    analyze_composition,
    analyze_harmony,
    detect_form,
    detect_motifs,
)

if TYPE_CHECKING:
    from .schema import Composition


@dataclass
class ValidationResult:
    """Results of expansion validation."""

    motifs_preserved: bool
    motifs_preserved_count: int
    motifs_total_count: int
    development_quality: float  # 0.0 to 1.0
    harmonic_coherence: float  # 0.0 to 1.0
    form_consistency: float  # 0.0 to 1.0
    overall_quality: float  # 0.0 to 1.0
    issues: list[str]  # List of validation issues
    warnings: list[str]  # List of validation warnings
    passed: bool  # Whether validation passed overall


def validate_expansion(
    original: Composition, expanded: Composition, target_length: float | None = None
) -> ValidationResult:
    """
    Validate that an expansion meets quality standards.

    Args:
        original: The original composition
        expanded: The expanded composition
        target_length: Optional target length in beats (for length validation)

    Returns:
        ValidationResult with quality scores and issues
    """
    if not MUSIC21_AVAILABLE:
        return ValidationResult(
            motifs_preserved=False,
            motifs_preserved_count=0,
            motifs_total_count=0,
            development_quality=0.0,
            harmonic_coherence=0.0,
            form_consistency=0.0,
            overall_quality=0.0,
            issues=["music21 is required for validation"],
            warnings=[],
            passed=False,
        )

    issues: list[str] = []
    warnings: list[str] = []

    # Check motif preservation
    motif_result = check_motif_preservation(original, expanded)
    motifs_preserved = motif_result["preserved"]
    motifs_preserved_count = motif_result["preserved_count"]
    motifs_total_count = motif_result["total_count"]

    if not motifs_preserved:
        if motifs_total_count > 0:
            issues.append(f"Only {motifs_preserved_count}/{motifs_total_count} motifs preserved")
        else:
            warnings.append("No motifs detected in original composition")

    # Assess development quality
    development_quality = assess_development_quality(expanded)
    if development_quality < 0.5:
        issues.append("Low development quality detected")
    elif development_quality < 0.7:
        warnings.append("Development quality could be improved")

    # Check harmonic coherence
    harmonic_coherence = check_harmonic_coherence(expanded)
    if harmonic_coherence < 0.6:
        issues.append("Harmonic coherence issues detected")
    elif harmonic_coherence < 0.8:
        warnings.append("Harmonic coherence could be improved")

    # Check form consistency
    form_consistency = check_form_consistency(expanded)
    if form_consistency < 0.7:
        warnings.append("Form consistency could be improved")

    # Check length if target provided
    if target_length is not None:
        expanded_length = _calculate_composition_length(expanded)
        if expanded_length < target_length * 0.9:
            issues.append(
                f"Expanded length ({expanded_length:.1f} beats) is significantly "
                f"shorter than target ({target_length:.1f} beats)"
            )
        elif expanded_length < target_length * 0.95:
            warnings.append(
                f"Expanded length ({expanded_length:.1f} beats) is slightly "
                f"shorter than target ({target_length:.1f} beats)"
            )
        elif expanded_length > target_length * 1.1:
            warnings.append(
                f"Expanded length ({expanded_length:.1f} beats) is significantly "
                f"longer than target ({target_length:.1f} beats)"
            )

    # Calculate overall quality (weighted average)
    overall_quality = (
        (motifs_preserved_count / max(motifs_total_count, 1)) * 0.3
        + development_quality * 0.3
        + harmonic_coherence * 0.2
        + form_consistency * 0.2
    )

    # Validation passes if no critical issues and overall quality >= 0.6
    passed = len(issues) == 0 and overall_quality >= 0.6

    return ValidationResult(
        motifs_preserved=motifs_preserved,
        motifs_preserved_count=motifs_preserved_count,
        motifs_total_count=motifs_total_count,
        development_quality=development_quality,
        harmonic_coherence=harmonic_coherence,
        form_consistency=form_consistency,
        overall_quality=overall_quality,
        issues=issues,
        warnings=warnings,
        passed=passed,
    )


def check_motif_preservation(original: Composition, expanded: Composition) -> dict[str, Any]:
    """
    Check if original motifs are preserved in the expansion.

    Returns:
        Dictionary with:
        - preserved: bool (True if all motifs preserved)
        - preserved_count: int
        - total_count: int
        - missing_motifs: list of motif descriptions
    """
    if not MUSIC21_AVAILABLE:
        return {
            "preserved": False,
            "preserved_count": 0,
            "total_count": 0,
            "missing_motifs": [],
        }

    # Detect motifs in original
    original_motifs = detect_motifs(original)

    if not original_motifs:
        return {
            "preserved": True,  # No motifs to preserve
            "preserved_count": 0,
            "total_count": 0,
            "missing_motifs": [],
        }

    # Detect motifs in expanded
    expanded_motifs = detect_motifs(expanded)

    # Check for key ideas in musical_intent
    preserved_count = 0
    missing_motifs: list[str] = []

    # Check each original motif
    for orig_motif in original_motifs:
        # Look for similar motif in expanded (simple pitch matching)
        found = False
        for exp_motif in expanded_motifs:
            # Check if pitches overlap significantly
            orig_pitches = set(orig_motif.pitches)
            exp_pitches = set(exp_motif.pitches)

            # If at least 50% of pitches match, consider it preserved
            if orig_pitches and exp_pitches:
                overlap = len(orig_pitches & exp_pitches) / len(orig_pitches)
                if overlap >= 0.5:
                    found = True
                    break

        if found:
            preserved_count += 1
        else:
            missing_motifs.append(
                f"Motif with pitches {orig_motif.pitches} at {orig_motif.start:.1f} beats"
            )

    # Also check musical_intent key_ideas if present
    if original.musical_intent:
        for key_idea in original.musical_intent.key_ideas:
            if key_idea.type == "motif" and key_idea.importance in ("high", "medium"):
                # Check if this idea is preserved in expanded
                # Simple check: look for similar timing and pitches
                found = False
                for exp_motif in expanded_motifs:
                    # Check timing overlap
                    if (
                        abs(exp_motif.start - key_idea.start) < 2.0
                        and abs(exp_motif.duration - key_idea.duration) < 1.0
                    ):
                        found = True
                        break

                if not found:
                    missing_motifs.append(f"Key idea '{key_idea.id}' not found")

    preserved = preserved_count == len(original_motifs) and len(missing_motifs) == 0

    return {
        "preserved": preserved,
        "preserved_count": preserved_count,
        "total_count": len(original_motifs),
        "missing_motifs": missing_motifs,
    }


def assess_development_quality(expanded: Composition) -> float:
    """
    Assess the quality of motif/phrase development.

    Returns:
        Quality score from 0.0 to 1.0
    """
    if not MUSIC21_AVAILABLE:
        return 0.0

    try:
        analysis = analyze_composition(expanded)

        # Factors that contribute to development quality:
        # 1. Presence of motifs (indicates development)
        # 2. Variety in motifs (indicates variation)
        # 3. Phrase structure (indicates musical coherence)
        # 4. Harmonic progression (indicates harmonic development)

        score = 0.0

        # Motif presence (0.3 weight)
        if analysis.motifs:
            # More motifs = better development (up to a point)
            motif_score = min(len(analysis.motifs) / 5.0, 1.0)
            score += motif_score * 0.3
        else:
            # No motifs might indicate lack of development
            score += 0.1 * 0.3

        # Motif variety (0.2 weight)
        if len(analysis.motifs) > 1:
            # Check for variety in motif pitches
            unique_pitch_sets = {tuple(sorted(m.pitches)) for m in analysis.motifs}
            variety_score = min(len(unique_pitch_sets) / len(analysis.motifs), 1.0)
            score += variety_score * 0.2
        else:
            score += 0.1 * 0.2

        # Phrase structure (0.3 weight)
        if analysis.phrases:
            # Multiple phrases indicate development
            phrase_score = min(len(analysis.phrases) / 4.0, 1.0)
            score += phrase_score * 0.3
        else:
            score += 0.1 * 0.3

        # Harmonic progression (0.2 weight)
        if analysis.harmonic_progression and analysis.harmonic_progression.chords:
            # More chords = more harmonic development
            chord_count = len(analysis.harmonic_progression.chords)
            harmonic_score = min(chord_count / 10.0, 1.0)
            score += harmonic_score * 0.2
        else:
            score += 0.1 * 0.2

        return min(score, 1.0)
    except Exception:
        # If analysis fails, return low score
        return 0.3


def check_harmonic_coherence(composition: Composition) -> float:
    """
    Check harmonic coherence of the composition.

    Returns:
        Coherence score from 0.0 to 1.0
    """
    if not MUSIC21_AVAILABLE:
        return 0.0

    try:
        harmony = analyze_harmony(composition)

        if not harmony or not harmony.chords:
            # No harmony detected - assume basic coherence
            return 0.5

        # Factors for harmonic coherence:
        # 1. Key consistency (if key is detected)
        # 2. Chord progression smoothness (basic check)
        # 3. Number of chords (more = better progression)

        score = 0.0

        # Key consistency (0.4 weight)
        if harmony.key:
            # If key is detected, assume some coherence
            score += 0.8 * 0.4
        else:
            # No key detected - might indicate issues
            score += 0.4 * 0.4

        # Chord progression (0.4 weight)
        if len(harmony.chords) >= 2:
            # Multiple chords indicate progression
            progression_score = min(len(harmony.chords) / 8.0, 1.0)
            score += progression_score * 0.4
        else:
            score += 0.3 * 0.4

        # Basic smoothness check (0.2 weight)
        # Check if chords change frequently (indicates movement)
        if len(harmony.chords) > 1:
            # Simple heuristic: more chord changes = more movement = better
            score += 0.7 * 0.2
        else:
            score += 0.3 * 0.2

        return min(score, 1.0)
    except Exception:
        return 0.4


def check_form_consistency(composition: Composition) -> float:
    """
    Check form consistency of the composition.

    Returns:
        Consistency score from 0.0 to 1.0
    """
    if not MUSIC21_AVAILABLE:
        return 0.0

    try:
        form = detect_form(composition)

        # If form is detected, assume consistency
        if form:
            return 0.8

        # Check for section markers
        has_sections = False
        for track in composition.tracks:
            for event in track.events:
                if hasattr(event, "type") and event.type == "section":
                    has_sections = True
                    break
            if has_sections:
                break

        if has_sections:
            return 0.7

        # No form detected - might be through-composed or simple
        # Assume moderate consistency
        return 0.6
    except Exception:
        return 0.5


def _calculate_composition_length(composition: Composition) -> float:
    """Calculate the total length of a composition in beats."""
    length = 0.0
    for track in composition.tracks:
        for event in track.events:
            event_end = event.start + (getattr(event, "duration", 0.0))
            length = max(length, event_end)
    return length
