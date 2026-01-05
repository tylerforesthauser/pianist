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

**Using `section` for formal structure**: Mark formal sections (e.g., `"section": "exposition"`, `"section": "A"`, `"section": "development"`) to help organize longer works. This is purely annotative and doesn't affect playback, but helps models structure their output.

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
You are an expert music composition generator with deep knowledge of music theory, harmony, and classical composition. Output MUST be valid JSON only.

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
- Prefer events sorted by start time.
- Ensure all harmonies are complete and properly voiced.
- Maintain consistent key centers within sections unless intentionally modulating.
```

### User prompt (copy/paste)
```
Compose a piano piece. Requirements:

Musical goals:
- Use a clear formal structure (ABA/ternary recommended, or sonata, rondo, theme and variations for longer works).
- For longer pieces, aim for ~100–500+ beats and organize material by form.
- Introduce a short motif early, then develop it (transpose/invert/augment/fragment/sequence) throughout.
- Use dynamics via velocity (p -> mf -> f and back) to shape phrases and larger sections.
- Mark formal sections using the `section` field (e.g., "exposition", "A", "development", "B").
- Create contrast between sections (keys, textures, moods) and use transitions to connect them.
- Keep timing consistent: start/duration in beats; allow chords by multiple pitches.

Harmony and voice leading:
- Use functional harmony: establish clear tonic-dominant relationships, use proper cadences (authentic V→I, half cadences ending on V, plagal IV→I, deceptive V→vi).
- Maintain smooth voice leading: prefer stepwise motion, resolve leading tones and chordal sevenths properly, avoid parallel fifths/octaves.
- Vary harmonic rhythm appropriately: faster changes in active sections, slower in lyrical passages.
- When modulating, use pivot chords or prepare modulations clearly; return to home key for structural closure.

Melody and counterpoint:
- Create melodic lines with clear direction and contour. Use non-chord tones (passing, neighbor, suspension) for interest while maintaining harmonic clarity.
- If using multiple voices, maintain independence with contrary motion where appropriate, proper spacing, and avoid voice crossing.

Texture and voicing:
- Left hand: provide harmonic foundation (bass line + chord tones in appropriate register).
- Right hand: carry melody with supporting harmony when needed.
- Balance melody and accompaniment; vary texture between sections.

