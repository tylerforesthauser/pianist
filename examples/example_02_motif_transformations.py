"""
Example: Using music21's powerful transformation capabilities on parsed motifs.
"""

from pianist import MusicParser
from music21 import stream
import copy

# Parse a motif
parser = MusicParser()
motif = parser.parse_motif("C4:0.5 E4:0.5 G4:0.5 C5:1.0")

# Create a score with original and transformations
score = stream.Score()
part = stream.Part()

# Original motif
for note in motif.notesAndRests:
    part.append(copy.deepcopy(note))

# Transpose up a whole step (music21 built-in)
transposed = motif.transpose(2)
for note in transposed.notesAndRests:
    part.append(copy.deepcopy(note))

# Transpose down a major third
transposed_down = motif.transpose(-4)
for note in transposed_down.notesAndRests:
    part.append(copy.deepcopy(note))

# Retrograde (play backwards)
notes_list = list(motif.notesAndRests)
for note in reversed(notes_list):
    part.append(copy.deepcopy(note))

score.append(part)

# Export to MIDI
score.write('midi', fp='motif_transformations.mid')

print("✓ Generated motif_transformations.mid")
print(f"  Original motif + transposed up + transposed down + retrograde")
print(f"  Using music21's built-in transformation methods")
