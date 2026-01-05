"""
Basic example: Creating a simple melody and converting it to MIDI.
"""

from pianist import Note, Motif, Phrase, Section, Composition, Tempo, TimeSignature, MIDIGenerator

# Create a simple melody: C-D-E-F-G-A-G-F-E-D-C
notes = [
    Note.from_name("C", 4, 1.0, 64),
    Note.from_name("D", 4, 1.0, 64),
    Note.from_name("E", 4, 1.0, 64),
    Note.from_name("F", 4, 1.0, 64),
    Note.from_name("G", 4, 1.0, 80),  # Accent on G
    Note.from_name("A", 4, 1.0, 64),
    Note.from_name("G", 4, 1.0, 64),
    Note.from_name("F", 4, 1.0, 64),
    Note.from_name("E", 4, 1.0, 64),
    Note.from_name("D", 4, 1.0, 64),
    Note.from_name("C", 4, 2.0, 64),  # Longer final note
]

# Create a motif from the notes
motif = Motif(notes=notes, name="Ascending-Descending Scale")

# Create a phrase from the motif
phrase = Phrase(motifs=[motif], name="Main Theme")

# Create a section from the phrase
section = Section(phrases=[phrase], name="Main Section")

# Create a composition
composition = Composition(
    title="Simple Scale Melody",
    sections=[section],
    tempo=Tempo(120),
    time_signature=TimeSignature(4, 4),
    composer="Example AI"
)

# Generate MIDI file
generator = MIDIGenerator(composition)
generator.generate("simple_melody.mid")

print("✓ Generated simple_melody.mid")
print(f"  Duration: {composition.duration_in_seconds():.2f} seconds")
print(f"  Number of notes: {len(composition.get_all_notes())}")