Representation:
- Use a single Piano track.
- Use `groups` (preferred) or `notes` so every note is labeled with `hand` ("lh"/"rh") and optional `voice` (1-4).
```

## Formal Structures (for lengthier compositions)

Use these classical and romantic forms as **creative frameworks**, not rigid templates. Interpret them freely, combine elements, and adapt them to your musical vision.

### Single-Movement Forms

#### **Binary Form (A-B)**
- **A section**: Establish a theme, typically 16-32 beats. End with a cadence (often in the tonic or dominant).
- **B section**: Contrasting material, may modulate. Can be similar length or longer. Return to tonic at the end.
- **Creative approach**: Vary the return, add transitions, or extend sections with sequences.

#### **Ternary Form (A-B-A)**
- **A section**: Main theme, establishes key and character.
- **B section**: Contrast (different key, mood, texture, or tempo). Often 1.5-2x the length of A.
- **A' section**: Return of A, often varied (ornamented, transposed, or with different accompaniment).
- **Creative approach**: Make the return transformative—add countermelodies, change register, or develop the theme further.

#### **Rondo Form (A-B-A-C-A or A-B-A-C-A-B-A)**
- **A section**: Recurring theme (refrain), appears 3-5 times.
- **B, C sections**: Contrasting episodes (episodes), each different from A and each other.
- **Typical patterns**: ABACA (5-part), ABACABA (7-part).
- **Creative approach**: Vary each A return, make episodes increasingly contrasting, or add a coda.

#### **Sonata Form** (exposition-development-recapitulation)
- **Exposition**: 
  - First theme (tonic key), typically 16-32 beats
  - Transition (modulation)
  - Second theme (dominant or relative major/minor), contrasting character
  - Closing section (codetta), reinforces new key
- **Development**: 
  - Fragments, sequences, modulations, dramatic tension
  - Typically 1.5-2x the length of exposition
  - Explore remote keys, invert themes, combine motifs
- **Recapitulation**:
  - First theme returns (tonic)
  - Transition (stays in tonic or modulates briefly)
  - Second theme returns in **tonic** (key difference from exposition)
  - Closing section (coda optional)
- **Creative approach**: Compress or expand sections, add introductions/codas, or blur boundaries between sections.

#### **Theme and Variations**
- **Theme**: Clear, memorable melody (16-32 beats), simple harmonization.
- **Variations**: 3-8+ variations, each transforming the theme:
  - Variation techniques: ornamentation, change of mode (major/minor), tempo, meter, texture, register, harmony, rhythm, counterpoint.
- **Creative approach**: Progressive complexity, or alternating character (fast/slow, lyrical/virtuosic).

### Multi-Movement Forms

#### **Sonata** (multi-movement)
- Typically 3-4 movements with contrasting characters:
  - **Movement 1**: Fast, often sonata form, dramatic
  - **Movement 2**: Slow, lyrical, often ternary or theme and variations
  - **Movement 3**: Dance (minuet, scherzo) or moderate tempo, ternary form
  - **Movement 4**: Fast finale, rondo or sonata form
- **Creative approach**: Vary the number of movements, or use free forms for some movements.

#### **Suite** (multi-movement)
- Collection of dance movements, each in binary or ternary form:
  - **Allemande** (moderate, 4/4)
  - **Courante** (fast, 3/4 or 3/2)
  - **Sarabande** (slow, 3/4, emphasis on beat 2)
  - **Gigue** (fast, compound meter, often fugal)
- **Creative approach**: Add character pieces, modernize rhythms, or select specific dances.

### Dance Forms

#### **Minuet** (and Trio)
- **Minuet**: Moderate 3/4, graceful, binary or ternary, typically 32-64 beats.
- **Trio**: Contrasting middle section (often different key, texture, or character).
- **Return**: Minuet da capo (often without repeats).
- **Creative approach**: Vary the trio's character dramatically, or expand into a scherzo (faster, more playful).

#### **Waltz**
- 3/4 time, strong downbeat, lyrical or dance-like.
- Often in ternary form or as a collection of waltzes.
- **Creative approach**: Vary tempo, add rubato, or use extended harmonies.

#### **Polonaise**
- 3/4 time, stately, characteristic rhythm (often eighth-sixteenth-sixteenth on beat 1).
- Binary or ternary form, typically 64-128 beats.
- **Creative approach**: Vary the characteristic rhythm, or blend with other forms.

### Romantic Character Pieces

#### **Nocturne**
- Slow to moderate, lyrical, song-like.
- Often ternary form with ornamented return.
- Emphasis on melody, rich harmonies, expressive dynamics.
- **Creative approach**: Free-form sections, extended codas, or programmatic elements.

#### **Ballade**
- Narrative character, often free-form or through-composed.
- May incorporate multiple themes, dramatic contrasts, and programmatic elements.
- Can be quite extended (200+ beats).
- **Creative approach**: Tell a story through music, use recurring themes, or build to climactic moments.

#### **Étude**
- Focus on a specific technical challenge (arpeggios, octaves, thirds, etc.).
- Often ternary or binary form, but technique takes precedence.
- **Creative approach**: Make it musically interesting beyond the technical exercise, or combine multiple techniques.

### Creating Lengthier Compositions

**Strategies for extended works (100-500+ beats):**

1. **Use formal structures**: Sonata form, multi-movement works, or extended theme and variations naturally create longer pieces.

2. **Develop motifs extensively**: 
   - Introduce 2-3 contrasting motifs early
   - Develop each through sequences, modulations, and transformations
   - Combine motifs in counterpoint or layered textures

3. **Plan section lengths**:
   - Simple forms (binary/ternary): 32-128 beats total
   - Sonata form: 150-300+ beats
   - Multi-movement: 200-500+ beats (50-150 per movement)

4. **Use the `section` field**: Mark formal sections clearly:
   ```json
   { "type": "note", ..., "section": "exposition" }
   { "type": "note", ..., "section": "development" }
   { "type": "note", ..., "section": "recapitulation" }
   ```

5. **Create contrast and return**:
   - Establish clear sections with different keys, tempos (via BPM changes if needed), textures, or moods
   - Use transitions between sections (modulating passages, sequences)
   - Return to earlier material to create coherence

6. **Build to climaxes**:
   - Use dynamics (velocity) to shape larger arcs
   - Save highest energy for development sections or final returns
   - Create tension and release across the entire work

**Remember**: These forms are tools for organization and expression. Feel free to:
- Combine elements from different forms
- Compress or expand traditional proportions
- Add introductions, codas, or interludes
- Break "rules" when it serves the music
- Use free-form sections within structured works

## Tips that help models succeed
- Keep events **sorted by `start`** (not required, but reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start`.
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation.
- For longer works, plan the overall structure first, then fill in details section by section.
- Use the `section` annotation field liberally to mark formal divisions—it helps organize thinking even if it doesn't affect playback.
