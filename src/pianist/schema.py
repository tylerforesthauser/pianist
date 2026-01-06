from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from .notes import note_name_to_midi


Beat = Annotated[float, Field(ge=0)]
Hand = Literal["lh", "rh"]
Voice = Annotated[int, Field(ge=1, le=4)]


class TimeSignature(BaseModel):
    numerator: int = Field(default=4, ge=1, le=32)
    denominator: Literal[1, 2, 4, 8, 16, 32] = 4


def _coerce_pitch_to_midi(p: int | str) -> int:
    if isinstance(p, int):
        midi = p
    elif isinstance(p, str):
        midi = note_name_to_midi(p)
    else:
        raise TypeError(f"Invalid pitch type: {type(p)}")
    if not 0 <= midi <= 127:
        raise ValueError(f"Pitch out of range: {midi}")
    return midi


class LabeledNote(BaseModel):
    """
    A single note with explicit hand/voice labels.

    This is an annotation structure; rendering only uses MIDI pitches + timing.
    """

    pitch: int | str
    hand: Hand
    voice: Voice | None = None

    @field_validator("pitch")
    @classmethod
    def _coerce_pitch(cls, v: int | str) -> int:
        return _coerce_pitch_to_midi(v)


class NoteGroup(BaseModel):
    """
    A sub-chord within a NoteEvent: multiple pitches sharing the same hand/voice.
    
    Supports both "pitches" (plural, list) and "pitch" (singular, single value).
    """

    # Support both pitch (singular) and pitches (plural)
    pitch: int | str | None = None
    pitches: list[int | str] | None = None
    hand: Hand
    voice: Voice | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_pitch_field(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        # If "pitch" is provided, convert it to "pitches" list
        if "pitch" in data and "pitches" not in data:
            data = dict(data)
            data["pitches"] = [data["pitch"]]
            data.pop("pitch", None)
        elif "pitch" in data and "pitches" in data:
            # Both present - prefer pitches, but this shouldn't happen in practice
            data = dict(data)
            data.pop("pitch", None)
        
        return data

    @field_validator("pitches")
    @classmethod
    def _coerce_pitches(cls, v: list[int | str] | None) -> list[int]:
        if v is None:
            raise ValueError("Either 'pitch' or 'pitches' must be provided.")
        out = [_coerce_pitch_to_midi(p) for p in v]
        if not out:
            raise ValueError("pitches must not be empty.")
        return out

    @model_validator(mode="after")
    def _ensure_pitches_present(self) -> "NoteGroup":
        if self.pitches is None:
            raise ValueError("Either 'pitch' or 'pitches' must be provided.")
        return self


class NoteEvent(BaseModel):
    """
    A note or chord that starts at `start` (in beats) and lasts `duration` (in beats).

    Provide pitch content in exactly ONE of these forms:
    - Legacy: `pitch` (single) or `pitches` (chord)
    - New (preferred): `notes` (per-note hand/voice labels)
    - New (preferred): `groups` (per-sub-chord hand/voice labels)

    - Velocity defaults to a moderate piano dynamic.
    """

    type: Literal["note"] = "note"
    start: Beat
    duration: Annotated[float, Field(gt=0)]

    # Legacy pitch fields.
    pitch: int | str | None = None
    pitches: list[int | str] | None = None

    # Preferred labeled representations.
    notes: list[LabeledNote] | None = None
    groups: list[NoteGroup] | None = None

    velocity: int = Field(default=80, ge=1, le=127)

    # Optional annotation fields (do not affect rendering).
    # NOTE: `hand` here is legacy and applies to the whole event. Prefer `notes`/`groups`.
    hand: Hand | None = None
    motif: str | None = None
    section: str | None = None
    phrase: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_pitch_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        pitch = data.get("pitch")
        pitches = data.get("pitches")
        notes = data.get("notes")
        groups = data.get("groups")

        has_legacy = pitch is not None or pitches is not None
        has_notes = notes is not None
        has_groups = groups is not None

        if not (has_legacy or has_notes or has_groups):
            raise ValueError(
                "One of 'pitch', 'pitches', 'notes', or 'groups' must be provided."
            )

        if sum([has_legacy, has_notes, has_groups]) > 1:
            raise ValueError(
                "Provide only one of legacy 'pitch'/'pitches', 'notes', or 'groups'."
            )

        if pitch is not None and pitches is not None:
            raise ValueError("Provide either 'pitch' or 'pitches', not both.")

        data = dict(data)
        if pitch is not None:
            data["pitches"] = [pitch]
            data.pop("pitch", None)
        elif notes is not None:
            if not isinstance(notes, list):
                raise ValueError("Field 'notes' must be a list.")
            if not notes:
                raise ValueError("'notes' must not be empty.")

            # Normalize to the internal `pitches` list for rendering convenience.
            # This runs before Pydantic parses nested models, so items may be dicts.
            pitches_from_notes: list[int | str] = []
            for idx, n in enumerate(notes):
                if isinstance(n, dict):
                    if "pitch" not in n:
                        raise ValueError(
                            f"Note at index {idx} is missing required 'pitch' field."
                        )
                    pitch_value = n.get("pitch")
                else:
                    if not hasattr(n, "pitch"):
                        raise ValueError(
                            f"Note at index {idx} is missing required 'pitch' attribute."
                        )
                    pitch_value = getattr(n, "pitch")

                if pitch_value is None:
                    raise ValueError(
                        f"Note at index {idx} has 'pitch' set to None; a pitch value is required."
                    )
                pitches_from_notes.append(pitch_value)

            data["pitches"] = pitches_from_notes
        elif groups is not None:
            if not isinstance(groups, list):
                raise ValueError("Field 'groups' must be a list.")
            if not groups:
                raise ValueError("'groups' must not be empty.")

            flattened: list[int | str] = []
            for idx, g in enumerate(groups):
                if isinstance(g, dict):
                    # Support both "pitches" (plural) and "pitch" (singular) for groups
                    if "pitches" in g:
                        group_pitches = g.get("pitches")
                    elif "pitch" in g:
                        # Convert singular "pitch" to list format
                        group_pitches = [g.get("pitch")]
                    else:
                        raise ValueError(
                            f"Group at index {idx} is missing required 'pitches' or 'pitch' field."
                        )
                else:
                    # For non-dict objects, check for both attributes
                    if hasattr(g, "pitches"):
                        group_pitches = getattr(g, "pitches")
                    elif hasattr(g, "pitch"):
                        # Convert singular "pitch" to list format
                        group_pitches = [getattr(g, "pitch")]
                    else:
                        raise ValueError(
                            f"Group at index {idx} is missing required 'pitches' or 'pitch' attribute."
                        )

                if group_pitches is None:
                    raise ValueError(
                        f"Group at index {idx} has 'pitches'/'pitch' set to None; pitches are required."
                    )
                if not isinstance(group_pitches, list):
                    raise ValueError(
                        f"Group at index {idx} has invalid 'pitches' type {type(group_pitches)}; expected a list."
                    )
                flattened.extend(group_pitches)
            data["pitches"] = flattened

        return data

    @model_validator(mode="after")
    def _disallow_legacy_hand_with_labeled_pitch_structures(self) -> "NoteEvent":
        if self.hand is not None and (self.notes is not None or self.groups is not None):
            raise ValueError(
                "When using 'notes' or 'groups', omit event-level 'hand' "
                "and label hand per note/group."
            )
        return self

    @field_validator("pitches")
    @classmethod
    def _coerce_pitches(cls, v: list[int | str] | None) -> list[int]:
        if v is None:
            raise ValueError("Missing pitch information.")
        out = [_coerce_pitch_to_midi(p) for p in v]
        if not out:
            raise ValueError("pitches must not be empty.")
        return out


class PedalEvent(BaseModel):
    """
    Sustain pedal (CC 64) event.
    
    For sustained pedaling (most common case):
    - Set `duration` > 0 to specify how long the pedal should be held down
    - The renderer will automatically create a press at `start` and release at `start+duration`
    - Example: {"type": "pedal", "start": 0, "duration": 4, "value": 127}
      This holds the pedal down for 4 beats, then releases it automatically.
    
    For instant press/release (rare, advanced use):
    - Set `duration` = 0 for a single control_change message
    - Use value=127 for instant press, value=0 for instant release
    - You must manually manage press-release pairs with separate events
    - Example: {"type": "pedal", "start": 0, "duration": 0, "value": 127}
      This sends a single press message (no automatic release).
    
    Default value is 127 (full pedal down).
    """

    type: Literal["pedal"] = "pedal"
    start: Beat
    duration: Annotated[float, Field(ge=0)]
    value: int = Field(default=127, ge=0, le=127)

    # Optional annotation fields
    section: str | None = None
    phrase: str | None = None

    @model_validator(mode="after")
    def _warn_duration_zero(self) -> "PedalEvent":
        """
        Warn when duration=0 is used with value=127, as this is likely a mistake.
        Most pedaling should use duration>0 for automatic press-release pairs.
        """
        if self.duration == 0 and self.value == 127:
            import warnings
            # stacklevel=3 attempts to point to user code that created the PedalEvent.
            # The call stack typically is: user code -> validate_composition_dict -> 
            # Pydantic validation -> this validator. stacklevel=3 should point to the
            # validate_composition_dict call or the user code that called it.
            # This is approximate and may vary based on call stack depth.
            warnings.warn(
                f"PedalEvent at start={self.start} has duration=0 with value=127. "
                "This creates an instant press with no automatic release. "
                "For sustained pedaling, use duration>0 instead. "
                "The renderer will automatically create a press at start and release at start+duration.",
                UserWarning,
                stacklevel=3
            )
        return self


class TempoEvent(BaseModel):
    """
    Tempo change event. Supports both instant and gradual tempo changes.

    For instant tempo changes:
    - Provide `bpm` (the new tempo at `start`)

    For gradual tempo changes (ritardando/accelerando):
    - Provide `start_bpm` and `end_bpm` (tempo at start and end of the change)
    - Provide `duration` (how long the change takes in beats)
    - The system will approximate the gradual change with discrete tempo steps

    Note: Tempo events can be placed in any track; they will be collected and
    rendered in the conductor track during MIDI generation.
    """

    type: Literal["tempo"] = "tempo"
    start: Beat

    # Instant tempo change: provide bpm only
    bpm: Annotated[float, Field(ge=20, lt=400)] | None = None

    # Gradual tempo change: provide start_bpm, end_bpm, and duration
    start_bpm: Annotated[float, Field(ge=20, lt=400)] | None = None
    end_bpm: Annotated[float, Field(ge=20, lt=400)] | None = None
    duration: Annotated[float, Field(gt=0)] | None = None

    # Optional annotation fields
    section: str | None = None
    phrase: str | None = None

    @model_validator(mode="after")
    def _validate_tempo_fields(self) -> "TempoEvent":
        has_instant = self.bpm is not None
        has_gradual = (
            self.start_bpm is not None
            or self.end_bpm is not None
            or self.duration is not None
        )

        if not has_instant and not has_gradual:
            raise ValueError(
                "TempoEvent must specify either 'bpm' (instant change) or "
                "'start_bpm'/'end_bpm'/'duration' (gradual change)."
            )

        if has_instant and has_gradual:
            raise ValueError(
                "TempoEvent cannot specify both instant ('bpm') and gradual "
                "('start_bpm'/'end_bpm'/'duration') tempo changes."
            )

        if has_gradual:
            if self.start_bpm is None:
                raise ValueError("Gradual tempo change requires 'start_bpm'.")
            if self.end_bpm is None:
                raise ValueError("Gradual tempo change requires 'end_bpm'.")
            if self.duration is None:
                raise ValueError("Gradual tempo change requires 'duration'.")

        return self


class SectionEvent(BaseModel):
    """
    Section marker event for metadata/annotation purposes.
    
    These events are ignored during MIDI rendering but can be used to
    organize and label sections of a composition.
    """

    type: Literal["section"] = "section"
    start: Beat
    label: str

    # Optional annotation fields
    phrase: str | None = None


Event = Annotated[
    NoteEvent | PedalEvent | TempoEvent | SectionEvent, Field(discriminator="type")
]


class Track(BaseModel):
    name: str = "Piano"
    channel: int = Field(default=0, ge=0, le=15)
    program: int = Field(default=0, ge=0, le=127)  # 0 = Acoustic Grand Piano
    events: list[Event] = Field(default_factory=list)


class Composition(BaseModel):
    """
    Top-level spec that an AI model should emit as JSON.

    Time units:
    - start/duration are in beats (quarter note == 1 beat for denominator=4).
    - For other denominators, "beat" still means a quarter note beat for simplicity.
      (This keeps time math predictable for models.)
    """

    title: str = "Untitled"
    bpm: Annotated[float, Field(ge=20, lt=400)] = 120.0
    time_signature: TimeSignature = Field(default_factory=TimeSignature)
    key_signature: str | None = None
    ppq: int = Field(default=480, ge=24, le=9600)
    tracks: list[Track] = Field(default_factory=lambda: [Track()])

    @field_validator("tracks")
    @classmethod
    def _ensure_tracks_present(cls, v: list[Track]) -> list[Track]:
        if not v:
            raise ValueError("At least one track is required.")
        return v


def validate_composition_dict(data: dict[str, Any]) -> Composition:
    try:
        return Composition.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Invalid composition schema: {e}") from e

