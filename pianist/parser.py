"""
Parser for converting AI model text responses into structured music data.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from .music_theory import Note, TimeSignature, Tempo, Scale, ScaleType, Chord, ChordType
from .composition import Motif, Phrase, Section, Composition


class MusicParser:
    """
    Parses AI-generated text descriptions of music into structured Composition objects.
    
    Supports various formats for describing notes, chords, rhythms, and musical structures.
    """
    
    def __init__(self):
        self.default_tempo = 120
        self.default_time_signature = TimeSignature(4, 4)
        self.default_velocity = 64
    
    def parse_note(self, note_str: str) -> Note:
        """
        Parse a note string into a Note object.
        
        Formats supported:
        - "C4:1.0:64" - note name, octave, duration, velocity
        - "C4:1.0" - note name, octave, duration (default velocity)
        - "C4" - note name, octave (default duration and velocity)
        - "60:1.0:64" - MIDI pitch, duration, velocity
        - "60" - MIDI pitch only
        
        Args:
            note_str: String representation of a note
            
        Returns:
            Note object
        """
        parts = note_str.strip().split(':')
        
        # Check if first part is a MIDI pitch number or note name
        first_part = parts[0].strip()
        
        if first_part.isdigit():
            # MIDI pitch format
            pitch = int(first_part)
            duration = float(parts[1]) if len(parts) > 1 else 1.0
            velocity = int(parts[2]) if len(parts) > 2 else self.default_velocity
            return Note(pitch=pitch, duration=duration, velocity=velocity)
        else:
            # Note name format (e.g., "C4", "C#4", "Db5")
            # Extract note name and octave
            match = re.match(r'([A-Ga-g][#b]?)(\d+)', first_part)
            if not match:
                raise ValueError(f"Invalid note format: {note_str}")
            
            note_name = match.group(1)
            octave = int(match.group(2))
            duration = float(parts[1]) if len(parts) > 1 else 1.0
            velocity = int(parts[2]) if len(parts) > 2 else self.default_velocity
            
            return Note.from_name(note_name, octave, duration, velocity)
    
    def parse_chord(self, chord_str: str) -> List[Note]:
        """
        Parse a chord string into a list of Note objects.
        
        Formats supported:
        - "Cmaj" - C major chord
        - "Cmin" - C minor chord
        - "C#dim" - C# diminished chord
        - "Dmaj7" - D major seventh chord
        - "C4maj:2.0:80" - C4 major chord with duration 2.0 and velocity 80
        
        Args:
            chord_str: String representation of a chord
            
        Returns:
            List of Note objects representing the chord
        """
        # Parse format: note[octave]type[:duration[:velocity]]
        parts = chord_str.strip().split(':')
        chord_part = parts[0]
        duration = float(parts[1]) if len(parts) > 1 else 1.0
        velocity = int(parts[2]) if len(parts) > 2 else self.default_velocity
        
        # Extract note name, octave, and chord type (order matters - longer patterns first!)
        match = re.match(r'([A-Ga-g][#b]?)(\d+)?(maj7|min7|dom7|dim7|maj|min|dim|aug|sus2|sus4)', chord_part)
        if not match:
            raise ValueError(f"Invalid chord format: {chord_str}")
        
        note_name = match.group(1)
        octave = int(match.group(2)) if match.group(2) else 4
        chord_type_str = match.group(3)
        
        # Map chord type string to ChordType enum
        chord_type_map = {
            'maj': ChordType.MAJOR,
            'min': ChordType.MINOR,
            'dim': ChordType.DIMINISHED,
            'aug': ChordType.AUGMENTED,
            'maj7': ChordType.MAJOR_SEVENTH,
            'min7': ChordType.MINOR_SEVENTH,
            'dom7': ChordType.DOMINANT_SEVENTH,
            'dim7': ChordType.DIMINISHED_SEVENTH,
            'sus2': ChordType.SUSPENDED_SECOND,
            'sus4': ChordType.SUSPENDED_FOURTH,
        }
        
        chord_type = chord_type_map.get(chord_type_str, ChordType.MAJOR)
        
        # Create the chord
        root_note = Note.from_name(note_name, octave, duration, velocity)
        chord = Chord(root=root_note.pitch, chord_type=chord_type)
        
        # Convert chord pitches to Note objects
        return [
            Note(pitch=pitch, duration=duration, velocity=velocity)
            for pitch in chord.get_notes()
        ]
    
    def parse_motif(self, motif_str: str, name: Optional[str] = None) -> Motif:
        """
        Parse a motif string into a Motif object.
        
        Format: notes separated by spaces or commas
        Example: "C4:1.0 D4:0.5 E4:0.5 F4:2.0"
        
        Args:
            motif_str: String representation of a motif
            name: Optional name for the motif
            
        Returns:
            Motif object
        """
        # Split by spaces or commas
        note_strings = re.split(r'[,\s]+', motif_str.strip())
        notes = [self.parse_note(ns) for ns in note_strings if ns]
        
        return Motif(notes=notes, name=name)
    
    def parse_phrase(self, phrase_dict: Dict[str, Any]) -> Phrase:
        """
        Parse a phrase dictionary into a Phrase object.
        
        Expected format:
        {
            "name": "Opening phrase",
            "motifs": ["C4:1.0 D4:1.0", "E4:0.5 F4:0.5"]
        }
        
        Args:
            phrase_dict: Dictionary representation of a phrase
            
        Returns:
            Phrase object
        """
        motifs = []
        for motif_data in phrase_dict.get('motifs', []):
            if isinstance(motif_data, str):
                motifs.append(self.parse_motif(motif_data))
            elif isinstance(motif_data, dict):
                motif_str = motif_data.get('notes', '')
                motif_name = motif_data.get('name')
                motifs.append(self.parse_motif(motif_str, motif_name))
        
        return Phrase(motifs=motifs, name=phrase_dict.get('name'))
    
    def parse_section(self, section_dict: Dict[str, Any]) -> Section:
        """
        Parse a section dictionary into a Section object.
        
        Expected format:
        {
            "name": "Exposition",
            "phrases": [...],
            "repeat": false
        }
        
        Args:
            section_dict: Dictionary representation of a section
            
        Returns:
            Section object
        """
        phrases = []
        for phrase_data in section_dict.get('phrases', []):
            if isinstance(phrase_data, dict):
                phrases.append(self.parse_phrase(phrase_data))
        
        return Section(
            phrases=phrases,
            name=section_dict.get('name'),
            repeat=section_dict.get('repeat', False)
        )
    
    def parse_composition(self, composition_dict: Dict[str, Any]) -> Composition:
        """
        Parse a composition dictionary into a Composition object.
        
        Expected format:
        {
            "title": "Sonata in C Major",
            "composer": "AI Assistant",
            "tempo": 120,
            "time_signature": [4, 4],
            "key_signature": "C major",
            "form": "Sonata",
            "sections": [...]
        }
        
        Args:
            composition_dict: Dictionary representation of a composition
            
        Returns:
            Composition object
        """
        # Parse tempo
        tempo_value = composition_dict.get('tempo', self.default_tempo)
        tempo = Tempo(bpm=tempo_value)
        
        # Parse time signature
        ts_data = composition_dict.get('time_signature', [4, 4])
        time_signature = TimeSignature(numerator=ts_data[0], denominator=ts_data[1])
        
        # Parse sections
        sections = []
        for section_data in composition_dict.get('sections', []):
            if isinstance(section_data, dict):
                sections.append(self.parse_section(section_data))
        
        return Composition(
            title=composition_dict.get('title', 'Untitled'),
            sections=sections,
            tempo=tempo,
            time_signature=time_signature,
            key_signature=composition_dict.get('key_signature'),
            composer=composition_dict.get('composer'),
            form=composition_dict.get('form'),
            metadata=composition_dict.get('metadata', {})
        )
    
    def parse_simple_melody(self, melody_str: str, title: str = "Simple Melody") -> Composition:
        """
        Parse a simple melody string into a Composition object.
        
        This is a convenience method for quickly creating compositions from simple note sequences.
        
        Format: notes separated by spaces or commas
        Example: "C4:1.0 D4:1.0 E4:1.0 F4:2.0"
        
        Args:
            melody_str: String representation of a melody
            title: Title for the composition
            
        Returns:
            Composition object
        """
        motif = self.parse_motif(melody_str)
        phrase = Phrase(motifs=[motif], name="Main theme")
        section = Section(phrases=[phrase], name="Main section")
        
        return Composition(
            title=title,
            sections=[section],
            tempo=Tempo(bpm=self.default_tempo),
            time_signature=self.default_time_signature
        )
