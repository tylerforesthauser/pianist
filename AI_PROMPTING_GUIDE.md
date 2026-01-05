# AI Prompting Guide for Pianist

This guide helps you craft effective prompts for AI models to generate piano compositions using the Pianist framework.

## Basic Prompt Template

```
Create a piano composition in JSON format with the following structure:

{
  "title": "Your Composition Title",
  "composer": "AI Assistant",
  "tempo": 120,
  "time_signature": [4, 4],
  "key_signature": "C major",
  "form": "Sonata/Rondo/Theme and Variations",
  "sections": [
    {
      "name": "Section Name",
      "repeat": false,
      "phrases": [
        {
          "name": "Phrase Name",
          "motifs": [
            "Note specifications here"
          ]
        }
      ]
    }
  ]
}

Note format: NoteName+Octave:Duration:Velocity
- NoteName: C, C#, Db, D, etc. (use sharps or flats)
- Octave: 0-8 (middle C is C4, concert A is A4)
- Duration: in beats (1.0 = quarter note in 4/4 time)
- Velocity: 0-127 (48=piano, 64=mezzo-forte, 80=forte, 96=fortissimo)

Example: "C4:1.0:64 E4:1.0:70 G4:1.0:80 C5:2.0:64"
```

## Example Prompts

### 1. Simple Scale Exercise

```
Create a C major scale exercise for piano practice.
Use 4/4 time at 120 BPM.
Ascending scale from C4 to C5, then descending back to C4.
Each note should be a quarter note (1.0 beat).
```

### 2. Classical Sonata Movement

```
Compose a short sonata movement in sonata form with:
- Exposition (repeated): First theme in C major, second theme in G major
- Development: Explore the first theme with modulations
- Recapitulation: Both themes return in C major

Use 4/4 time at 120 BPM. Create clear melodic motifs that are developed throughout.
Include dynamics (vary velocity values between 48-96).
```

### 3. Jazz-Inspired Piece

```
Create a jazz-inspired piano piece with:
- 4/4 swing feel at 140 BPM
- Use chromatic passing tones and blue notes
- Include syncopated rhythms (use durations like 0.75, 0.25, 0.5)
- Build on a II-V-I progression in C major

Structure as: Intro, Theme, Variation, Coda
```

### 4. Minimalist Composition

```
Compose a minimalist piano piece inspired by Philip Glass:
- Use repetitive patterns that gradually evolve
- 4/4 time at 180 BPM (fast tempo)
- Build on simple arpeggios (e.g., C-E-G repeated)
- Slowly add and remove notes to create gradual changes
- Use consistent velocity (64) for a mechanical feel
```

### 5. Romantic Character Piece

```
Create a Romantic-era character piece (like a Chopin Nocturne):
- 3/4 time (waltz) at 70 BPM (rubato feel)
- Key: F minor
- Lyrical melody with expressive dynamics (velocity range 40-110)
- Include ornamentations (use shorter note durations for grace notes)
- Structure: A-B-A form with coda
```

## Advanced Techniques

### Motif Development

Ask the AI to:
- **Transpose** motifs to different keys
- **Invert** motifs (flip the melodic contour)
- **Augment** motifs (double note durations)
- **Diminish** motifs (halve note durations)
- **Retrograde** motifs (play backwards)

Example prompt:
```
Create a composition that introduces a 4-note motif in the first phrase,
then develop it through transposition, inversion, and rhythmic augmentation
in subsequent phrases.
```

### Using Chords

For harmonic accompaniment, you can specify chords directly in motifs:

Example:
```
Create a hymn-like piece with block chords:
- Use four-note chords (specify all notes at the same time with same duration)
- Progression: I-IV-V-I in C major
- Each chord held for 2 beats
```

### Dynamic Expression

Use velocity to create musical expression:
- **Crescendo**: Gradually increase velocity (e.g., 64 → 80 → 96)
- **Diminuendo**: Gradually decrease velocity
- **Accent**: Single note with higher velocity
- **Sforzando**: Sudden loud note (velocity 100+)

Example prompt:
```
Include a dramatic crescendo in the development section,
building from piano (velocity 48) to fortissimo (velocity 112).
```

### Form and Structure

Common classical forms to request:
- **Binary (AB)**: Two contrasting sections
- **Ternary (ABA)**: Return to opening after contrast
- **Rondo (ABACA)**: Recurring theme with episodes
- **Theme and Variations**: Present theme, then multiple variations
- **Sonata**: Exposition, Development, Recapitulation

## Tips for Better Results

1. **Be Specific**: Provide clear tempo, time signature, and key
2. **Use Musical Terms**: AI models understand standard music terminology
3. **Request Repetition**: Mark sections with `"repeat": true` for classical forms
4. **Vary Velocity**: Ask for dynamic contrast to make music more expressive
5. **Name Sections**: Give meaningful names to help AI understand structure
6. **Start Simple**: Begin with shorter pieces and gradually increase complexity
7. **Iterate**: Generate, listen, and refine your prompts based on results

## Example Complete Prompt

```
Create a short piano piece in C major with the following specifications:

Title: "Morning Meditation"
Tempo: 80 BPM (calm and peaceful)
Time Signature: 4/4
Form: ABA (Ternary)

Section A (repeated):
- Gentle melody starting on C4, moving stepwise
- Soft dynamics (velocity 48-64)
- Quarter and half notes, creating a flowing feel
- 8 measures

Section B:
- Move to the relative minor (A minor)
- Slightly more rhythmic activity with eighth notes
- Moderate dynamics (velocity 64-80)
- 8 measures

Section A (return):
- Same as first section but end with a perfect authentic cadence
- Very soft ending (velocity 40)

Use the JSON format with sections, phrases, and motifs clearly defined.
```

## Processing AI Output

Once you have the JSON response from your AI model:

```python
import json
from pianist import MusicParser, MIDIGenerator

# Load AI response
ai_response = json.loads(ai_output_text)

# Parse into composition
parser = MusicParser()
composition = parser.parse_composition(ai_response)

# Generate MIDI file
generator = MIDIGenerator(composition)
generator.generate("output.mid")

print(f"Generated: {composition.title}")
print(f"Duration: {composition.duration_in_seconds():.1f} seconds")
print(f"Sections: {len(composition.sections)}")
```

## Common Issues and Solutions

### Issue: AI generates invalid note names
**Solution**: Remind the AI to use standard note names (C, C#, Db, D, etc.)

### Issue: Durations don't align with time signature
**Solution**: Specify that phrase durations should align with measures

### Issue: Too repetitive or too random
**Solution**: Ask for specific balance between unity (repetition) and variety

### Issue: Unmusical intervals
**Solution**: Request stepwise motion or specify interval constraints

### Issue: Missing dynamics
**Solution**: Explicitly request varied velocity values for expression

## Further Reading

- See `examples/` directory for working code examples
- Check `README.md` for API reference
- Music theory concepts in `pianist/music_theory.py`
- Composition structures in `pianist/composition.py`
