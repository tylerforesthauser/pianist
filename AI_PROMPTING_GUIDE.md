# AI Prompting Guide (schema-aligned)

Your model should output **one JSON object** that validates against Pianist’s schema.

## Musical goals (what to ask the model to do)
- **Form**: ABA, rondo, theme & variations, sonata-ish exposition/development/recap (loosely).
- **Motif development**: introduce a short motif early, then vary it via transposition, inversion, augmentation/diminution, fragmentation, sequence.
- **Harmony/texture**: right-hand melody + left-hand accompaniment, occasional chords, cadences.
- **Dynamics**: use `velocity` to shape phrases (accent, crescendo, diminuendo).

## Output schema (high level)

- Top level: `title`, `bpm`, `time_signature`, optional `key_signature`, `ppq`, `tracks`
- Each `track` has `name`, `program` (0=piano), `channel`, and `events`
- Each `event` is either:
  - `type: "note"` with `start` (beats), `duration` (beats), `pitches` (list of notes), `velocity`
  - `type: "pedal"` with `start`, `duration`, optional `value`

Optional annotation fields (do not affect rendering): `motif`, `section`, `phrase`, `hand`.

### Pitch format
You may provide pitches as:
- MIDI numbers (0–127), or
- scientific pitch strings (`"C4"`, `"F#3"`, `"Bb2"`)

Internally Pianist validates and converts pitches to MIDI numbers.

## Canonical JSON example

```json
{
  "title": "Morning Sketch",
  "bpm": 84,
  "time_signature": { "numerator": 4, "denominator": 4 },
  "key_signature": "C",
  "ppq": 480,
  "tracks": [
    {
      "name": "Piano",
      "program": 0,
      "channel": 0,
      "events": [
        { "type": "note", "start": 0, "duration": 1, "pitches": ["C4"], "velocity": 72, "hand": "rh", "motif": "A", "section": "A" },
        { "type": "note", "start": 1, "duration": 1, "pitches": ["E4"], "velocity": 76, "hand": "rh", "motif": "A", "section": "A" },
        { "type": "note", "start": 2, "duration": 1, "pitches": ["G4"], "velocity": 80, "hand": "rh", "motif": "A", "section": "A" },

        { "type": "note", "start": 0, "duration": 2, "pitches": ["C3", "G3"], "velocity": 60, "hand": "lh", "section": "A" },
        { "type": "note", "start": 2, "duration": 2, "pitches": ["F3", "C4"], "velocity": 60, "hand": "lh", "section": "A" },

        { "type": "pedal", "start": 0, "duration": 4, "value": 127, "section": "A" }
      ]
    }
  ]
}
```

## Prompt template (copy/paste)

```
Compose a piano piece. Requirements:

- Output ONLY a single JSON object (no markdown, no explanation).
- Use this schema:
  - title: string
  - bpm: number (20-300 recommended)
  - time_signature: { numerator: int, denominator: 1|2|4|8|16|32 }
  - key_signature: optional string (e.g., "C", "Gm", "F#", "Bb")
  - ppq: int (suggest 480)
  - tracks: [{ name, program, channel, events }]
  - events:
    - note: { type:"note", start: beats>=0, duration: beats>0, pitches: [ "C4" | 60 | ... ], velocity: 1-127, optional: hand/motif/section/phrase }
    - pedal: { type:"pedal", start, duration, value 0-127 }

Musical goals:
- Use a clear form (ABA recommended).
- Introduce a short motif in A, then develop it (transpose/invert/augment) in B.
- Use dynamics via velocity (p -> mf -> f and back).
- Keep timing consistent: start/duration in beats; allow chords by multiple pitches.
```

## Tips that help models succeed
- Keep events **sorted by `start`** (not required, but reduces mistakes).
- For chords, use `pitches: ["C4","E4","G4"]` at the same `start`.
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation.
