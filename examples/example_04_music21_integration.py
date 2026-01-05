"""
Example: Using music21 directly alongside our parser for advanced features.
"""

from pianist import MusicParser
from music21 import stream, chord as m21_chord

# Parse a simple melody with our parser
parser = MusicParser()
melody_part = parser.parse_motif("C4:1.0 E4:1.0 G4:1.0 C5:2.0")

# Create a score
score = stream.Score()

# Add the melody
score.append(melody_part)

# Use music21's built-in harmony capabilities to add chords
harmony_part = stream.Part()

# Create a I-IV-V-I progression using music21's Chord class
c_major = m21_chord.Chord('C4 E4 G4')
c_major.quarterLength = 1.0
harmony_part.append(c_major)

f_major = m21_chord.Chord('F3 A3 C4')
f_major.quarterLength = 1.0
harmony_part.append(f_major)

g_major = m21_chord.Chord('G3 B3 D4')
g_major.quarterLength = 1.0
harmony_part.append(g_major)

c_major_final = m21_chord.Chord('C3 E3 G3')
c_major_final.quarterLength = 2.0
harmony_part.append(c_major_final)

score.append(harmony_part)

# Export to MIDI
score.write('midi', fp='melody_with_chords.mid')

print("✓ Generated melody_with_chords.mid")
print(f"  Melody + I-IV-V-I chord progression")
print(f"  Combining custom parser with music21's chord library")
