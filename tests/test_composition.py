"""Tests for composition structures."""

import pytest
from pianist.music_theory import Note
from pianist.composition import Motif, Phrase, Section, Composition, Tempo, TimeSignature


class TestMotif:
    """Tests for the Motif class."""
    
    def test_motif_creation(self):
        """Test creating a motif."""
        notes = [Note(60, 1.0), Note(62, 1.0), Note(64, 1.0)]
        motif = Motif(notes=notes, name="Opening")
        assert len(motif.notes) == 3
        assert motif.name == "Opening"
    
    def test_motif_transpose(self):
        """Test transposing a motif."""
        notes = [Note(60, 1.0), Note(62, 1.0), Note(64, 1.0)]
        motif = Motif(notes=notes)
        transposed = motif.transpose(2)
        
        assert transposed.notes[0].pitch == 62
        assert transposed.notes[1].pitch == 64
        assert transposed.notes[2].pitch == 66
    
    def test_motif_augment(self):
        """Test augmenting a motif (longer durations)."""
        notes = [Note(60, 1.0), Note(62, 1.0)]
        motif = Motif(notes=notes)
        augmented = motif.augment(2.0)
        
        assert augmented.notes[0].duration == 2.0
        assert augmented.notes[1].duration == 2.0
    
    def test_motif_diminish(self):
        """Test diminishing a motif (shorter durations)."""
        notes = [Note(60, 2.0), Note(62, 2.0)]
        motif = Motif(notes=notes)
        diminished = motif.diminish(2.0)
        
        assert diminished.notes[0].duration == 1.0
        assert diminished.notes[1].duration == 1.0
    
    def test_motif_invert(self):
        """Test inverting a motif."""
        notes = [Note(60, 1.0), Note(64, 1.0), Note(67, 1.0)]
        motif = Motif(notes=notes)
        inverted = motif.invert(axis=64)
        
        # Inversion around C (64): C->C, E->C, G->A
        assert inverted.notes[0].pitch == 68
        assert inverted.notes[1].pitch == 64
        assert inverted.notes[2].pitch == 61
    
    def test_motif_retrograde(self):
        """Test retrograde (reverse) of a motif."""
        notes = [Note(60, 1.0), Note(62, 1.0), Note(64, 1.0)]
        motif = Motif(notes=notes)
        retrograde = motif.retrograde()
        
        assert retrograde.notes[0].pitch == 64
        assert retrograde.notes[1].pitch == 62
        assert retrograde.notes[2].pitch == 60
    
    def test_motif_total_duration(self):
        """Test calculating total duration of a motif."""
        notes = [Note(60, 1.0), Note(62, 0.5), Note(64, 0.5)]
        motif = Motif(notes=notes)
        assert motif.total_duration() == 2.0
    
    def test_empty_motif_raises_error(self):
        """Test that creating an empty motif raises ValueError."""
        with pytest.raises(ValueError):
            Motif(notes=[])


class TestPhrase:
    """Tests for the Phrase class."""
    
    def test_phrase_creation(self):
        """Test creating a phrase."""
        motif1 = Motif(notes=[Note(60, 1.0)])
        motif2 = Motif(notes=[Note(62, 1.0)])
        phrase = Phrase(motifs=[motif1, motif2], name="Opening phrase")
        
        assert len(phrase.motifs) == 2
        assert phrase.name == "Opening phrase"
    
    def test_phrase_get_all_notes(self):
        """Test getting all notes from a phrase."""
        motif1 = Motif(notes=[Note(60, 1.0), Note(62, 1.0)])
        motif2 = Motif(notes=[Note(64, 1.0)])
        phrase = Phrase(motifs=[motif1, motif2])
        
        all_notes = phrase.get_all_notes()
        assert len(all_notes) == 3
        assert all_notes[0].pitch == 60
        assert all_notes[1].pitch == 62
        assert all_notes[2].pitch == 64
    
    def test_phrase_total_duration(self):
        """Test calculating total duration of a phrase."""
        motif1 = Motif(notes=[Note(60, 1.0)])
        motif2 = Motif(notes=[Note(62, 0.5)])
        phrase = Phrase(motifs=[motif1, motif2])
        
        assert phrase.total_duration() == 1.5


class TestSection:
    """Tests for the Section class."""
    
    def test_section_creation(self):
        """Test creating a section."""
        motif = Motif(notes=[Note(60, 1.0)])
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase], name="Exposition", repeat=True)
        
        assert len(section.phrases) == 1
        assert section.name == "Exposition"
        assert section.repeat is True
    
    def test_section_total_duration_with_repeat(self):
        """Test calculating duration with repeat."""
        motif = Motif(notes=[Note(60, 2.0)])
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase], repeat=True)
        
        # Should be doubled due to repeat
        assert section.total_duration() == 4.0


class TestComposition:
    """Tests for the Composition class."""
    
    def test_composition_creation(self):
        """Test creating a composition."""
        motif = Motif(notes=[Note(60, 1.0)])
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase], name="Main")
        
        composition = Composition(
            title="Test Piece",
            sections=[section],
            tempo=Tempo(120),
            time_signature=TimeSignature(4, 4),
            composer="Test Composer"
        )
        
        assert composition.title == "Test Piece"
        assert composition.composer == "Test Composer"
        assert len(composition.sections) == 1
    
    def test_composition_get_all_notes(self):
        """Test getting all notes from a composition."""
        notes1 = [Note(60, 1.0), Note(62, 1.0)]
        notes2 = [Note(64, 1.0), Note(65, 1.0)]
        
        motif1 = Motif(notes=notes1)
        motif2 = Motif(notes=notes2)
        phrase1 = Phrase(motifs=[motif1])
        phrase2 = Phrase(motifs=[motif2])
        section = Section(phrases=[phrase1, phrase2])
        
        composition = Composition(title="Test", sections=[section])
        all_notes = composition.get_all_notes()
        
        assert len(all_notes) == 4
        assert all_notes[0].pitch == 60
        assert all_notes[3].pitch == 65
    
    def test_composition_duration_in_seconds(self):
        """Test calculating duration in seconds."""
        motif = Motif(notes=[Note(60, 4.0)])  # 4 beats
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase])
        
        composition = Composition(
            title="Test",
            sections=[section],
            tempo=Tempo(120)  # 120 BPM = 2 beats per second
        )
        
        # 4 beats at 120 BPM = 2 seconds
        assert composition.duration_in_seconds() == 2.0
    
    def test_composition_add_section(self):
        """Test adding a section to a composition."""
        motif = Motif(notes=[Note(60, 1.0)])
        phrase = Phrase(motifs=[motif])
        section1 = Section(phrases=[phrase], name="Section 1")
        section2 = Section(phrases=[phrase], name="Section 2")
        
        composition = Composition(title="Test", sections=[section1])
        assert len(composition.sections) == 1
        
        composition.add_section(section2)
        assert len(composition.sections) == 2
    
    def test_composition_get_section_by_name(self):
        """Test getting a section by name."""
        motif = Motif(notes=[Note(60, 1.0)])
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase], name="Exposition")
        
        composition = Composition(title="Test", sections=[section])
        found_section = composition.get_section_by_name("Exposition")
        
        assert found_section is not None
        assert found_section.name == "Exposition"
    
    def test_composition_get_section_by_name_not_found(self):
        """Test getting a nonexistent section returns None."""
        motif = Motif(notes=[Note(60, 1.0)])
        phrase = Phrase(motifs=[motif])
        section = Section(phrases=[phrase], name="Exposition")
        
        composition = Composition(title="Test", sections=[section])
        found_section = composition.get_section_by_name("Nonexistent")
        
        assert found_section is None
