"""
Example: Using music21's powerful transformation capabilities on parsed motifs.
"""

from pianist import MusicParser

# Parse a motif
parser = MusicParser()
motif = parser.parse_motif("C4:0.5 E4:0.5 G4:0.5 C5:1.0")

# Use music21's built-in transformations
from music21 import stream

# Create a score with original and transformations
score = stream.Score()
part = stream.Part()

# Original motif
for note in motif.notesAndRests:
    part.append(note)

# Transpose up a whole step (music21 built-in)
transposed = motif.transpose(2)
for note in transposed.notesAndRests:
    part.append(note)

# Invert (music21 built-in)
inverted = motif.transpose(12).invert()  # Transpose to make inversion sound better
for note in inverted.notesAndRests:
    part.append(note)

# Retrograde (music21 built-in)
from music21 import stream as m21stream
retrograde_part = m21stream.Part()
notes_list = list(motif.notesAndRests)
for note in reversed(notes_list):
    import copy
    retrograde_part.append(copy.deepcopy(note))

for note in retrograde_part.notesAndRests:
    part.append(note)

score.append(part)

# Export to MIDI
score.write('midi', fp='motif_transformations.mid')

print("✓ Generated motif_transformations.mid")
print(f"  Original motif + transposed + inverted + retrograde")
print(f"  Using music21's built-in transformation methods")
