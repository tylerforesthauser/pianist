# Pianist 🎹

A Python framework for converting AI model responses into functional MIDI files. Pianist provides a simple parser that works seamlessly with the industry-standard **music21** library for robust music theory and MIDI generation.

## Key Features

- 🎼 **Built on music21**: Leverages the professional-grade music21 library for music theory and MIDI generation
- 📝 **AI Response Parsing**: Custom parser converts structured AI responses (JSON/dict) into music21 objects
- 🎵 **Simple API**: Easy-to-use interface for parsing AI-generated compositions
- 🎹 **Professional Output**: Generate high-quality MIDI files using music21's robust export functionality
- 🔄 **Full music21 Access**: Use all of music21's powerful features (transformations, analysis, etc.)

## Why music21?

Instead of reimplementing music theory from scratch, Pianist uses **music21** - the most comprehensive and well-tested music library for Python. This provides:

- ✅ Professional-grade music theory (notes, scales, chords, keys, meters)
- ✅ Robust MIDI file generation
- ✅ Built-in transformations (transpose, invert, retrograde, etc.)
- ✅ Music analysis and manipulation tools
- ✅ Extensive documentation and community support
- ✅ Actively maintained since 2008

## Installation

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

## Quick Start

### Simple Melody

```python
from pianist import MusicParser

# Create parser
parser = MusicParser()

# Parse a simple melody
score = parser.parse_simple_melody(
    "C4:1.0 D4:1.0 E4:1.0 F4:1.0 G4:2.0",
    title="C Major Scale"
)

# Export to MIDI using music21
score.write('midi', fp='output.mid')
```

### AI Response Parsing

```python
from pianist import MusicParser

# AI model output as structured data
ai_response = {
    "title": "Sonata in C Major",
    "composer": "AI Assistant",
    "tempo": 120,
    "time_signature": [4, 4],
    "sections": [{
        "name": "Exposition",
        "phrases": [{
            "name": "First Theme",
            "motifs": ["C4:1.0 E4:1.0 G4:1.0 C5:2.0"]
        }]
    }]
}

# Parse and generate MIDI
parser = MusicParser()
score = parser.parse_composition(ai_response)
score.write('midi', fp='ai_composition.mid')

print(f"Generated: {score.metadata.title}")
print(f"Duration: {score.duration.quarterLength} quarter notes")
```

### Using music21 Features Directly

```python
from pianist import MusicParser
from music21 import stream, chord

# Parse AI response
parser = MusicParser()
melody = parser.parse_motif("C4:1.0 E4:1.0 G4:1.0")

# Use music21's built-in transformations
transposed = melody.transpose(2)  # Up a whole step
inverted = melody.invert()  # Melodic inversion

# Use music21's chord library
c_major = chord.Chord('C4 E4 G4')
c_major.quarterLength = 4.0

# Combine into a score
score = stream.Score()
score.append(melody)
score.append(transposed)

# Export
score.write('midi', fp='transformed.mid')
```

## Note Format Specification

The parser supports flexible notation for describing notes:

### Note Formats
- `"C4:1.0:64"` - Note name, duration (quarter lengths), velocity (0-127)
- `"C4:1.0"` - Default velocity (64)
- `"C4"` - Default duration (1.0) and velocity (64)
- `"60:1.0:64"` - MIDI pitch number format
- Supports sharps (`C#4`), flats (`D-4`), and Unicode symbols

### Chord Formats
- `"C4maj:2.0:80"` - Root note, chord type, duration, velocity
- `"Amin"` - A minor chord with defaults
- Supported types: `maj`, `min`, `dim`, `aug`, `maj7`, `min7`, `dom7`, `dim7`, `sus2`, `sus4`

## Architecture

```
pianist/
├── __init__.py         # Package exports (music21 + MusicParser)
└── parser.py           # Custom parser for AI responses

Uses music21 for:
- Note, Chord, Scale classes
- Stream, Part, Score for composition
- MIDI export functionality
- Music theory and transformations
```

## AI Integration

### Prompt Template for AI Models

```
Create a piano composition in JSON format:

{
  "title": "Your Composition Title",
  "composer": "Your Name",
  "tempo": 120,
  "time_signature": [4, 4],
  "sections": [{
    "name": "Section Name",
    "repeat": false,
    "phrases": [{
      "name": "Phrase Name",
      "motifs": ["C4:1.0:64 E4:1.0:70 G4:1.0:80"]
    }]
  }]
}

Note format: NoteName+Octave:Duration:Velocity
- NoteName: C, C#, D-, D, etc.
- Octave: 0-8 (C4 = middle C)
- Duration: in quarter notes (1.0 = quarter note)
- Velocity: 0-127 (64 = mezzo-forte)
```

### Processing AI Output

```python
import json
from pianist import MusicParser

# Get response from AI model
ai_response_text = model.generate(prompt)
ai_data = json.loads(ai_response_text)

# Parse and generate MIDI
parser = MusicParser()
score = parser.parse_composition(ai_data)
score.write('midi', fp='ai_composition.mid')
```

## Examples

Check the `examples/` directory for working demonstrations:

1. **example_01_simple_melody.py** - Basic melody parsing
2. **example_02_motif_transformations.py** - Using music21 transformations
3. **example_03_ai_parsing.py** - Full AI response parsing
4. **example_04_music21_integration.py** - Combining parser with music21 features

Run examples:

```bash
cd examples
python example_01_simple_melody.py
```

## Testing

Run the test suite:

```bash
pip install -r requirements-dev.txt
pytest
```

All tests use music21's robust music theory implementation.

## Dependencies

- **music21>=9.0.0**: Professional music theory and MIDI generation library
- **pytest>=7.0.0** (dev): Testing framework

## Why This Approach?

This framework follows best practices by:

1. **Using existing libraries**: Built on music21 instead of reimplementing music theory
2. **Separation of concerns**: Custom parser for AI responses, music21 for music theory
3. **Professional output**: Leverages music21's well-tested MIDI export
4. **Extensibility**: Full access to music21's powerful features
5. **Maintainability**: Smaller codebase focused on AI response parsing

## Use Cases

- **AI Music Composition**: Enable LLMs to compose music through structured responses
- **Music Education**: Generate musical examples for teaching
- **Algorithmic Composition**: Build rule-based composition systems
- **Music Prototyping**: Quickly sketch musical ideas programmatically

## Contributing

Contributions are welcome! The framework is intentionally minimal - we focus on parsing AI responses while music21 handles the music theory.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built on [music21](https://web.mit.edu/music21/) - the comprehensive music analysis and generation toolkit
- Inspired by the need for simple AI-to-MIDI conversion
