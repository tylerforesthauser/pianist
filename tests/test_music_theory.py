"""Tests for music theory primitives."""

import pytest
from pianist.music_theory import (
    Note, NoteName, Scale, ScaleType, Chord, ChordType,
    TimeSignature, Tempo, Dynamics
)


class TestNote:
    """Tests for the Note class."""
    
    def test_note_creation(self):
        """Test creating a note with MIDI pitch."""
        note = Note(pitch=60, duration=1.0, velocity=64)
        assert note.pitch == 60
        assert note.duration == 1.0
        assert note.velocity == 64
    
    def test_note_from_name(self):
        """Test creating a note from name and octave."""
        note = Note.from_name("C", 4, 1.0, 64)
        assert note.pitch == 60  # C4 is MIDI pitch 60
        
        note = Note.from_name("A", 4, 1.0, 64)
        assert note.pitch == 69  # A4 is MIDI pitch 69
    
    def test_note_from_name_with_sharp(self):
        """Test creating a note with sharp."""
        note = Note.from_name("C#", 4, 1.0, 64)
        assert note.pitch == 61
    
    def test_note_from_name_with_flat(self):
        """Test creating a note with flat."""
        note = Note.from_name("Db", 4, 1.0, 64)
        assert note.pitch == 61
    
    def test_note_invalid_pitch(self):
        """Test that invalid pitch raises ValueError."""
        with pytest.raises(ValueError):
            Note(pitch=128, duration=1.0, velocity=64)
        
        with pytest.raises(ValueError):
            Note(pitch=-1, duration=1.0, velocity=64)
    
    def test_note_invalid_duration(self):
        """Test that invalid duration raises ValueError."""
        with pytest.raises(ValueError):
            Note(pitch=60, duration=0, velocity=64)
        
        with pytest.raises(ValueError):
            Note(pitch=60, duration=-1.0, velocity=64)
    
    def test_note_invalid_velocity(self):
        """Test that invalid velocity raises ValueError."""
        with pytest.raises(ValueError):
            Note(pitch=60, duration=1.0, velocity=128)
        
        with pytest.raises(ValueError):
            Note(pitch=60, duration=1.0, velocity=-1)


class TestScale:
    """Tests for the Scale class."""
    
    def test_major_scale(self):
        """Test C major scale."""
        scale = Scale(root=60, scale_type=ScaleType.MAJOR)
        notes = scale.get_notes(octaves=1)
        expected = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
        assert notes == expected
    
    def test_minor_scale(self):
        """Test A natural minor scale."""
        scale = Scale(root=69, scale_type=ScaleType.NATURAL_MINOR)
        notes = scale.get_notes(octaves=1)
        expected = [69, 71, 72, 74, 76, 77, 79, 81]  # A B C D E F G A
        assert notes == expected
    
    def test_scale_degree(self):
        """Test getting scale degrees."""
        scale = Scale(root=60, scale_type=ScaleType.MAJOR)
        assert scale.get_degree(1) == 60  # C
        assert scale.get_degree(3) == 64  # E
        assert scale.get_degree(5) == 67  # G


class TestChord:
    """Tests for the Chord class."""
    
    def test_major_chord(self):
        """Test C major chord."""
        chord = Chord(root=60, chord_type=ChordType.MAJOR)
        notes = chord.get_notes()
        expected = [60, 64, 67]  # C E G
        assert notes == expected
    
    def test_minor_chord(self):
        """Test A minor chord."""
        chord = Chord(root=69, chord_type=ChordType.MINOR)
        notes = chord.get_notes()
        expected = [69, 72, 76]  # A C E
        assert notes == expected
    
    def test_chord_inversion(self):
        """Test chord inversions."""
        chord = Chord(root=60, chord_type=ChordType.MAJOR, inversion=1)
        notes = chord.get_notes()
        expected = [64, 67, 72]  # E G C (first inversion)
        assert notes == expected


class TestTimeSignature:
    """Tests for the TimeSignature class."""
    
    def test_common_time(self):
        """Test 4/4 time signature."""
        ts = TimeSignature(4, 4)
        assert ts.numerator == 4
        assert ts.denominator == 4
        assert ts.beats_per_measure() == 4
    
    def test_waltz_time(self):
        """Test 3/4 time signature."""
        ts = TimeSignature(3, 4)
        assert ts.numerator == 3
        assert ts.beats_per_measure() == 3
    
    def test_invalid_denominator(self):
        """Test that invalid denominator raises ValueError."""
        with pytest.raises(ValueError):
            TimeSignature(4, 3)


class TestTempo:
    """Tests for the Tempo class."""
    
    def test_tempo_creation(self):
        """Test creating a tempo."""
        tempo = Tempo(120)
        assert tempo.bpm == 120
    
    def test_invalid_tempo(self):
        """Test that invalid tempo raises ValueError."""
        with pytest.raises(ValueError):
            Tempo(0)
        
        with pytest.raises(ValueError):
            Tempo(-60)
