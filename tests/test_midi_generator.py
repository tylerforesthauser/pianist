"""Tests for MIDI generation."""

import pytest
import os
import tempfile
from pianist.music_theory import Note
from pianist.composition import Motif, Phrase, Section, Composition, Tempo, TimeSignature
from pianist.midi_generator import MIDIGenerator, MultiTrackMIDIGenerator


class TestMIDIGenerator:
    """Tests for the MIDIGenerator class."""
    
    def test_generate_simple_composition(self):
        """Test generating a MIDI file from a simple composition."""
        # Create a simple composition
        notes = [Note(60, 1.0), Note(62, 1.0), Note(64, 1.0)]
        motif = Motif(notes=notes)
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase])
        composition = Composition(
            title="Test Piece",
            sections=[section],
            tempo=Tempo(120),
            time_signature=TimeSignature(4, 4)
        )
        
        # Generate MIDI file
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generator = MIDIGenerator(composition)
            generator.generate(tmp_path)
            
            # Verify file was created
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_generate_from_notes_static_method(self):
        """Test generating a MIDI file directly from notes."""
        notes = [
            Note(60, 1.0, 64),
            Note(62, 1.0, 64),
            Note(64, 1.0, 64),
            Note(65, 2.0, 64)
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            MIDIGenerator.from_notes(notes, tmp_path, title="Quick Test")
            
            # Verify file was created
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestMultiTrackMIDIGenerator:
    """Tests for the MultiTrackMIDIGenerator class."""
    
    def test_generate_multitrack(self):
        """Test generating a multi-track MIDI file."""
        # Create notes for right hand
        right_hand = [Note(60, 1.0), Note(64, 1.0), Note(67, 1.0)]
        
        # Create notes for left hand
        left_hand = [Note(48, 3.0)]
        
        generator = MultiTrackMIDIGenerator()
        generator.add_track(right_hand, "Right Hand", channel=0)
        generator.add_track(left_hand, "Left Hand", channel=0)
        
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generator.generate(tmp_path, tempo=120)
            
            # Verify file was created
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
