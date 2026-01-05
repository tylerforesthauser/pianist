from dataclasses import dataclass, field
from typing import List

@dataclass
class Note:
    pitch: str  # Scientific pitch notation e.g., "C4", "F#3"
    duration: float  # In beats
    start_time: float  # In beats from the beginning of the track
    velocity: int = 80  # MIDI velocity (0-127)

@dataclass
class Track:
    name: str
    instrument: int  # General MIDI instrument number (0-127)
    notes: List[Note] = field(default_factory=list)

@dataclass
class Composition:
    title: str
    tempo: int  # BPM
    time_signature: str  # e.g., "4/4"
    tracks: List[Track] = field(default_factory=list)
