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
  - `type: "note"` with `start` (beats), `duration` (beats), `velocity`, and pitch content in ONE of:
    - **Preferred**: `groups` (sub-chords with shared `hand`/`voice`)
    - **Preferred**: `notes` (per-note `hand`/`voice`)
    - Legacy: `pitches` / `pitch` (no per-note labeling)
  - `type: "pedal"` with `start`, `duration`, optional `value`

Optional annotation fields (do not affect rendering): `motif`, `section`, `phrase`.

### Pitch format
You may provide pitches as:
- MIDI numbers (0–127), or
- scientific pitch strings (`"C4"`, `"F#3"`, `"Bb2"`)

Internally Pianist validates and converts pitches to MIDI numbers.

### Hand/voice labeling (recommended)
For piano writing, keep a **single Piano track** and label each generated note (or sub-chord) with:
- `hand`: `"lh"` or `"rh"` (required in `notes` / `groups`)
- `voice`: optional integer 1–4 (useful for downstream notation/analysis)

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
        {
          "type": "note",
          "start": 0,
          "duration": 1,
          "velocity": 72,
          "motif": "A",
          "section": "A",
          "groups": [
            { "hand": "rh", "voice": 1, "pitches": ["C4"] },
            { "hand": "lh", "voice": 2, "pitches": ["C3", "G3"] }
          ]
        },
        {
          "type": "note",
          "start": 1,
          "duration": 1,
          "velocity": 76,
          "motif": "A",
          "section": "A",
          "groups": [{ "hand": "rh", "voice": 1, "pitches": ["E4"] }]
        },
        {
          "type": "note",
          "start": 2,
          "duration": 2,
          "velocity": 60,
          "section": "A",
          "groups": [
            { "hand": "rh", "voice": 1, "pitches": ["G4"] },
            { "hand": "lh", "voice": 2, "pitches": ["F3", "C4"] }
          ]
        },

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
    - note: { type:"note", start: beats>=0, duration: beats>0, velocity: 1-127,
              pitch content in ONE of:
                - groups: [{ hand:"lh|rh", voice?: 1..4, pitches:[ "C4" | 60 | ... ] }, ...]
                - notes:  [{ hand:"lh|rh", voice?: 1..4, pitch:  "C4" | 60 }, ...]
                - legacy pitches/pitch (allowed but not recommended)
              optional: motif/section/phrase }
    - pedal: { type:"pedal", start, duration, value 0-127 }

Musical goals:
- Use a clear form (ABA recommended).
- Introduce a short motif in A, then develop it (transpose/invert/augment) in B.
- Use dynamics via velocity (p -> mf -> f and back).
- Keep timing consistent: start/duration in beats; allow chords by multiple pitches.
```

## Tips that help models succeed
- Keep events **sorted by `start`** (not required, but reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start`.
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation.
