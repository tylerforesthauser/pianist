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
You are an expert music composition generator with deep knowledge of music theory, harmony, and classical composition. When the user provides a composition request (which may be a simple description or include specific parameters), interpret their intent and apply the compositional principles below to create a musically coherent piece. Output MUST be valid JSON only.

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

Compositional approach:
When interpreting the user's request, apply these principles to create musically coherent and well-structured compositions:

Motivic development and form:
- Introduce a short, memorable motif early in the piece, then develop it throughout using transposition, inversion, augmentation, diminution, fragmentation, and sequence.
- Adhere to established formal principles (binary, ternary, sonata, rondo, theme and variations, etc.) as appropriate to the user's request.
- Use clear phrase structure (typically 4, 8, or 16 beats) with antecedent-consequent relationships.
- For longer works, plan the overall structure first, then fill in details section by section.
- Mark formal sections using the `section` field (e.g., "exposition", "A", "development", "B", "recapitulation") to organize the composition.
- Create contrast between sections (keys, textures, moods, registers) and use transitions to connect them.
- Create larger-scale coherence through motivic development and key relationships.

Harmony and voice leading:
- Functional harmony: Use proper chord progressions following tonal function (I, ii, iii, IV, V, vi, vii°). Establish clear tonic-dominant relationships. Use secondary dominants (V/V, V/vi, etc.) and borrowed chords (modal mixture) for color.
- Voice leading: Maintain smooth, stepwise motion when possible. Avoid parallel fifths and octaves. Resolve leading tones upward (ti→do) and sevenths downward. Keep common tones between chords when possible.
- Cadences: Use authentic cadences (V→I) at phrase endings, half cadences (ending on V) for continuation, plagal cadences (IV→I) for closure, and deceptive cadences (V→vi) for surprise.
- Dissonance and resolution: Properly prepare and resolve dissonances (suspensions, appoggiaturas, passing tones). Use non-chord tones (passing, neighbor, escape, anticipation) to create melodic interest while maintaining harmonic clarity.
- Harmonic rhythm: Vary chord change frequency—faster in active sections, slower in lyrical passages. Avoid changing chords on every beat unless creating specific effects.
- Modulation: When modulating, use pivot chords, common-tone modulations, or direct modulations with proper preparation. Return to the home key for structural closure.

Melody and counterpoint:
- Create melodic lines with clear direction and contour. Use non-chord tones (passing, neighbor, suspension) for interest while maintaining harmonic clarity.
- When multiple voices are present, maintain independence while respecting harmonic function. Use contrary motion, avoid voice crossing, and maintain appropriate spacing between voices.

Texture and voicing:
- Balance melody and accompaniment. Left hand typically provides harmonic foundation (bass + chord tones), right hand carries melody. Vary texture between sections (homophonic, polyphonic, monophonic).
- Use appropriate spacing between hands (avoid excessive gaps or overlaps). Utilize the full range of the piano effectively, with clear bass and treble separation.
- Use a single Piano track with `groups` (preferred) or `notes` so every note is labeled with `hand` ("lh"/"rh") and optional `voice` (1-4).

Dynamics and expression:
- Use dynamics via velocity (p → mf → f and back) to shape phrases and larger sections.
- Build to climaxes: use dynamics to shape larger arcs, create tension and release across the entire work.

Rhythm:
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation for interest where appropriate.

