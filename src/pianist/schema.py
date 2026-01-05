from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from .notes import note_name_to_midi


Beat = Annotated[float, Field(ge=0)]


class TimeSignature(BaseModel):
    numerator: int = Field(ge=1, le=32)
    denominator: Literal[1, 2, 4, 8, 16, 32] = 4


class NoteEvent(BaseModel):
    """
    A note or chord that starts at `start` (in beats) and lasts `duration` (in beats).

    - Use `pitches` for chords, e.g. ["C4", "E4", "G4"].
    - Velocity defaults to a moderate piano dynamic.
    """

    type: Literal["note"] = "note"
    start: Beat
    duration: Annotated[float, Field(gt=0)]

    # Accept either `pitch` (single) or `pitches` (chord).
    pitch: int | str | None = None
    pitches: list[int | str] | None = None

    velocity: int = Field(default=80, ge=1, le=127)

    # Optional annotation fields (do not affect rendering).
    hand: Literal["lh", "rh"] | None = None
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
        if pitch is None and pitches is None:
            raise ValueError("Either 'pitch' or 'pitches' must be provided.")
        if pitch is not None and pitches is not None:
            raise ValueError("Provide either 'pitch' or 'pitches', not both.")
        if pitch is not None:
            data = dict(data)
            data["pitches"] = [pitch]
            data.pop("pitch", None)
        return data

    @field_validator("pitches")
    @classmethod
    def _coerce_pitches(cls, v: list[int | str] | None) -> list[int]:
        if v is None:
            raise ValueError("Missing pitch information.")
        out: list[int] = []
        for p in v:
            if isinstance(p, int):
                midi = p
            elif isinstance(p, str):
                midi = note_name_to_midi(p)
            else:
                raise TypeError(f"Invalid pitch type: {type(p)}")
            if not 0 <= midi <= 127:
                raise ValueError(f"Pitch out of range: {midi}")
            out.append(midi)
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
    bpm: Annotated[float, Field(gt=1, lt=400)] = 120.0
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

