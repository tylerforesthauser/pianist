"""Tests for the parser module using music21."""

import pytest
from pianist import MusicParser
from music21 import note, stream


class TestMusicParser:
    """Tests for the MusicParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MusicParser()
    
    def test_parse_note_with_name(self):
        """Test parsing a note from name format."""
        n = self.parser.parse_note("C4:1.0:64")
        assert n.pitch.midi == 60
        assert n.quarterLength == 1.0
        assert n.volume.velocity == 64
    
    def test_parse_note_with_name_short(self):
        """Test parsing a note with only name."""
        n = self.parser.parse_note("A4")
        assert n.pitch.midi == 69
        assert n.quarterLength == 1.0
    
    def test_parse_note_with_sharp(self):
        """Test parsing a note with sharp."""
        n = self.parser.parse_note("C#4:1.0")
        assert n.pitch.midi == 61
    
    def test_parse_note_with_flat(self):
        """Test parsing a note with flat."""
        n = self.parser.parse_note("D-4:1.0")
        assert n.pitch.midi == 61
    
    def test_parse_note_with_midi_pitch(self):
        """Test parsing a note from MIDI pitch format."""
        n = self.parser.parse_note("60:1.0:64")
        assert n.pitch.midi == 60
        assert n.quarterLength == 1.0
        assert n.volume.velocity == 64
    
    def test_parse_note_with_midi_pitch_short(self):
        """Test parsing a note with only MIDI pitch."""
        n = self.parser.parse_note("60")
        assert n.pitch.midi == 60
    
    def test_parse_chord_major(self):
        """Test parsing a major chord."""
        c = self.parser.parse_chord("C4maj:2.0:80")
        assert len(c.pitches) >= 3
        assert c.quarterLength == 2.0
    
    def test_parse_chord_minor(self):
        """Test parsing a minor chord."""
        c = self.parser.parse_chord("A4min")
        assert len(c.pitches) >= 3
    
    def test_parse_chord_seventh(self):
        """Test parsing a seventh chord."""
        c = self.parser.parse_chord("C4maj7")
        assert len(c.pitches) >= 4
    
    def test_parse_motif(self):
        """Test parsing a motif from string."""
        part = self.parser.parse_motif("C4:1.0 D4:1.0 E4:1.0")
        notes = list(part.notesAndRests)
        assert len(notes) == 3
        assert notes[0].pitch.midi == 60
        assert notes[1].pitch.midi == 62
        assert notes[2].pitch.midi == 64
    
    def test_parse_motif_with_commas(self):
        """Test parsing a motif with comma separators."""
        part = self.parser.parse_motif("C4:1.0, D4:1.0, E4:1.0")
        notes = list(part.notesAndRests)
        assert len(notes) == 3
    
    def test_parse_phrase(self):
        """Test parsing a phrase from dictionary."""
        phrase_dict = {
            "name": "Opening",
            "motifs": [
                "C4:1.0 D4:1.0",
                "E4:1.0 F4:1.0"
            ]
        }
        part = self.parser.parse_phrase(phrase_dict)
        notes = list(part.notesAndRests)
        assert len(notes) == 4
    
    def test_parse_phrase_with_motif_names(self):
        """Test parsing a phrase with named motifs."""
        phrase_dict = {
            "name": "Opening",
            "motifs": [
                {"name": "Motif A", "notes": "C4:1.0 D4:1.0"},
                {"name": "Motif B", "notes": "E4:1.0 F4:1.0"}
            ]
        }
        part = self.parser.parse_phrase(phrase_dict)
        notes = list(part.notesAndRests)
        assert len(notes) == 4
    
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
        part = self.parser.parse_section(section_dict)
        notes = list(part.notesAndRests)
        # Should have 6 notes (3 notes repeated)
        assert len(notes) == 6
    
    def test_parse_composition(self):
        """Test parsing a full composition from dictionary."""
        composition_dict = {
            "title": "Test Sonata",
            "composer": "AI Assistant",
            "tempo": 120,
            "time_signature": [4, 4],
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
        score = self.parser.parse_composition(composition_dict)
        assert score.metadata.title == "Test Sonata"
        assert score.metadata.composer == "AI Assistant"
        
        # Get all notes from the score
        notes = list(score.flatten().notesAndRests)
        assert len(notes) == 4
    
    def test_parse_simple_melody(self):
        """Test parsing a simple melody."""
        score = self.parser.parse_simple_melody(
            "C4:1.0 D4:1.0 E4:1.0 F4:2.0",
            title="Simple Test"
        )
        assert score.metadata.title == "Simple Test"
        notes = list(score.flatten().notesAndRests)
        assert len(notes) == 4
        assert notes[0].pitch.midi == 60
        assert notes[3].quarterLength == 2.0
    
    def test_midi_export(self):
        """Test that we can export to MIDI."""
        import tempfile
        import os
        
        score = self.parser.parse_simple_melody("C4:1.0 D4:1.0 E4:1.0")
        
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            score.write('midi', fp=tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
