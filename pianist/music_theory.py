"""
Music theory primitives for representing notes, scales, chords, and other musical elements.
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class NoteName(Enum):
    """Musical note names."""
    C = 0
    C_SHARP = 1
    D_FLAT = 1
    D = 2
    D_SHARP = 3
    E_FLAT = 3
    E = 4
    F = 5
    F_SHARP = 6
    G_FLAT = 6
    G = 7
    G_SHARP = 8
    A_FLAT = 8
    A = 9
    A_SHARP = 10
    B_FLAT = 10
    B = 11


@dataclass
class Note:
    """Represents a musical note with pitch, duration, and velocity."""
    
    pitch: int  # MIDI pitch number (0-127), where C4 = 60
    duration: float  # Duration in beats
    velocity: int = 64  # MIDI velocity (0-127), defaults to mezzo-forte
    
    def __post_init__(self):
        if not 0 <= self.pitch <= 127:
            raise ValueError(f"Pitch must be between 0 and 127, got {self.pitch}")
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")
        if not 0 <= self.velocity <= 127:
            raise ValueError(f"Velocity must be between 0 and 127, got {self.velocity}")
    
    @classmethod
    def from_name(cls, name: str, octave: int, duration: float = 1.0, velocity: int = 64) -> 'Note':
        """Create a Note from note name (e.g., 'C', 'C#', 'Db') and octave."""
        # Normalize note name: replace Unicode symbols and convert to uppercase
        name = name.replace('♯', '#').replace('♭', 'b').upper()
        
        # Map note names to semitones
        note_map = {
            'C': 0, 'C#': 1, 'DB': 1,
            'D': 2, 'D#': 3, 'EB': 3,
            'E': 4,
            'F': 5, 'F#': 6, 'GB': 6,
            'G': 7, 'G#': 8, 'AB': 8,
            'A': 9, 'A#': 10, 'BB': 10,
            'B': 11
        }
        
        if name not in note_map:
            raise ValueError(f"Invalid note name: {name}")
        
        # Calculate MIDI pitch: (octave + 1) * 12 + semitone
        # C4 = 60, C0 = 12
        pitch = (octave + 1) * 12 + note_map[name]
        
        return cls(pitch=pitch, duration=duration, velocity=velocity)


class ScaleType(Enum):
    """Common scale types."""
    MAJOR = [0, 2, 4, 5, 7, 9, 11]  # W-W-H-W-W-W-H
    NATURAL_MINOR = [0, 2, 3, 5, 7, 8, 10]  # W-H-W-W-H-W-W
    HARMONIC_MINOR = [0, 2, 3, 5, 7, 8, 11]
    MELODIC_MINOR = [0, 2, 3, 5, 7, 9, 11]
    DORIAN = [0, 2, 3, 5, 7, 9, 10]
    PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]
    LYDIAN = [0, 2, 4, 6, 7, 9, 11]
    MIXOLYDIAN = [0, 2, 4, 5, 7, 9, 10]
    AEOLIAN = [0, 2, 3, 5, 7, 8, 10]  # Same as natural minor
    LOCRIAN = [0, 1, 3, 5, 6, 8, 10]
    PENTATONIC_MAJOR = [0, 2, 4, 7, 9]
    PENTATONIC_MINOR = [0, 3, 5, 7, 10]
    BLUES = [0, 3, 5, 6, 7, 10]
    CHROMATIC = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


@dataclass
class Scale:
    """Represents a musical scale."""
    
    root: int  # MIDI pitch of the root note
    scale_type: ScaleType = ScaleType.MAJOR
    
    def get_notes(self, octaves: int = 1) -> List[int]:
        """Get all pitches in the scale for the specified number of octaves."""
        intervals = self.scale_type.value
        notes = []
        
        for octave in range(octaves):
            for interval in intervals:
                notes.append(self.root + octave * 12 + interval)
        
        # Add the root note of the next octave to complete the scale
        notes.append(self.root + octaves * 12)
        
        return notes
    
    def get_degree(self, degree: int) -> int:
        """Get the pitch of a specific scale degree (1-indexed)."""
        intervals = self.scale_type.value
        if degree < 1 or degree > len(intervals):
            raise ValueError(f"Degree must be between 1 and {len(intervals)}")
        
        return self.root + intervals[degree - 1]


class ChordType(Enum):
    """Common chord types with their interval structures."""
    MAJOR = [0, 4, 7]  # Root, major third, perfect fifth
    MINOR = [0, 3, 7]  # Root, minor third, perfect fifth
    DIMINISHED = [0, 3, 6]  # Root, minor third, diminished fifth
    AUGMENTED = [0, 4, 8]  # Root, major third, augmented fifth
    MAJOR_SEVENTH = [0, 4, 7, 11]  # Major triad + major seventh
    MINOR_SEVENTH = [0, 3, 7, 10]  # Minor triad + minor seventh
    DOMINANT_SEVENTH = [0, 4, 7, 10]  # Major triad + minor seventh
    DIMINISHED_SEVENTH = [0, 3, 6, 9]  # Diminished triad + diminished seventh
    HALF_DIMINISHED = [0, 3, 6, 10]  # Diminished triad + minor seventh
    MAJOR_SIXTH = [0, 4, 7, 9]  # Major triad + major sixth
    MINOR_SIXTH = [0, 3, 7, 9]  # Minor triad + major sixth
    SUSPENDED_SECOND = [0, 2, 7]  # Root, major second, perfect fifth
    SUSPENDED_FOURTH = [0, 5, 7]  # Root, perfect fourth, perfect fifth


@dataclass
class Chord:
    """Represents a musical chord."""
    
    root: int  # MIDI pitch of the root note
    chord_type: ChordType = ChordType.MAJOR
    inversion: int = 0  # 0 = root position, 1 = first inversion, etc.
    
    def get_notes(self) -> List[int]:
        """Get all pitches in the chord."""
        intervals = self.chord_type.value
        notes = [self.root + interval for interval in intervals]
        
        # Apply inversion
        for _ in range(self.inversion):
            notes.append(notes.pop(0) + 12)
        
        return notes


@dataclass
class TimeSignature:
    """Represents a time signature."""
    
    numerator: int = 4  # Number of beats per measure
    denominator: int = 4  # Note value that gets one beat
    
    def __post_init__(self):
        if self.numerator <= 0:
            raise ValueError("Time signature numerator must be positive")
        if self.denominator not in [1, 2, 4, 8, 16, 32]:
            raise ValueError("Time signature denominator must be a power of 2")
    
    def beats_per_measure(self) -> int:
        """Get the number of beats per measure."""
        return self.numerator


@dataclass
class Tempo:
    """Represents tempo in beats per minute."""
    
    bpm: int = 120  # Beats per minute
    
    def __post_init__(self):
        if self.bpm <= 0:
            raise ValueError("Tempo must be positive")


class Dynamics(Enum):
    """Common dynamic markings."""
    PIANISSIMO = 32  # pp - very soft
    PIANO = 48  # p - soft
    MEZZO_PIANO = 64  # mp - moderately soft
    MEZZO_FORTE = 80  # mf - moderately loud
    FORTE = 96  # f - loud
    FORTISSIMO = 112  # ff - very loud
