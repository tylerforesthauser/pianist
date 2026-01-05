# AI Prompting Guide

Your model should output **one JSON object** that validates against Pianist's schema.

## Prompt Structure

For best reliability, split prompting into:
- **System prompt**: Stable "rules of the game" (format + schema constraints).
- **User prompt**: The musical brief (style, form, length, key, tempo, etc.).

This typically improves **schema adherence** and reduces output drift compared to a single combined prompt.

## Prompt Templates

### System Prompt

```
You are an expert music composition generator with deep knowledge of music theory, harmony, and classical composition. Output MUST be valid JSON only.

Hard requirements:
- Output ONLY a single JSON object. No markdown. No explanations. No fenced code blocks.
- The JSON must validate against this schema:
  - title: string
  - bpm: number (20-300 recommended)
  - time_signature: { numerator: int, denominator: 1|2|4|8|16|32 }
  - key_signature: optional string (e.g., "C", "Gm", "F#", "Bb")
  - ppq: int (suggest 480)
  - tracks: [{ name, program (0=piano), channel, events }]
  - At least one track is required. Default to a single Piano track (program: 0) if not specified.
  - events:
    - note: { type:"note", start: beats>=0, duration: beats>0, velocity: 1-127,
              pitch content in ONE of:
                - groups: [{ hand:"lh|rh", voice?: 1..4, pitches:[ "C4" | 60 | ... ] }, ...] (PREFERRED: enables hand/voice labeling)
                - notes:  [{ hand:"lh|rh", voice?: 1..4, pitch:  "C4" | 60 }, ...] (PREFERRED: enables hand/voice labeling)
                - legacy pitches/pitch (allowed but not recommended: lacks hand/voice labels)
              optional: motif/section/phrase }
    - pedal: { type:"pedal", start, duration, value 0-127 }

Pitch format:
- Use MIDI numbers (0–127) OR scientific pitch strings ("C4", "F#3", "Bb2").

Time units:
- start/duration are in beats, where 1 beat == a quarter note.

Music theory and compositional principles (CRITICAL):
- Functional harmony: Use proper chord progressions following tonal function (I, ii, iii, IV, V, vi, vii°). Establish clear tonic-dominant relationships. Use secondary dominants (V/V, V/vi, etc.) and borrowed chords (modal mixture) for color.
- Voice leading: Maintain smooth, stepwise motion when possible. Avoid parallel fifths and octaves. Resolve leading tones upward (ti→do) and sevenths downward. Keep common tones between chords when possible.
- Cadences: Use authentic cadences (V→I) at phrase endings, half cadences (ending on V) for continuation, plagal cadences (IV→I) for closure, and deceptive cadences (V→vi) for surprise.
- Dissonance and resolution: Properly prepare and resolve dissonances (suspensions, appoggiaturas, passing tones). Use non-chord tones (passing, neighbor, escape, anticipation) to create melodic interest while maintaining harmonic clarity.
- Harmonic rhythm: Vary chord change frequency—faster in active sections, slower in lyrical passages. Avoid changing chords on every beat unless creating specific effects.
- Modulation: When modulating, use pivot chords, common-tone modulations, or direct modulations with proper preparation. Return to the home key for structural closure.
- Counterpoint: When multiple voices are present, maintain independence while respecting harmonic function. Use contrary motion, avoid voice crossing, and maintain appropriate spacing between voices.
- Form and structure: Adhere to established formal principles (binary, ternary, sonata, etc.). Use clear phrase structure (typically 4, 8, or 16 beats), with antecedent-consequent relationships. Create larger-scale coherence through motivic development and key relationships.
- Texture: Balance melody and accompaniment. Left hand typically provides harmonic foundation (bass + chord tones), right hand carries melody. Vary texture between sections (homophonic, polyphonic, monophonic).
- Register and spacing: Use appropriate spacing between hands (avoid excessive gaps or overlaps). Utilize the full range of the piano effectively, with clear bass and treble separation.

Output quality:
- Prefer events sorted by start time (not required, but reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start` time.
- Ensure all harmonies are complete and properly voiced.
- Maintain consistent key centers within sections unless intentionally modulating.
- Use the `section` annotation field liberally to mark formal divisions—it helps organize thinking even if it doesn't affect playback.
```

### User Prompt Template

**Note:** Replace all `{{VARIABLE}}` placeholders with your specific values. The first section below requires customization; other sections are guidelines you can adjust as needed.

```
Compose a piano piece. Requirements:

=== COMPOSITION SPECIFICATIONS (REQUIRED - CUSTOMIZE THESE) ===
- Title: {{"Morning Sketch"}} or {{"Sonata in C Minor"}}
- Form: {{binary}} | {{ternary/ABA}} | {{rondo}} | {{sonata}} | {{theme and variations}} | {{free-form}}
- Length: {{~64 beats}} or {{~200 beats}} (Typical ranges: binary/ternary 32-128, sonata 150-300+, multi-movement 200-500+)
- Key: {{"C"}} | {{"Gm"}} | {{"F#"}} | {{"Bb"}}
- Tempo: {{84}} | {{120}} | {{160}} (BPM)
- Time signature: {{4/4}} | {{3/4}} | {{6/8}}
- Style/Character: {{lyrical}} | {{dramatic}} | {{playful}} | {{contemplative}}