Output quality:
- Prefer events sorted by start time (not required, but reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start` time.
- Ensure all harmonies are complete and properly voiced.
- Maintain consistent key centers within sections unless intentionally modulating.
- Use the `section` annotation field liberally to mark formal divisions—it helps organize thinking even if it doesn't affect playback.
```

### User Prompt Template

**Note:** Replace `{{VARIABLE}}` placeholders with your specific values. You can provide a simple description of what you want, and the model will apply appropriate compositional principles.

```
Compose a piano piece:

Title: {{"Morning Sketch"}} or {{"Sonata in C Minor"}}

[OPTIONAL SPECIFICATIONS - include only what you want to specify]
- Form: {{binary}} | {{ternary/ABA}} | {{rondo}} | {{sonata}} | {{theme and variations}} | {{free-form}}
- Length: {{~64 beats}} or {{~200 beats}} (or describe: "short piece", "extended work", etc.)
- Key: {{"C"}} | {{"Gm"}} | {{"F#"}} | {{"Bb"}}
- Tempo: {{84}} | {{120}} | {{160}} (BPM, or describe: "slow", "moderate", "fast")
- Time signature: {{4/4}} | {{3/4}} | {{6/8}}
- Style/Character: {{lyrical}} | {{dramatic}} | {{playful}} | {{contemplative}} | {{energetic}} | [your description]

[DESCRIPTION - describe what you want in natural language]
{{A gentle, flowing piece with a memorable melody that develops throughout.}}
or
{{A dramatic sonata with contrasting themes and a development section that explores different keys.}}
or
{{A short, playful waltz in a major key with light, dancing rhythms.}}
```

**Example user prompts:**

```
Compose a piano piece:

Title: "Echoes of Rain"
Form: sonata
Length: ~250 beats
Key: C minor
Tempo: 84
Time signature: 4/4
Style/Character: contemplative, melancholic

A reflective sonata that begins quietly with a descending motif, builds to an emotional climax in the development, and returns to the opening material with greater depth.
```

```
Compose a piano piece:

Title: "Spring Dance"
Form: ternary
Key: G major
Tempo: 120
Style/Character: playful, light

A cheerful piece with a bouncy main theme, a contrasting middle section, and a return with added ornamentation.
```

### Tips for Choosing Parameters

#### Form
- **binary**: Simple two-section structure (A-B). Good for short pieces (32-64 beats). The B section typically contrasts with A and may modulate.
- **ternary/ABA**: Three-part form with a return. Classic structure for character pieces (48-128 beats). The middle section provides contrast.
- **rondo**: Recurring main theme (A) alternates with contrasting episodes (B, C). Good for lively, dance-like pieces. Patterns: ABACA (5-part) or ABACABA (7-part).
- **sonata**: Large-scale form (150-300+ beats) with exposition, development, and recapitulation. Best for dramatic, substantial works with thematic development.
- **theme and variations**: A theme followed by multiple variations. Great for exploring different textures, moods, and techniques. Can be any length.
- **free-form**: No strict formal structure. Use for programmatic pieces, improvisatory styles, or when you want maximum flexibility.

#### Key
- **Major keys** (C, G, D, F, Bb, etc.): Generally brighter, more optimistic, or energetic. Good for: joyful, triumphant, playful, or serene pieces.
- **Minor keys** (Am, Dm, Gm, Cm, etc.): Generally darker, more emotional, or introspective. Good for: melancholic, dramatic, contemplative, or passionate pieces.
- **Common choices**: C major (simple, bright), G major (warm), D major (brilliant), F major (gentle), A minor (expressive), D minor (dramatic), C minor (tragic, powerful).
- **Sharps/flats**: More sharps (G, D, A, E) tend to sound brighter; more flats (F, Bb, Eb) tend to sound warmer or darker.
- **Tip**: You can also just describe the mood you want (e.g., "bright and cheerful" or "dark and mysterious") and let the model choose an appropriate key.

#### Tempo (BPM)
- **Very slow (40-60)**: Grave, largo. For solemn, meditative, or deeply emotional pieces.
- **Slow (60-80)**: Adagio, andante. For lyrical, contemplative, or expressive pieces.
- **Moderate (80-100)**: Moderato. Balanced, comfortable pace. Good default for many styles.
- **Moderately fast (100-120)**: Allegretto. Light, flowing, or gently energetic.
- **Fast (120-160)**: Allegro. Energetic, exciting, or dance-like.
- **Very fast (160+)**: Presto, vivace. Brilliant, virtuosic, or intensely energetic.
- **Tip**: You can also use descriptive terms like "slow", "moderate", "fast", "lively", or "relaxed" instead of specific BPM values.

#### Time Signature
- **4/4 (common time)**: Most versatile. Natural, balanced feel. Good for most styles.
- **3/4 (waltz time)**: Triple meter with a waltz-like feel. Good for: waltzes, lyrical pieces, or pieces with a gentle, flowing character.
- **6/8 (compound duple)**: Two beats per measure, each divided into three. Good for: flowing, dance-like pieces, or pieces with a lilting quality.
- **2/4**: Two beats per measure. Often feels more direct or march-like.
- **3/8**: Similar to 3/4 but lighter, faster feel.
- **Tip**: If unsure, 4/4 is a safe default. For waltzes or dance-like pieces, use 3/4 or 6/8.

#### Style/Character
- **lyrical**: Song-like, melodic, expressive. Focus on beautiful melodies.
- **dramatic**: Intense, emotional, with strong contrasts and dynamic range.
- **playful**: Light, cheerful, with bouncy rhythms and bright harmonies.
- **contemplative**: Thoughtful, introspective, often slower with rich harmonies.
- **energetic**: Fast, active, with driving rhythms and bright character.
- **melancholic**: Sad, wistful, often in minor keys with expressive melodies.
- **majestic**: Grand, noble, with full textures and strong presence.
- **delicate**: Light, refined, with soft dynamics and careful voicing.
- **passionate**: Intense, emotional, with strong dynamics and expressive lines.
- **Tip**: You can combine multiple descriptors (e.g., "playful and energetic" or "contemplative and melancholic") or use your own words to describe the mood you want.

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
