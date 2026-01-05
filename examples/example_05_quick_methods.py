"""
Example: Quick method to generate MIDI from notes or simple string.
"""

from pianist import Note, MIDIGenerator, MusicParser

# Method 1: Quick generation from a list of notes
print("Method 1: From note list")
notes = [
    Note.from_name("C", 4, 1.0),
    Note.from_name("D", 4, 1.0),
    Note.from_name("E", 4, 1.0),
    Note.from_name("F", 4, 1.0),
    Note.from_name("G", 4, 2.0),
]

MIDIGenerator.from_notes(
    notes,
    "quick_melody.mid",
    title="Quick Melody",
    tempo=120
)
print("✓ Generated quick_melody.mid")

# Method 2: Parse a simple melody string
print("\nMethod 2: From simple string")
parser = MusicParser()
composition = parser.parse_simple_melody(
    "C4:1.0 E4:1.0 G4:1.0 E4:1.0 C4:2.0",
    title="C Major Arpeggio"
)

generator = MIDIGenerator(composition)
generator.generate("simple_string_melody.mid")
print("✓ Generated simple_string_melody.mid")

# Method 3: Using MIDI pitch numbers instead of note names
print("\nMethod 3: Using MIDI pitch numbers")
composition = parser.parse_simple_melody(
    "60:0.5 62:0.5 64:0.5 65:0.5 67:1.0",
    title="Numeric Scale"
)

generator = MIDIGenerator(composition)
generator.generate("numeric_melody.mid")
print("✓ Generated numeric_melody.mid")

print("\n✓ All quick examples generated successfully!")