=== MUSICAL GOALS ===
- Introduce a short motif early, then develop it throughout (transpose, invert, augment, diminish, fragment, sequence).
- Use dynamics via velocity (p → mf → f and back) to shape phrases and larger sections.
- Mark formal sections using the `section` field (e.g., "exposition", "A", "development", "B", "recapitulation").
- Create contrast between sections (keys, textures, moods, registers) and use transitions to connect them.
- For longer works, plan the overall structure first, then fill in details section by section.
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation for interest.

=== HARMONY AND VOICE LEADING ===
- Establish clear tonic-dominant relationships and use proper cadences (authentic V→I, half cadences ending on V, plagal IV→I, deceptive V→vi).
- Maintain smooth voice leading: prefer stepwise motion, resolve leading tones and chordal sevenths properly, avoid parallel fifths/octaves.
- Vary harmonic rhythm appropriately: faster changes in active sections, slower in lyrical passages.
- When modulating, use pivot chords or prepare modulations clearly; return to home key for structural closure.

=== MELODY AND COUNTERPOINT ===
- Create melodic lines with clear direction and contour. Use non-chord tones (passing, neighbor, suspension) for interest while maintaining harmonic clarity.
- If using multiple voices, maintain independence with contrary motion where appropriate, proper spacing, and avoid voice crossing.

=== TEXTURE AND VOICING ===
- Left hand: provide harmonic foundation (bass line + chord tones in appropriate register).
- Right hand: carry melody with supporting harmony when needed.
- Balance melody and accompaniment; vary texture between sections.
- Use a single Piano track with `groups` (preferred) or `notes` so every note is labeled with `hand` ("lh"/"rh") and optional `voice` (1-4).
```

## Schema Reference

### High-Level Structure

- Top level: `title`, `bpm`, `time_signature`, optional `key_signature`, `ppq`, `tracks`
- Each `track` has `name`, `program` (0=piano), `channel`, and `events`
- Each `event` is either:
  - `type: "note"` with `start` (beats), `duration` (beats), `velocity`, and pitch content in ONE of:
    - **Preferred**: `groups` (sub-chords with shared `hand`/`voice`)
    - **Preferred**: `notes` (per-note `hand`/`voice`)
    - Legacy: `pitches` / `pitch` (no per-note labeling)
  - `type: "pedal"` with `start`, `duration`, optional `value`

Optional annotation fields (do not affect rendering): `motif`, `section`, `phrase`.

### Pitch Format

You may provide pitches as:
- MIDI numbers (0–127), or
- scientific pitch strings (`"C4"`, `"F#3"`, `"Bb2"`)

Internally Pianist validates and converts pitches to MIDI numbers.

### Hand/Voice Labeling

For piano writing, keep a **single Piano track** and label each generated note (or sub-chord) with:
- `hand`: `"lh"` or `"rh"` (required in `notes` / `groups`)
- `voice`: optional integer 1–4 (useful for downstream notation/analysis)

## Example JSON

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

## Formal Structures Reference

This section provides reference information about classical musical forms to help you choose what to request in your prompts. These forms are **creative frameworks**, not rigid templates—you can adapt them to your musical vision.

### Common Forms

- **Binary (A-B)**: Two contrasting sections, typically 16-32 beats each. B section may modulate, returns to tonic.
- **Ternary (A-B-A)**: Main theme, contrasting middle section, return of A (often varied). B is typically 1.5-2x length of A.
- **Rondo (A-B-A-C-A)**: Recurring theme (A) alternates with contrasting episodes (B, C). Patterns: ABACA (5-part) or ABACABA (7-part).
- **Sonata Form**: Exposition (first theme in tonic, second theme in dominant), Development (fragments, modulations, tension), Recapitulation (both themes in tonic). Typically 150-300+ beats.
- **Theme and Variations**: Clear theme (16-32 beats) followed by 3-8+ variations transforming it through ornamentation, mode changes, tempo, texture, harmony, etc.

### Multi-Movement Works

- **Sonata**: 3-4 movements (fast-slow-dance-fast) with contrasting characters.
- **Suite**: Collection of dance movements (allemande, courante, sarabande, gigue), each in binary/ternary form.

### Character Pieces

- **Nocturne**: Slow-moderate, lyrical, song-like, often ternary with ornamented return.
- **Ballade**: Narrative character, free-form or through-composed, may be extended (200+ beats).
- **Étude**: Focus on technical challenge, often ternary or binary form.

### Planning Longer Works (100-500+ beats)

When requesting longer compositions, consider:
- **Formal structures**: Sonata form, multi-movement works, or extended theme and variations naturally create longer pieces.
- **Motif development**: Request 2-3 contrasting motifs that can be developed through sequences, modulations, and counterpoint.
- **Section lengths**: Binary/ternary forms typically yield 32-128 beats; sonata form 150-300+; multi-movement works 200-500+.
- **Section marking**: The model will use the `section` field to mark formal divisions (e.g., "exposition", "development", "recapitulation").
- **Contrast and return**: Request different keys, textures, and moods between sections, with transitions and returns to earlier material.
- **Dynamic arcs**: Request that dynamics shape larger arcs, building to climaxes and creating tension and release.
