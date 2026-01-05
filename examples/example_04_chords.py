"""
Example: Using chords and creating a harmonic progression.
"""

from pianist import Note, Chord, ChordType, Motif, Phrase, Section, Composition, MIDIGenerator, Tempo

# Create a chord progression: I - IV - V - I in C major
# Each chord will be played as a broken chord (arpeggio)

def chord_to_arpeggio(chord: Chord, duration_per_note: float = 0.5, velocity: int = 64):
    """Convert a chord to an arpeggio motif."""
    pitches = chord.get_notes()
    notes = [Note(pitch, duration_per_note, velocity) for pitch in pitches]
    return Motif(notes=notes)

# I chord - C major (C-E-G)
c_major = Chord(root=60, chord_type=ChordType.MAJOR)
i_motif = chord_to_arpeggio(c_major)
i_motif.name = "I - C major"

# IV chord - F major (F-A-C)
f_major = Chord(root=65, chord_type=ChordType.MAJOR)
iv_motif = chord_to_arpeggio(f_major)
iv_motif.name = "IV - F major"

# V chord - G major (G-B-D)
g_major = Chord(root=67, chord_type=ChordType.MAJOR)
v_motif = chord_to_arpeggio(g_major)
v_motif.name = "V - G major"

# Back to I
i_motif_final = chord_to_arpeggio(c_major, duration_per_note=0.5)
i_motif_final.name = "I - C major (final)"

# Create phrase from chord progression
progression = Phrase(
    motifs=[i_motif, iv_motif, v_motif, i_motif_final],
    name="I-IV-V-I Progression"
)

# Create section
section = Section(phrases=[progression], name="Harmonic Progression", repeat=True)

# Create composition
composition = Composition(
    title="Chord Progression Study",
    sections=[section],
    tempo=Tempo(90),
    composer="Example AI",
    key_signature="C major"
)

# Generate MIDI
generator = MIDIGenerator(composition)
generator.generate("chord_progression.mid")

print("✓ Generated chord_progression.mid")
print(f"  Chord progression: I - IV - V - I")
print(f"  Key: C major")
print(f"  Duration: {composition.duration_in_seconds():.2f} seconds")
