from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from .notes import note_name_to_midi


Beat = Annotated[float, Field(ge=0)]
Hand = Literal["lh", "rh"]
Voice = Annotated[int, Field(ge=1, le=4)]


class TimeSignature(BaseModel):
    numerator: int = Field(ge=1, le=32)
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
    """

    pitches: list[int | str]
    hand: Hand
    voice: Voice | None = None

    @field_validator("pitches")
    @classmethod
    def _coerce_pitches(cls, v: list[int | str]) -> list[int]:
        out = [_coerce_pitch_to_midi(p) for p in v]
        if not out:
            raise ValueError("pitches must not be empty.")
        return out


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
                data["pitches"] = None
                return data
            if not notes:
                raise ValueError("'notes' must not be empty.")

            # Normalize to the internal `pitches` list for rendering convenience.
            # This runs before Pydantic parses nested models, so items may be dicts.
            data["pitches"] = [
                (n.get("pitch") if isinstance(n, dict) else getattr(n, "pitch", None))
                for n in notes
            ]
        elif groups is not None:
            if not isinstance(groups, list):
                data["pitches"] = None
                return data
            if not groups:
                raise ValueError("'groups' must not be empty.")

            flattened: list[int | str] = []
            for g in groups:
                if isinstance(g, dict):
                    flattened.extend(g.get("pitches") or [])
                else:
                    flattened.extend(getattr(g, "pitches", []) or [])
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
    Sustain pedal (CC 64) event. `value` defaults to 127.
    """

    type: Literal["pedal"] = "pedal"
    start: Beat
    duration: Annotated[float, Field(gt=0)]
    value: int = Field(default=127, ge=0, le=127)

    # Optional annotation fields
    section: str | None = None
    phrase: str | None = None


Event = Annotated[NoteEvent | PedalEvent, Field(discriminator="type")]


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

