"""
Example: Using motif transformations (transpose, invert, retrograde).
"""

from pianist import Note, Motif, Phrase, Section, Composition, Tempo, MIDIGenerator

# Create an original motif
original_notes = [
    Note.from_name("C", 4, 0.5, 64),
    Note.from_name("E", 4, 0.5, 64),
    Note.from_name("G", 4, 0.5, 64),
    Note.from_name("C", 5, 1.0, 80),
]
original_motif = Motif(notes=original_notes, name="Original")

# Create transformations
transposed_motif = original_motif.transpose(2)  # Up a whole step
transposed_motif.name = "Transposed"

inverted_motif = original_motif.invert(axis=64)  # Invert around E4
inverted_motif.name = "Inverted"

retrograde_motif = original_motif.retrograde()  # Play backwards
retrograde_motif.name = "Retrograde"

# Create phrases from each variation
phrases = [
    Phrase(motifs=[original_motif], name="Original"),
    Phrase(motifs=[transposed_motif], name="Transposed"),
    Phrase(motifs=[inverted_motif], name="Inverted"),
    Phrase(motifs=[retrograde_motif], name="Retrograde"),
]

# Create sections
section = Section(phrases=phrases, name="Theme and Variations")

# Create composition
composition = Composition(
    title="Motif Transformations",
    sections=[section],
    tempo=Tempo(120),
    composer="Example AI"
)

# Generate MIDI
generator = MIDIGenerator(composition)
generator.generate("motif_transformations.mid")

print("✓ Generated motif_transformations.mid")
print(f"  Original motif: {len(original_motif.notes)} notes")
print(f"  Total variations: {len(phrases)}")
print(f"  Duration: {composition.duration_in_seconds():.2f} seconds")
