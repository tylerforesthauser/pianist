# Schema Extensions Design: Musical Intent & Annotations

## Overview

Extend the `Composition` schema to support musical intent annotations that enable AI to understand:
- What are the "great ideas" (key motifs, phrases, harmonic progressions)
- Where should the composition expand
- How should motifs be developed
- What should be preserved vs. what can be changed

## Design Goals

1. **Backward Compatible**: Existing compositions without annotations should still work
2. **Optional**: Annotations should be optional, not required
3. **Clear Structure**: Easy for humans to mark and AI to understand
4. **Extensible**: Can add more annotation types in the future

## Proposed Schema Extensions

### 1. MusicalIntent Model

```python
class MusicalIntent(BaseModel):
    """
    Musical intent annotations for guiding AI expansion and development.
    
    This is optional - compositions without this field work as before.
    """
    key_ideas: list[KeyIdea] = Field(default_factory=list)
    expansion_points: list[ExpansionPoint] = Field(default_factory=list)
    preserve: list[str] = Field(default_factory=list)
    development_direction: str | None = None
```

### 2. KeyIdea Model

```python
class KeyIdea(BaseModel):
    """
    Marks an important musical idea that should be preserved and/or developed.
    
    Types:
    - "motif": Recurring melodic/rhythmic pattern
    - "phrase": Musical phrase
    - "harmonic_progression": Important chord progression
    - "rhythmic_pattern": Important rhythmic pattern
    """
    id: str  # Unique identifier (e.g., "motif_1", "opening_phrase")
    type: Literal["motif", "phrase", "harmonic_progression", "rhythmic_pattern"]
    start: float  # Start time in beats
    duration: float  # Duration in beats
    description: str  # Human-readable description
    importance: Literal["high", "medium", "low"] = "medium"
    development_direction: str | None = None  # How to develop (e.g., "expand and vary", "preserve exactly")
```

### 3. ExpansionPoint Model

```python
class ExpansionPoint(BaseModel):
    """
    Marks where and how the composition should be expanded.
    """
    section: str  # Section identifier (e.g., "A", "B", "exposition")
    current_length: float  # Current length in beats
    suggested_length: float  # Target length in beats
    development_strategy: str  # How to expand (e.g., "develop motif_1 with variations")
    preserve: list[str] = Field(default_factory=list)  # List of key_idea IDs to preserve
```

## Integration with Composition

### Option 1: Optional Field (Recommended)

Add `musical_intent` as an optional field to `Composition`:

```python
class Composition(BaseModel):
    # ... existing fields ...
    musical_intent: MusicalIntent | None = None
```

**Pros:**
- Fully backward compatible
- Clean separation
- Easy to check if present

**Cons:**
- None significant

### Option 2: Separate Annotation File

Keep annotations in a separate file that references the composition.

**Pros:**
- Keeps composition JSON clean
- Can have multiple annotation sets

**Cons:**
- More complex workflow
- Harder to keep in sync
- Not as integrated

**Decision: Option 1** - Add as optional field to Composition

## Example JSON

```json
{
  "title": "Incomplete Sketch",
  "bpm": 120,
  "time_signature": {"numerator": 4, "denominator": 4},
  "tracks": [...],
  "musical_intent": {
    "key_ideas": [
      {
        "id": "motif_1",
        "type": "motif",
        "start": 0,
        "duration": 4,
        "description": "Opening ascending motif",
        "importance": "high",
        "development_direction": "expand and vary"
      },
      {
        "id": "phrase_A",
        "type": "phrase",
        "start": 0,
        "duration": 16,
        "description": "Opening phrase with motif_1",
        "importance": "high",
        "development_direction": "preserve structure, develop content"
      }
    ],
    "expansion_points": [
      {
        "section": "A",
        "current_length": 32,
        "suggested_length": 120,
        "development_strategy": "develop motif_1 with variations and sequences",
        "preserve": ["motif_1", "phrase_A"]
      }
    ],
    "preserve": [
      "harmonic_progression_A",
      "opening_motif",
      "tempo_character"
    ],
    "development_direction": "Expand section A while preserving the opening motif and phrase structure"
  }
}
```

## Backward Compatibility

- Compositions without `musical_intent` field work exactly as before
- All existing validation passes
- All existing serialization works
- Renderer ignores `musical_intent` (doesn't affect MIDI output)

## Implementation Steps

1. Add models to `src/pianist/schema.py`
2. Add optional field to `Composition`
3. Update validation (should accept compositions with or without intent)
4. Update serialization (include intent if present)
5. Write tests for:
   - Compositions without intent (backward compatibility)
   - Compositions with intent
   - Validation of intent structure
6. Update documentation

## Open Questions

1. **Should key_ideas reference events by ID or by time range?**
   - Time range (current design) - simpler, but may drift if composition changes
   - Event ID - more precise, but requires event IDs
   - **Decision needed**

2. **How to handle overlapping key ideas?**
   - Allow overlaps
   - Validate no overlaps
   - **Decision needed**

3. **Should we support linking key_ideas to specific events?**
   - Could add `event_ids` or `event_references` field
   - **Decision needed**

4. **How detailed should development_direction be?**
   - Free-form text (current design) - flexible but less structured
   - Structured options (enum) - more constrained but clearer
   - **Decision needed**

## Next Steps

1. Review this design
2. Answer open questions
3. Finalize model structure
4. Implement in schema.py
5. Write tests
6. Update documentation

