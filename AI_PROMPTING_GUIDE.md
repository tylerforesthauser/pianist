# AI Prompting Guide (schema-aligned)

Your model should output **one JSON object** that validates against Pianist’s schema.

## Prompt structure: system + user (recommended)
For best reliability, split prompting into:
- **System prompt**: stable “rules of the game” (format + schema constraints).
- **User prompt**: the musical brief (style, form, length, key, tempo, etc.).

This typically improves **schema adherence** and reduces output drift compared to a single combined prompt.

Note: while Pianist’s parser can extract JSON from fenced ```json blocks and other surrounding text, you’ll get the most reliable results by instructing the model to output **raw JSON only**.

## Musical goals (what to ask the model to do)
- **Form**: use a clear formal structure (binary, ternary/ABA, rondo, sonata-ish, theme & variations, dance/character pieces, or multi-movement works).
- **Length**: for substantial works, aim for ~100–500+ beats and use the chosen form to organize material (see the Formal Structures section below).
- **Motif development**: introduce a short motif early, then develop it via transposition, inversion, augmentation/diminution, fragmentation, and sequence.
- **Dynamics**: use `velocity` to shape phrases (p → mf → f and back), with local accents and larger-scale crescendi/decrescendi.
- **Sections**: mark formal sections using the `section` field (e.g. `"exposition"`, `"A"`, `"development"`, `"B"`) for clarity.
- **Contrast + transitions**: create contrast between sections (key, texture, mood, register) and use transitions to connect them.
- **Harmony/texture**: aim for right-hand melody + left-hand accompaniment as a default texture, with occasional chords/cadences.
- **Timing**: keep timing consistent (start/duration in beats); allow chords via multiple pitches in a single event.

Representation:
- Use a single Piano track.
- Use `groups` (preferred) or `notes` so every note is labeled with `hand` (`"lh"`/`"rh"`) and optional `voice` (1–4).

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

### System prompt (copy/paste)
```
You are a music composition generator. Output MUST be valid JSON only.

Hard requirements:
- Output ONLY a single JSON object. No markdown. No explanations.
- The JSON must validate against this schema:
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

Pitch format:
- Use MIDI numbers (0–127) OR scientific pitch strings ("C4", "F#3", "Bb2").

Time units:
- start/duration are in beats, where 1 beat == a quarter note.

Output quality:
- Prefer events sorted by start time.
```

### User prompt (copy/paste)
```
Compose a piano piece. Requirements:

Musical goals:
- Use a clear formal structure (ABA/ternary recommended).
- For longer pieces, aim for ~100–500+ beats and organize material by form.
- Introduce a short motif early, then develop it (transpose/invert/augment/fragment/sequence) throughout.
- Use dynamics via velocity (p -> mf -> f and back) to shape phrases and larger sections.
- Mark formal sections using the `section` field (e.g., "exposition", "A", "development", "B").
- Create contrast between sections (keys, textures, moods) and use transitions to connect them.
- Keep timing consistent: start/duration in beats; allow chords by multiple pitches.

Representation:
- Use a single Piano track.
- Use `groups` (preferred) or `notes` so every note is labeled with `hand` ("lh"/"rh") and optional `voice` (1-4).
```

## Tips that help models succeed
- Keep events **sorted by `start`** (not required, but reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start`.
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation.
