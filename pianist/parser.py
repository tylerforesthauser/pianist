"""
Parser for converting AI model text responses into music21 objects.

This module provides a parser that converts structured AI responses (JSON/dict format)
into music21 Stream objects that can be exported as MIDI files.
"""

import re
import copy
from typing import Dict, Any, Optional, List
from music21 import note, chord, stream, tempo, meter, metadata


class MusicParser:
    """
    Parses AI-generated text descriptions of music into music21 Stream objects.
    
    Supports various formats for describing notes, chords, rhythms, and musical structures.
    Built on top of the music21 library for robust music theory support.
    """
    
    def __init__(self):
        self.default_tempo = 120
        self.default_time_signature = (4, 4)
    
    def parse_note(self, note_str: str) -> note.Note:
        """
        Parse a note string into a music21 Note object.
        
        Formats supported:
        - "C4:1.0:64" - note name, duration (quarter lengths), velocity
        - "C4:1.0" - note name, duration (default velocity)
        - "C4" - note name (default duration and velocity)
        - "60:1.0:64" - MIDI pitch, duration, velocity
        - "60" - MIDI pitch only
        
        Args:
            note_str: String representation of a note
            
        Returns:
            music21 Note object
        """
        parts = note_str.strip().split(':')
        first_part = parts[0].strip()
        
        # Parse duration and velocity
        duration_ql = float(parts[1]) if len(parts) > 1 else 1.0
        velocity_val = int(parts[2]) if len(parts) > 2 else 64
        
        # Create note
        if first_part.isdigit():
            # MIDI pitch format
            n = note.Note(midi=int(first_part))
        else:
            # Note name format (music21 handles this natively)
            n = note.Note(first_part)
        
        n.quarterLength = duration_ql
        n.volume.velocity = velocity_val
        
        return n
    
    def parse_chord(self, chord_str: str) -> chord.Chord:
        """
        Parse a chord string into a music21 Chord object.
        
        Formats supported:
        - "C4maj:2.0:80" - Root note, chord type, duration, velocity
        - "Cmaj" - Chord with defaults
        - "C4maj7" - Seventh chords
        
        Args:
            chord_str: String representation of a chord
            
        Returns:
            music21 Chord object
        """
        parts = chord_str.strip().split(':')
        chord_part = parts[0]
        duration_ql = float(parts[1]) if len(parts) > 1 else 1.0
        velocity_val = int(parts[2]) if len(parts) > 2 else 64
        
        # Extract note name, octave, and chord type
        match = re.match(r'([A-Ga-g][#b-]?)(\d+)?(maj7|min7|dom7|dim7|maj|min|dim|aug|sus2|sus4|7)?', chord_part)
        if not match:
            raise ValueError(f"Invalid chord format: {chord_str}")
        
        root = match.group(1)
        octave = match.group(2) if match.group(2) else '4'
        chord_type = match.group(3) if match.group(3) else 'maj'
        
        # Build chord using interval patterns
        root_note = f"{root}{octave}"
        
        # Define chord intervals (in semitones from root)
        chord_intervals = {
            'maj': [0, 4, 7],  # Major triad
            'min': [0, 3, 7],  # Minor triad
            'dim': [0, 3, 6],  # Diminished triad
            'aug': [0, 4, 8],  # Augmented triad
            'maj7': [0, 4, 7, 11],  # Major seventh
            'min7': [0, 3, 7, 10],  # Minor seventh
            'dom7': [0, 4, 7, 10],  # Dominant seventh
            '7': [0, 4, 7, 10],  # Dominant seventh (alternate)
            'dim7': [0, 3, 6, 9],  # Diminished seventh
            'sus2': [0, 2, 7],  # Suspended second
            'sus4': [0, 5, 7],  # Suspended fourth
        }
        
        intervals = chord_intervals.get(chord_type, [0, 4, 7])
        
        # Create notes for the chord
        root_pitch_note = note.Note(root_note)
        root_midi = root_pitch_note.pitch.midi
        
        chord_notes = []
        for interval in intervals:
            n = note.Note(midi=root_midi + interval)
            chord_notes.append(n)
        
        # Create chord from notes
        c = chord.Chord(chord_notes)
        c.quarterLength = duration_ql
        
        # Set velocity for all notes in chord
        for n in c.notes:
            n.volume.velocity = velocity_val
        
        return c
    
    def parse_motif(self, motif_str: str) -> stream.Part:
        """
        Parse a motif string into a music21 Part (sequence of notes).
        
        Format: notes separated by spaces or commas
        Example: "C4:1.0 D4:0.5 E4:0.5 F4:2.0"
        
        Args:
            motif_str: String representation of a motif
            
        Returns:
            music21 Part containing the notes
        """
        note_strings = re.split(r'[,\s]+', motif_str.strip())
        part = stream.Part()
        
        for note_str in note_strings:
            if note_str:
                part.append(self.parse_note(note_str))
        
        return part
    
    def parse_phrase(self, phrase_dict: Dict[str, Any]) -> stream.Part:
        """
        Parse a phrase dictionary into a music21 Part.
        
        Expected format:
        {
            "name": "Opening phrase",
            "motifs": ["C4:1.0 D4:1.0", "E4:0.5 F4:0.5"]
        }
        
        Args:
            phrase_dict: Dictionary representation of a phrase
            
        Returns:
            music21 Part containing all motifs
        """
        phrase_part = stream.Part()
        
        if 'name' in phrase_dict:
            phrase_part.partName = phrase_dict['name']
        
        for motif_data in phrase_dict.get('motifs', []):
            if isinstance(motif_data, str):
                motif_part = self.parse_motif(motif_data)
                # Append all notes from motif to phrase
                for element in motif_part.notesAndRests:
                    phrase_part.append(copy.deepcopy(element))
            elif isinstance(motif_data, dict):
                motif_str = motif_data.get('notes', '')
                motif_part = self.parse_motif(motif_str)
                for element in motif_part.notesAndRests:
                    phrase_part.append(copy.deepcopy(element))
        
        return phrase_part
    
    def parse_section(self, section_dict: Dict[str, Any]) -> stream.Part:
        """
        Parse a section dictionary into a music21 Part.
        
        Expected format:
        {
            "name": "Exposition",
            "phrases": [...],
            "repeat": false
        }
        
        Args:
            section_dict: Dictionary representation of a section
            
        Returns:
            music21 Part containing all phrases
        """
        section_part = stream.Part()
        
        if 'name' in section_dict:
            section_part.partName = section_dict['name']
        
        for phrase_data in section_dict.get('phrases', []):
            if isinstance(phrase_data, dict):
                phrase_part = self.parse_phrase(phrase_data)
                for element in phrase_part.notesAndRests:
                    section_part.append(copy.deepcopy(element))
        
        # Handle repeats by duplicating content
        if section_dict.get('repeat', False):
            # Store original elements
            original_elements = [copy.deepcopy(e) for e in section_part.notesAndRests]
            # Append them again for repeat
            for element in original_elements:
                section_part.append(element)
        
        return section_part
    
    def parse_composition(self, composition_dict: Dict[str, Any]) -> stream.Score:
        """
        Parse a composition dictionary into a music21 Score.
        
        Expected format:
        {
            "title": "Sonata in C Major",
            "composer": "AI Assistant",
            "tempo": 120,
            "time_signature": [4, 4],
            "key_signature": "C major",
            "sections": [...]
        }
        
        Args:
            composition_dict: Dictionary representation of a composition
            
        Returns:
            music21 Score object ready to export as MIDI
        """
        score = stream.Score()
        
        # Set metadata
        if 'title' in composition_dict or 'composer' in composition_dict:
            score.metadata = metadata.Metadata()
            if 'title' in composition_dict:
                score.metadata.title = composition_dict['title']
            if 'composer' in composition_dict:
                score.metadata.composer = composition_dict['composer']
        
        # Create main part for the composition
        main_part = stream.Part()
        
        # Add tempo
        tempo_val = composition_dict.get('tempo', self.default_tempo)
        main_part.insert(0, tempo.MetronomeMark(number=tempo_val))
        
        # Add time signature
        ts_data = composition_dict.get('time_signature', self.default_time_signature)
        main_part.insert(0, meter.TimeSignature(f'{ts_data[0]}/{ts_data[1]}'))
        
        # Parse all sections and add their notes
        for section_data in composition_dict.get('sections', []):
            if isinstance(section_data, dict):
                section_part = self.parse_section(section_data)
                for element in section_part.notesAndRests:
                    main_part.append(copy.deepcopy(element))
        
        score.append(main_part)
        
        return score
    
    def parse_simple_melody(self, melody_str: str, title: str = "Simple Melody") -> stream.Score:
        """
        Parse a simple melody string into a music21 Score.
        
        This is a convenience method for quickly creating compositions from simple note sequences.
        
        Format: notes separated by spaces or commas
        Example: "C4:1.0 D4:1.0 E4:1.0 F4:2.0"
        
        Args:
            melody_str: String representation of a melody
            title: Title for the composition
            
        Returns:
            music21 Score object
        """
        score = stream.Score()
        score.metadata = metadata.Metadata()
        score.metadata.title = title
        
        part = stream.Part()
        part.insert(0, tempo.MetronomeMark(number=self.default_tempo))
        part.insert(0, meter.TimeSignature(f'{self.default_time_signature[0]}/{self.default_time_signature[1]}'))
        
        motif_part = self.parse_motif(melody_str)
        for element in motif_part.notesAndRests:
            part.append(copy.deepcopy(element))
        
        score.append(part)
        return score
