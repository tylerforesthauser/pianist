"""Tests for the parser module."""

import pytest
from pianist.parser import MusicParser
from pianist.music_theory import Note
from pianist.composition import Motif, Composition


class TestMusicParser:
    """Tests for the MusicParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MusicParser()
    
    def test_parse_note_with_name(self):
        """Test parsing a note from name format."""
        note = self.parser.parse_note("C4:1.0:64")
        assert note.pitch == 60
        assert note.duration == 1.0
        assert note.velocity == 64
    
    def test_parse_note_with_name_short(self):
        """Test parsing a note with only name and octave."""
        note = self.parser.parse_note("A4")
        assert note.pitch == 69
        assert note.duration == 1.0
        assert note.velocity == 64
    
    def test_parse_note_with_sharp(self):
        """Test parsing a note with sharp."""
        note = self.parser.parse_note("C#4:1.0")
        assert note.pitch == 61
    
    def test_parse_note_with_flat(self):
        """Test parsing a note with flat."""
        note = self.parser.parse_note("Db4:1.0")
        assert note.pitch == 61
    
    def test_parse_note_with_midi_pitch(self):
        """Test parsing a note from MIDI pitch format."""
        note = self.parser.parse_note("60:1.0:64")
        assert note.pitch == 60
        assert note.duration == 1.0
        assert note.velocity == 64
    
    def test_parse_note_with_midi_pitch_short(self):
        """Test parsing a note with only MIDI pitch."""
        note = self.parser.parse_note("60")
        assert note.pitch == 60
        assert note.duration == 1.0
        assert note.velocity == 64
    
    def test_parse_chord_major(self):
        """Test parsing a major chord."""
        notes = self.parser.parse_chord("C4maj:2.0:80")
        assert len(notes) == 3
        assert notes[0].pitch == 60  # C
        assert notes[1].pitch == 64  # E
        assert notes[2].pitch == 67  # G
        assert all(n.duration == 2.0 for n in notes)
        assert all(n.velocity == 80 for n in notes)
    
    def test_parse_chord_minor(self):
        """Test parsing a minor chord."""
        notes = self.parser.parse_chord("A4min")
        assert len(notes) == 3
        assert notes[0].pitch == 69  # A
        assert notes[1].pitch == 72  # C
        assert notes[2].pitch == 76  # E
    
    def test_parse_chord_seventh(self):
        """Test parsing a seventh chord."""
        notes = self.parser.parse_chord("C4maj7")
        assert len(notes) == 4
        assert notes[0].pitch == 60  # C
        assert notes[1].pitch == 64  # E
        assert notes[2].pitch == 67  # G
        assert notes[3].pitch == 71  # B
    
    def test_parse_motif(self):
        """Test parsing a motif from string."""
        motif = self.parser.parse_motif("C4:1.0 D4:1.0 E4:1.0", name="Test Motif")
        assert len(motif.notes) == 3
        assert motif.notes[0].pitch == 60
        assert motif.notes[1].pitch == 62
        assert motif.notes[2].pitch == 64
        assert motif.name == "Test Motif"
    
    def test_parse_motif_with_commas(self):
        """Test parsing a motif with comma separators."""
        motif = self.parser.parse_motif("C4:1.0, D4:1.0, E4:1.0")
        assert len(motif.notes) == 3
    
    def test_parse_phrase(self):
        """Test parsing a phrase from dictionary."""
        phrase_dict = {
            "name": "Opening",
            "motifs": [
                "C4:1.0 D4:1.0",
                "E4:1.0 F4:1.0"
            ]
        }
        phrase = self.parser.parse_phrase(phrase_dict)
        assert phrase.name == "Opening"
        assert len(phrase.motifs) == 2
        assert len(phrase.get_all_notes()) == 4
    
    def test_parse_phrase_with_motif_names(self):
        """Test parsing a phrase with named motifs."""
        phrase_dict = {
            "name": "Opening",
            "motifs": [
                {"name": "Motif A", "notes": "C4:1.0 D4:1.0"},
                {"name": "Motif B", "notes": "E4:1.0 F4:1.0"}
            ]
        }
        phrase = self.parser.parse_phrase(phrase_dict)
        assert phrase.motifs[0].name == "Motif A"
        assert phrase.motifs[1].name == "Motif B"
    
    def test_parse_section(self):
        """Test parsing a section from dictionary."""
        section_dict = {
            "name": "Exposition",
            "repeat": True,
            "phrases": [
                {
                    "name": "Theme 1",
                    "motifs": ["C4:1.0 D4:1.0 E4:1.0"]
                }
            ]
        }
        section = self.parser.parse_section(section_dict)
        assert section.name == "Exposition"
        assert section.repeat is True
        assert len(section.phrases) == 1
    
    def test_parse_composition(self):
        """Test parsing a full composition from dictionary."""
        composition_dict = {
            "title": "Test Sonata",
            "composer": "AI Assistant",
            "tempo": 120,
            "time_signature": [4, 4],
            "key_signature": "C major",
            "form": "Sonata",
            "sections": [
                {
                    "name": "Exposition",
                    "phrases": [
                        {
                            "name": "Theme",
                            "motifs": ["C4:1.0 D4:1.0 E4:1.0 F4:1.0"]
                        }
                    ]
                }
            ]
        }
        composition = self.parser.parse_composition(composition_dict)
        assert composition.title == "Test Sonata"
        assert composition.composer == "AI Assistant"
        assert composition.tempo.bpm == 120
        assert composition.time_signature.numerator == 4
        assert composition.key_signature == "C major"
        assert composition.form == "Sonata"
        assert len(composition.sections) == 1
    
    def test_parse_simple_melody(self):
        """Test parsing a simple melody."""
        composition = self.parser.parse_simple_melody(
            "C4:1.0 D4:1.0 E4:1.0 F4:2.0",
            title="Simple Test"
        )
        assert composition.title == "Simple Test"
        assert len(composition.sections) == 1
        notes = composition.get_all_notes()
        assert len(notes) == 4
        assert notes[0].pitch == 60
        assert notes[3].duration == 2.0
