"""
Basic example: Creating a simple melody using the music21-based parser.
"""

from pianist import MusicParser

# Create parser
parser = MusicParser()

# Parse a simple melody
score = parser.parse_simple_melody(
    "C4:1.0 D4:1.0 E4:1.0 F4:1.0 G4:2.0 A4:1.0 G4:1.0 F4:1.0 E4:1.0 D4:1.0 C4:2.0",
    title="C Major Scale Melody"
)

# Export to MIDI using music21's built-in functionality
score.write('midi', fp='simple_melody.mid')

print("✓ Generated simple_melody.mid")
print(f"  Title: {score.metadata.title}")
print(f"  Duration: {score.duration.quarterLength} quarter notes")
print(f"  Using music21 library for robust music theory support")
