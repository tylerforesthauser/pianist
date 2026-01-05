"""
Musical composition structures including motifs, phrases, sections, and full compositions.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from .music_theory import Note, TimeSignature, Tempo


@dataclass
class Motif:
    """
    A motif is a short musical idea or pattern that can be developed throughout a composition.
    It's the smallest structural unit that has musical significance.
    """
    
    notes: List[Note]
    name: Optional[str] = None
    
    def __post_init__(self):
        if not self.notes:
            raise ValueError("Motif must contain at least one note")
    
    def transpose(self, semitones: int) -> 'Motif':
        """Transpose the motif by a given number of semitones."""
        transposed_notes = [
            Note(
                pitch=note.pitch + semitones,
                duration=note.duration,
                velocity=note.velocity
            )
            for note in self.notes
        ]
        return Motif(notes=transposed_notes, name=self.name)
    
    def augment(self, factor: float = 2.0) -> 'Motif':
        """Augment the motif by increasing note durations."""
        augmented_notes = [
            Note(
                pitch=note.pitch,
                duration=note.duration * factor,
                velocity=note.velocity
            )
            for note in self.notes
        ]
        return Motif(notes=augmented_notes, name=self.name)
    
    def diminish(self, factor: float = 2.0) -> 'Motif':
        """Diminish the motif by decreasing note durations."""
        diminished_notes = [
            Note(
                pitch=note.pitch,
                duration=note.duration / factor,
                velocity=note.velocity
            )
            for note in self.notes
        ]
        return Motif(notes=diminished_notes, name=self.name)
    
    def invert(self, axis: Optional[int] = None) -> 'Motif':
        """Invert the motif melodically around an axis pitch."""
        if axis is None:
            axis = self.notes[0].pitch
        
        inverted_notes = [
            Note(
                pitch=axis - (note.pitch - axis),
                duration=note.duration,
                velocity=note.velocity
            )
            for note in self.notes
        ]
        return Motif(notes=inverted_notes, name=self.name)
    
    def retrograde(self) -> 'Motif':
        """Reverse the motif (play it backwards)."""
        return Motif(notes=list(reversed(self.notes)), name=self.name)
    
    def total_duration(self) -> float:
        """Get the total duration of the motif in beats."""
        return sum(note.duration for note in self.notes)


@dataclass
class Phrase:
    """
    A phrase is a musical sentence, typically consisting of multiple motifs or a complete musical thought.
    """
    
    motifs: List[Motif]
    name: Optional[str] = None
    
    def __post_init__(self):
        if not self.motifs:
            raise ValueError("Phrase must contain at least one motif")
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes in the phrase."""
        notes = []
        for motif in self.motifs:
            notes.extend(motif.notes)
        return notes
    
    def total_duration(self) -> float:
        """Get the total duration of the phrase in beats."""
        return sum(motif.total_duration() for motif in self.motifs)


@dataclass
class Section:
    """
    A section is a large structural component of a composition (e.g., exposition, development, recapitulation).
    """
    
    phrases: List[Phrase]
    name: Optional[str] = None
    repeat: bool = False
    
    def __post_init__(self):
        if not self.phrases:
            raise ValueError("Section must contain at least one phrase")
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes in the section."""
        notes = []
        for phrase in self.phrases:
            notes.extend(phrase.get_all_notes())
        return notes
    
    def total_duration(self) -> float:
        """Get the total duration of the section in beats."""
        duration = sum(phrase.total_duration() for phrase in self.phrases)
        return duration * 2 if self.repeat else duration


@dataclass
class Composition:
    """
    A complete musical composition with metadata and structural sections.
    """
    
    title: str
    sections: List[Section]
    tempo: Tempo = field(default_factory=lambda: Tempo(120))
    time_signature: TimeSignature = field(default_factory=lambda: TimeSignature(4, 4))
    key_signature: Optional[str] = None
    composer: Optional[str] = None
    form: Optional[str] = None  # e.g., "Sonata", "Rondo", "Theme and Variations"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.sections:
            raise ValueError("Composition must contain at least one section")
    
    def get_all_notes(self) -> List[Note]:
        """Get all notes in the composition."""
        notes = []
        for section in self.sections:
            section_notes = section.get_all_notes()
            notes.extend(section_notes)
            # If section repeats, add notes again
            if section.repeat:
                notes.extend(section_notes)
        return notes
    
    def total_duration(self) -> float:
        """Get the total duration of the composition in beats."""
        return sum(section.total_duration() for section in self.sections)
    
    def duration_in_seconds(self) -> float:
        """Get the total duration of the composition in seconds."""
        beats = self.total_duration()
        # Convert beats to seconds: (beats / bpm) * 60
        return (beats / self.tempo.bpm) * 60
    
    def add_section(self, section: Section):
        """Add a section to the composition."""
        self.sections.append(section)
    
    def get_section_by_name(self, name: str) -> Optional[Section]:
        """Get a section by its name."""
        for section in self.sections:
            if section.name == name:
                return section
        return None
