# Pianist 🎹

A Python framework for converting AI model responses into functional MIDI files. Pianist enables AI models to compose piano music using music theory concepts, classical musical forms, and motif development.

## Features

- 🎼 **Music Theory Primitives**: Notes, scales, chords, time signatures, and tempo
- 🎵 **Composition Structures**: Motifs, phrases, sections, and complete compositions
- 🔄 **Motif Transformations**: Transpose, invert, augment, diminish, and retrograde
- 📝 **AI Response Parsing**: Convert structured text/JSON from AI models into music
- 🎹 **MIDI Generation**: Export compositions as playable MIDI files
- 🎼 **Classical Forms**: Support for sonata, rondo, theme & variations, and more

## Installation

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

## Quick Start

### Method 1: Simple Note List

```python
from pianist import Note, MIDIGenerator

# Create notes
notes = [
    Note.from_name("C", 4, 1.0),  # C4, 1 beat duration
    Note.from_name("E", 4, 1.0),
    Note.from_name("G", 4, 1.0),
    Note.from_name("C", 5, 2.0),
]

# Generate MIDI file
MIDIGenerator.from_notes(notes, "output.mid", title="C Major Arpeggio", tempo=120)
```

### Method 2: Simple String Parsing

```python
from pianist import MusicParser, MIDIGenerator

parser = MusicParser()
composition = parser.parse_simple_melody(
    "C4:1.0 D4:1.0 E4:1.0 F4:1.0 G4:2.0",
    title="Simple Scale"
)

generator = MIDIGenerator(composition)
generator.generate("scale.mid")
```

### Method 3: Full Composition with AI Response

```python
from pianist import MusicParser, MIDIGenerator

# AI model output as structured data
ai_response = {
    "title": "Sonata in C Major",
    "composer": "AI Assistant",
    "tempo": 120,
    "time_signature": [4, 4],
    "key_signature": "C major",
    "form": "Sonata",
    "sections": [
        {
            "name": "Exposition",
            "repeat": True,
            "phrases": [
                {
                    "name": "First Theme",
                    "motifs": [
                        "C4:1.0 E4:1.0 G4:1.0 C5:2.0",
                        "B4:0.5 A4:0.5 G4:1.0 F4:1.0"
                    ]
                }
            ]
        },
        {
            "name": "Development",
            "phrases": [
                {
                    "name": "Theme Variation",
                    "motifs": ["E4:0.5 G4:0.5 B4:0.5 D5:0.5"]
                }
            ]
        }
    ]
}

# Parse and generate MIDI
parser = MusicParser()
composition = parser.parse_composition(ai_response)
generator = MIDIGenerator(composition)
generator.generate("sonata.mid")
```

## Core Concepts

### Music Theory Primitives

```python
from pianist import Note, Scale, ScaleType, Chord, ChordType

# Create notes
note = Note(pitch=60, duration=1.0, velocity=64)  # MIDI format
note = Note.from_name("C", 4, 1.0, 64)  # Note name format

# Create scales
c_major = Scale(root=60, scale_type=ScaleType.MAJOR)
notes = c_major.get_notes(octaves=2)  # Get two octaves

# Create chords
c_major_chord = Chord(root=60, chord_type=ChordType.MAJOR)
pitches = c_major_chord.get_notes()  # [60, 64, 67] = C, E, G
```

### Motif Development

```python
from pianist import Motif, Note

# Create a motif
original = Motif(notes=[
    Note.from_name("C", 4, 0.5),
    Note.from_name("E", 4, 0.5),
    Note.from_name("G", 4, 1.0),
])

# Transform the motif
transposed = original.transpose(2)        # Up a whole step
inverted = original.invert(axis=64)       # Invert around E4
retrograde = original.retrograde()        # Play backwards
augmented = original.augment(2.0)         # Double note durations
diminished = original.diminish(2.0)       # Halve note durations
```

### Composition Structure

```python
from pianist import Motif, Phrase, Section, Composition, Tempo, TimeSignature

# Build hierarchy: Motif → Phrase → Section → Composition
motif = Motif(notes=[...])
phrase = Phrase(motifs=[motif], name="Opening")
section = Section(phrases=[phrase], name="Exposition", repeat=True)

composition = Composition(
    title="My Composition",
    sections=[section],
    tempo=Tempo(120),
    time_signature=TimeSignature(4, 4),
    composer="AI Composer",
    form="Sonata"
)
```

## Note Format Specification

The parser supports multiple formats for specifying notes:

### Note Name Format
- `"C4:1.0:64"` - Note name, octave, duration (beats), velocity (0-127)
- `"C4:1.0"` - Default velocity (64)
- `"C4"` - Default duration (1.0) and velocity (64)
- Supports sharps: `"C#4"`, `"F#5"`
- Supports flats: `"Db4"`, `"Bb3"`

### MIDI Pitch Format
- `"60:1.0:64"` - MIDI pitch (0-127), duration, velocity
- `"60:1.0"` - Default velocity
- `"60"` - Default duration and velocity

### Chord Format
- `"C4maj:2.0:80"` - Root note, chord type, duration, velocity
- `"Amin"` - A minor chord with defaults
- Supported types: `maj`, `min`, `dim`, `aug`, `maj7`, `min7`, `dom7`, `dim7`, `sus2`, `sus4`

## Examples

Check the `examples/` directory for complete examples:

- `example_01_simple_melody.py` - Basic melody creation
- `example_02_motif_transformations.py` - Motif development techniques
- `example_03_ai_parsing.py` - Parsing AI-generated compositions
- `example_04_chords.py` - Working with chords and harmony
- `example_05_quick_methods.py` - Quick generation methods

Run examples:

```bash
cd examples
python example_01_simple_melody.py
```

## AI Model Integration

### Prompt Template for AI Models

```
Create a piano composition in the following JSON format:

{
  "title": "Your Composition Title",
  "composer": "Your Name",
  "tempo": 120,
  "time_signature": [4, 4],
  "key_signature": "C major",
  "form": "Sonata/Rondo/Theme and Variations",
  "sections": [
    {
      "name": "Section Name (e.g., Exposition, Development)",
      "repeat": true/false,
      "phrases": [
        {
          "name": "Phrase Name",
          "motifs": [
            "C4:1.0 E4:1.0 G4:1.0 C5:2.0"
          ]
        }
      ]
    }
  ]
}

Notes are specified as: NoteName+Octave:Duration:Velocity
- NoteName: C, C#, Db, D, etc.
- Octave: 0-8 (middle C is C4)
- Duration: in beats (1.0 = quarter note at 4/4)
- Velocity: 0-127 (64 = mezzo-forte, 80 = forte, 48 = piano)

Example motifs:
- Scale: "C4:1.0 D4:1.0 E4:1.0 F4:1.0 G4:1.0"
- Arpeggio: "C4:0.5 E4:0.5 G4:0.5 C5:1.0"
- Melody: "E4:0.5:64 D4:0.5:64 C4:1.0:80"
```

### Processing AI Response

```python
import json
from pianist import MusicParser, MIDIGenerator

# Get response from AI model
ai_response_text = model.generate(prompt)
ai_data = json.loads(ai_response_text)

# Parse and generate MIDI
parser = MusicParser()
composition = parser.parse_composition(ai_data)
generator = MIDIGenerator(composition)
generator.generate("ai_composition.mid")

print(f"Generated: {composition.title}")
print(f"Duration: {composition.duration_in_seconds():.2f} seconds")
```

## Testing

Run the test suite:

```bash
pip install -r requirements-dev.txt
pytest
```

Run with coverage:

```bash
pytest --cov=pianist --cov-report=html
```

## Architecture

```
pianist/
├── music_theory.py      # Notes, scales, chords, time signatures
├── composition.py       # Motifs, phrases, sections, compositions
├── parser.py           # Parse AI responses into structures
├── midi_generator.py   # Convert to MIDI files
└── __init__.py         # Package exports

tests/
├── test_music_theory.py
├── test_composition.py
├── test_parser.py
└── test_midi_generator.py

examples/
├── example_01_simple_melody.py
├── example_02_motif_transformations.py
├── example_03_ai_parsing.py
├── example_04_chords.py
└── example_05_quick_methods.py
```

## Use Cases

1. **AI Music Composition**: Enable LLMs to compose music by outputting structured data
2. **Music Education**: Teach composition through programmatic music creation
3. **Algorithmic Composition**: Build rule-based composition systems
4. **Music Theory Exploration**: Experiment with scales, chords, and transformations
5. **Rapid Prototyping**: Quickly sketch musical ideas in code

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [MIDIUtil](https://github.com/MarkCWirt/MIDIUtil) for MIDI file generation
- Inspired by classical music theory and composition techniques