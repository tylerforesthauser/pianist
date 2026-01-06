# AI Prompting Guide

## Overview

This guide is structured in two parts:
- **Part 1: For Users** - How to create effective prompts and use Pianist's tools
- **Part 2: For AI Models** - System prompt templates, schema reference, and output requirements

The key to success is splitting your prompt into two parts:
- **System prompt**: Stable "rules of the game" (format + schema constraints). This is typically fixed and doesn't change.
- **User prompt**: Your musical brief (style, form, length, key, tempo, etc.). This is where you specify what you want.

This two-part approach typically improves **schema adherence** and reduces output drift compared to a single combined prompt.

---

# Part 1: For Users

This section contains instructions and guidance for **human users** creating prompts and using Pianist.

## Iterating on Existing Works (JSON or MIDI)

Pianist supports an iteration workflow where you can start from either:
- An existing **Pianist composition JSON** (or raw model output that contains such JSON), or
- A **MIDI file** (`.mid`/`.midi`)

The goal is to produce a **clean, schema-valid JSON seed** you can edit by hand or feed back into an AI model to revise/extend.

### Step 1: Import your starting point into a JSON seed

Use `pianist iterate` to normalize either JSON or MIDI into a canonical, tweak-friendly JSON file:

```bash
# MIDI -> JSON seed
./pianist iterate --in "existing.mid" --out "seed.json"

# JSON/LLM output -> canonical JSON seed
./pianist iterate --in "some_model_output.txt" --out "seed.json"
```

Optional quick tweak (without using an AI model):

```bash
# Transpose all notes up by 2 semitones
./pianist iterate --in "seed.json" --transpose 2 --out "seed_transposed.json"
```

### Step 2: Ask the model to revise the seed (recommended prompting pattern)

Keep your **System prompt** mostly the same, but change your **User prompt** to:
- Provide the *existing seed JSON*
- Specify *requested changes*
- Require the model to output a **complete new JSON object**, not a diff

Tip: Pianist can generate a ready-to-paste iteration prompt file:

```bash
./pianist iterate --in "seed.json" --prompt-out "iterate_prompt.txt" --instructions "Make it more lyrical and add an 8-beat coda."
```

Then paste that prompt into your model and render the result:

```bash
./pianist render --in "updated_seed.json" --out "updated.mid"
```

## Creating NEW Works Inspired by an Existing MIDI (Analysis -> Prompt)

Sometimes you don't want to *edit* an existing piece—you want to create something **new** that inherits its tempo/texture/density/registration tendencies.

Use `pianist analyze` to extract prompt-friendly constraints from a MIDI file and generate a ready-to-paste prompt for composing a new work:

```bash
# Generate a prompt for a NEW composition (recommended)
./pianist analyze --in "existing.mid" --format prompt --prompt-out "new_piece_prompt.txt" \
  --instructions "Compose a new 64-bar piece with similar texture, but brighter harmony and a stronger climax."

# Optional: export structured analysis JSON (useful for building tools/UIs)
./pianist analyze --in "existing.mid" --format json --out "analysis.json"
```

Workflow:
- Run `./pianist analyze ...` to get a prompt.
- Paste the prompt into your model to produce a **new** Pianist composition JSON.
- Render it with `./pianist render --in new.json --out new.mid`.

## Building Your User Prompt

The user prompt is where you specify what you want. You can phrase your request naturally—the model will interpret it. You don't need to include all parameters; provide only what matters to you.

### User Prompt Template

**Template structure:**

```
[OPTIONAL OPENING - phrase naturally]
{{Compose a piano piece:}} or {{I'd like a piano piece}} or {{Create a piano composition}} or just start with the title

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
```

### Tips for Choosing Parameters

#### Form
- **binary (A-B)**: Simple two-section structure. Good for short pieces (32-64 beats). The B section typically contrasts with A and may modulate, then returns to tonic.
- **ternary (A-B-A)**: Three-part form with a return. Classic structure for character pieces (48-128 beats). The middle section (B) provides contrast and is typically 1.5-2x the length of A. The return of A is often varied or ornamented.
- **rondo**: Recurring main theme (A) alternates with contrasting episodes (B, C). Good for lively, dance-like pieces. Common patterns: ABACA (5-part) or ABACABA (7-part). Each episode explores different keys, textures, or moods.
- **sonata form**: Large-scale form (150-300+ beats) with three main sections: **Exposition** (first theme in tonic, second theme in dominant), **Development** (fragments, modulations, tension), **Recapitulation** (both themes in tonic). Best for dramatic, substantial works with thematic development.
- **theme and variations**: A clear theme (16-32 beats) followed by 3-8+ variations that transform it through ornamentation, mode changes, tempo, texture, harmony, etc. Great for exploring different moods and techniques. Can be any length.
- **multi-movement works**: Complete works with 3-4 movements, each with contrasting characters. Common patterns: fast-slow-dance-fast, or dramatic-lyrical-scherzo-finale. Each movement can use its own form (sonata, ternary, rondo, etc.). Total length typically 300-500+ beats.
- **free-form**: No strict formal structure. Use for programmatic pieces, improvisatory styles, or when you want maximum flexibility. Can be through-composed with multiple contrasting sections.

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

#### Tempo Changes
You can request tempo changes in your composition to create expressive effects:

- **Ritardando (slowing down)**: Request a gradual slowdown, especially at phrase endings, cadences, or the end of a piece. For example: "Include a ritardando in the final 8 beats" or "Slow down gradually at the end."
- **Accelerando (speeding up)**: Request a gradual speedup, often useful in transitions or climactic sections. For example: "Include an accelerando in the transition to the development section."
- **Tempo flexibility**: Request tempo changes for expressive purposes, such as "Add some tempo flexibility in the lyrical middle section" or "Use a slight ritardando before the final cadence."

The AI model will automatically generate the appropriate tempo events in the JSON output. You don't need to specify the technical details—just describe the musical effect you want.

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

**Character pieces** (specific genres that combine form and style):
- **Nocturne**: Slow-moderate tempo, lyrical and song-like, often ternary form with ornamented return. Typically contemplative or melancholic.
- **Ballade**: Narrative character, free-form or through-composed, may be extended (200+ beats). Often dramatic with multiple contrasting sections.
- **Étude**: Focus on technical challenge or specific technique, often ternary or binary form. Can be energetic, virtuosic, or lyrical.
- **Suite**: Collection of dance movements (allemande, courante, sarabande, gigue), each typically in binary or ternary form. Each movement has its own character.

- **Tip**: You can combine multiple descriptors (e.g., "playful and energetic" or "contemplative and melancholic") or use your own words to describe the mood you want. Character pieces like "nocturne" or "ballade" can serve as both form and style descriptors.

### Example Prompts for Shorter Works (32-128 beats)

Here are diverse examples of prompts for shorter compositions covering various styles, tempos, moods, and structures:

#### Example 1: Playful Dance (Ternary)

```
Compose a piano piece:

Title: "Spring Dance"
Form: ternary
Key: G major
Tempo: 120
Style/Character: playful, light

A cheerful piece with a bouncy main theme, a contrasting middle section, and a return with added ornamentation.
```

#### Example 2: Lyrical Contemplation (Ternary)

```
I'd like a gentle, flowing piano piece called "Morning Sketch" in C major. Something lyrical and contemplative, around 64 beats long, in ternary form.
```

#### Example 3: Melancholic Expression (Binary)

```
Title: "Evening Prelude"
Form: binary
Length: ~48 beats
Key: D minor
Tempo: 72
Style/Character: contemplative, melancholic

A short, expressive piece with a memorable melody that develops through the two sections.
```

#### Example 4: Baroque-Inspired Fugue (Fugue)

```
Compose a piano piece:

Title: "Fugue in A Minor"
Form: fugue
Length: ~80 beats
Key: A minor
Tempo: 100
Time signature: 4/4
Style/Character: Baroque, contrapuntal, with intricate voice leading

A three-voice fugue with a clear subject, answer, and episodes. The subject should be memorable and easily recognizable. Include stretto entries and a final statement of the subject in the bass.
```

#### Example 5: Impressionist Watercolor (Free-form)

```
Create a piano piece:

Title: "Reflections on Water"
Form: free-form
Length: ~96 beats
Key: Db major (with modal inflections)
Tempo: 66
Time signature: 9/8
Style/Character: impressionist, ethereal, with floating harmonies

A dreamy piece with whole-tone and pentatonic elements. Use parallel chords, delicate textures, and subtle dynamic shifts. The melody should be fragmentary and atmospheric rather than strongly directional.
```

#### Example 6: Virtuosic Étude (Ternary)

```
Compose a piano étude:

Title: "Étude in E Major - The Cascades"
Form: ternary
Length: ~112 beats
Key: E major
Tempo: 144
Time signature: 4/4
Style/Character: brilliant, virtuosic, with rapid arpeggios

A technical étude focusing on right-hand arpeggiated passages across the keyboard. The A section should feature cascading arpeggios, the B section provides lyrical contrast, and the return of A adds greater complexity and intensity.
```

#### Example 7: Minimalist Pattern Piece (Through-composed)

```
I'd like a minimalist piano piece:

Title: "Pattern Study No. 1"
Form: through-composed
Length: ~64 beats
Key: F major (with modal ambiguity)
Tempo: 88
Time signature: 5/4
Style/Character: minimalist, meditative, with repetitive patterns

A piece built on a simple melodic pattern that gradually transforms through subtle variations. Use sparse textures, clear harmonic progressions, and let the pattern evolve organically without dramatic contrasts.
```

#### Example 8: Romantic Intermezzo (Ternary)

```
Compose a piano intermezzo:

Title: "Intermezzo in Bb Minor"
Form: ternary
Length: ~96 beats
Key: Bb minor
Tempo: 76
Time signature: 3/4
Style/Character: romantic, expressive, with rich chromaticism

A lyrical piece with a song-like melody in the outer sections and a more agitated middle section. Use expressive rubato, chromatic harmonies, and build to an emotional climax before returning to the opening material.
```

#### Example 9: Jazz-Influenced Blues (12-bar Blues)

```
Create a piano piece:

Title: "Midnight Blues"
Form: 12-bar blues (extended)
Length: ~96 beats
Key: C minor (blues scale)
Tempo: 92
Time signature: 4/4
Style/Character: blues, jazz-influenced, with syncopation

A blues piece with a walking bass line in the left hand and a syncopated melody in the right. Include blue notes, seventh chords, and rhythmic flexibility. The form should follow a 12-bar blues progression with variations.
```

#### Example 10: Mysterious Nocturne (Ternary)

```
Compose a piano nocturne:

Title: "Nocturne in F# Major"
Form: ternary
Length: ~80 beats
Key: F# major
Tempo: 58
Time signature: 4/4
Style/Character: mysterious, nocturnal, with subtle dissonances

A haunting piece with a meandering melody and rich, sometimes ambiguous harmonies. Use the full range of the piano, create moments of tension and release, and maintain an overall sense of mystery and introspection.
```

### Planning Longer Works (100-500+ beats)

When requesting longer compositions, you'll need to provide more structure and planning. Here's how to approach it:

#### Choosing the Right Form
- **Sonata form** (150-300+ beats): Best for dramatic, substantial works with thematic development. Natural structure: exposition (60-80 beats), development (80-100 beats), recapitulation (60-80 beats).
- **Theme and variations** (150-400+ beats): Flexible length depending on number of variations. Request 4-8 variations for substantial works. Each variation can explore different textures, keys, tempos, or moods.
- **Extended rondo** (100-250+ beats): ABACABA pattern creates natural length. Each episode (B, C) can be substantial (30-50 beats), with returns to the main theme.
- **Multi-movement works** (300-500+ beats): Request 3-4 movements with contrasting characters (e.g., "fast-slow-dance-fast" or "dramatic-lyrical-scherzo-finale").
- **Extended ternary** (100-200 beats): Expand the middle section significantly (60-100 beats) and add transitions, creating a more substantial work.
- **Free-form/through-composed** (200-500+ beats): For programmatic or narrative pieces, request multiple contrasting sections with clear transitions.

#### Structuring Your Prompt
1. **Specify overall length**: Give a target range (e.g., "approximately 250 beats" or "around 300-350 beats").
2. **Outline the form**: Explicitly state the formal structure and expected section lengths.
3. **Request motif development**: Ask for 2-3 contrasting motifs that will be developed throughout the piece.
4. **Plan key relationships**: For sonata form, request modulation to the dominant in the exposition, distant keys in the development, and return to tonic in the recapitulation.
5. **Request transitions**: Explicitly ask for connecting passages, modulatory bridges, or cadential extensions between sections.
6. **Specify dynamic arcs**: Request that dynamics build to a climax (often in the development or middle section) and create tension and release across the entire work.

#### Section-by-Section Planning
- **For sonata form**: Request a clear first theme group (20-30 beats), transition to second theme (10-15 beats), second theme group (20-30 beats), closing material (10-15 beats), development with modulations (80-100 beats), and recapitulation with both themes in tonic (60-80 beats).
- **For theme and variations**: Request a clear, memorable theme (16-32 beats), then specify the character of each variation (e.g., "first variation: faster tempo with ornamentation", "second variation: minor mode", "third variation: slower, more lyrical").
- **For extended rondo**: Request a memorable main theme (16-24 beats) that returns, and substantial contrasting episodes (30-50 beats each) that explore different keys, textures, or moods.

#### Motivic Development Strategies
- Request that motifs be introduced early and developed through:
  - **Transposition**: Moving the motif to different keys
  - **Inversion**: Turning the motif upside down
  - **Augmentation**: Slowing the motif down
  - **Diminution**: Speeding the motif up
  - **Fragmentation**: Breaking the motif into smaller pieces
  - **Sequence**: Repeating the motif at different pitch levels
  - **Counterpoint**: Combining motifs in different voices

#### Key Relationships and Modulations
- For longer works, request planned modulations:
  - **Sonata form**: Tonic → Dominant (exposition), distant keys (development), return to Tonic (recapitulation)
  - **Theme and variations**: Each variation can explore related keys (relative major/minor, parallel major/minor, or closely related keys)
  - **Extended works**: Request a key scheme (e.g., "modulate to the subdominant in the middle section, then return to tonic")

#### Dynamic Planning
- Request that dynamics create larger-scale arcs:
  - Build from quiet opening to a climactic middle section
  - Use dynamic contrast between sections (e.g., quiet lyrical section vs. loud dramatic section)
  - Request a gradual crescendo to the climax, then a gradual decrescendo
  - Use dynamics to highlight returns of themes (e.g., "return the main theme with greater intensity")

#### Ensuring Continuity
- Explicitly request that the piece be continuous with no large gaps:
  - "Fill the entire 250 beats with continuous music"
  - "Use transitions and connecting passages between sections"
  - "Avoid long silences—brief pauses (1-2 beats) between phrases are acceptable, but sections should flow continuously"
  - "The last event should end close to the requested length"

#### Example Section Lengths for Common Forms
- **Sonata form (250 beats)**: Exposition ~70 beats, Development ~90 beats, Recapitulation ~70 beats, transitions ~20 beats
- **Theme and variations (200 beats)**: Theme ~24 beats, 6 variations ~28 beats each, transitions ~8 beats
- **Extended rondo (180 beats)**: Main theme (A) ~20 beats, episodes (B, C) ~40 beats each, returns (A) ~20 beats each
- **Extended ternary (150 beats)**: A section ~40 beats, B section ~60 beats, A' section ~40 beats, transitions ~10 beats

### Example Prompts for Longer Works (100-500+ beats)

Here are diverse examples of prompts for compositions in the 100-500+ beat range, covering various styles, tempos, moods, structures, and melodic complexities:

#### Example 1: Sonata Form (250 beats)

```
Compose a piano sonata:

Title: "Sonata in C Minor - The Tempest"
Form: sonata
Length: approximately 250 beats
Key: C minor
Tempo: 84
Time signature: 4/4
Style/Character: dramatic, passionate, with moments of lyrical contrast

Structure:
- Exposition (approximately 70 beats): First theme group in C minor (20-25 beats), transition modulating to Eb major (10-15 beats), second theme group in Eb major (20-25 beats), closing material (10-15 beats)
- Development (approximately 90 beats): Develop both themes through sequences, modulations to distant keys (Ab major, F minor, G minor), use fragmentation and counterpoint, build to a dramatic climax
- Recapitulation (approximately 70 beats): Both themes return in C minor, second theme now in tonic, with some variation and expansion
- Transitions: Use connecting passages and modulatory bridges between sections (approximately 20 beats total)

Musical elements:
- Introduce 2-3 contrasting motifs in the exposition that will be developed throughout
- Use dynamics to build from a quiet, mysterious opening to a powerful climax in the development, then return with greater intensity in the recapitulation
- Include a lyrical, contrasting second theme that provides relief from the dramatic first theme
- Use proper voice leading and functional harmony throughout
- Fill the entire 250 beats with continuous music—no large gaps or silences
```

#### Example 2: Theme and Variations (300 beats)

```
Create a piano composition:

Title: "Variations on a Theme"
Form: theme and variations
Length: approximately 300 beats
Key: G major (with variations exploring related keys)
Tempo: 100
Time signature: 4/4
Style/Character: elegant, with each variation exploring different moods and textures

Structure:
- Theme (24 beats): A simple, memorable melody in G major, in binary form (A-B, 12 beats each)
- Variation 1 (28 beats): Faster tempo (120 BPM), add ornamentation and running passages, maintain G major
- Variation 2 (28 beats): Minor mode variation in G minor, more expressive and melancholic, tempo returns to 100
- Variation 3 (28 beats): Slower tempo (80 BPM), more lyrical and contemplative, explore richer harmonies, return to G major
- Variation 4 (28 beats): Lively and playful, use staccato and syncopation, modulate to D major
- Variation 5 (28 beats): Adagio tempo (60 BPM), very expressive and lyrical, return to G major, use full piano range
- Variation 6 (28 beats): Fast and brilliant (140 BPM), virtuosic passages, return to G major
- Variation 7 (28 beats): Tempo giusto (100 BPM), combine elements from previous variations, return to the original theme character
- Coda (28 beats): Extended conclusion that references the theme and brings the work to a satisfying close

Musical elements:
- Each variation should transform the theme while remaining recognizable
- Use different textures: homophonic, polyphonic, melody with accompaniment
- Explore different registers and hand distributions
- Build dynamic intensity through the variations, with a peak in variation 6, then a reflective variation 7
- Include smooth transitions between variations (2-4 beats each)
- Ensure continuous music throughout—the last event should end around beat 300
```

#### Example 3: Extended Rondo (180 beats)

```
Compose a piano piece:

Title: "Rondo Capriccioso"
Form: extended rondo (ABACABA)
Length: approximately 180 beats
Key: A major
Tempo: 120
Time signature: 6/8
Style/Character: light, dance-like, with contrasting episodes

Structure:
- Main theme (A): 20 beats, cheerful and memorable, in A major, appears at beats 0, 50, 120, and 160
- Episode 1 (B): 30 beats, contrasting key (D major), more lyrical and flowing
- Episode 2 (C): 30 beats, contrasting key (F# minor), more dramatic and expressive
- Transitions: Brief connecting passages (2-4 beats) between sections

Musical elements:
- The main theme should be catchy and easily recognizable when it returns
- Each episode should contrast in character: B more lyrical, C more dramatic
- Use modulations to create interest: A major → D major → A major → F# minor → A major
- Vary the returns of the main theme: first return can be identical, later returns can have slight variations or different dynamics
- Build energy through the piece, with the final A section being the most energetic
- Maintain the 6/8 dance-like character throughout
- Fill all 180 beats with continuous music
```

#### Example 4: Extended Ternary with Development (150 beats)

```
I'd like a piano piece:

Title: "Nocturne in Eb Major"
Form: extended ternary (ABA')
Length: approximately 150 beats
Key: Eb major
Tempo: 72
Time signature: 4/4
Style/Character: lyrical, contemplative, with a passionate middle section

Structure:
- A section (40 beats): Lyrical, song-like melody in Eb major, quiet dynamics (p to mp)
- Transition (8 beats): Modulate to C minor, build tension
- B section (60 beats): More dramatic and passionate, in C minor, explore the full range of the piano, build to a climax (f to ff), then gradually subside
- Transition (8 beats): Return to Eb major, prepare for the return
- A' section (40 beats): Return of the A theme with ornamentation and variation, slightly more expressive, end with a gentle coda

Musical elements:
- The A section should have a memorable, flowing melody
- The B section should provide strong contrast: different key, different mood, different texture
- Use dynamics to shape the overall arc: quiet opening, build to climax in B section, return with greater depth in A'
- Include tempo flexibility: slight ritardando at phrase endings, especially in the final A' section
- Use pedal throughout to create a rich, sustained sound
- Ensure smooth transitions between sections—no abrupt changes
- The piece should flow continuously from start to finish
```

#### Example 5: Multi-Movement Work (400 beats)

```
Compose a multi-movement piano work:

Title: "Sonata in D Major"
Form: multi-movement (4 movements)
Length: approximately 400 beats total
Key: D major (with movements in related keys)
Style/Character: Classical style with contrasting movements

Structure:
- Movement 1: Allegro (120 beats, D major, 120 BPM, sonata form) - Energetic and brilliant
- Movement 2: Adagio (80 beats, B minor, 60 BPM, ternary form) - Slow, expressive, and lyrical
- Movement 3: Menuetto (60 beats, D major, 100 BPM, ternary form) - Dance-like, graceful
- Movement 4: Presto (140 beats, D major, 160 BPM, rondo form) - Fast, lively, and virtuosic

Musical elements:
- Each movement should be complete and satisfying on its own, but also work as part of the whole
- Create contrast between movements: fast-slow-dance-fast pattern
- Movement 1: Use sonata form with clear themes, development, and recapitulation
- Movement 2: Very expressive, use rich harmonies and full dynamic range
- Movement 3: Light and dance-like, with a contrasting trio section
- Movement 4: Brilliant and energetic, bring the work to an exciting conclusion
- Transitions between movements can be brief (1-2 beats) or you can request seamless connections
- Each movement should fill its specified length with continuous music
```

#### Example 6: Free-Form Extended Work (250 beats)

```
Create an extended piano composition:

Title: "Ballade in F# Minor"
Form: free-form, through-composed
Length: approximately 250 beats
Key: F# minor (with modulations)
Tempo: 88
Time signature: 4/4
Style/Character: narrative, dramatic, with multiple contrasting sections

Structure:
- Introduction (20 beats): Mysterious opening, establish F# minor, quiet dynamics
- Main theme (30 beats): Lyrical melody, develop the main musical idea
- Transition 1 (10 beats): Modulate to A major
- Contrasting section (40 beats): More energetic, in A major, different texture
- Development (60 beats): Develop themes from previous sections, modulate through several keys (A major → D major → B minor), build to a dramatic climax
- Transition 2 (15 beats): Return to F# minor, prepare for recapitulation
- Recapitulation (50 beats): Return of main theme with variation and greater intensity, in F# minor
- Coda (25 beats): Extended conclusion, reference earlier material, bring to a satisfying close

Musical elements:
- Create a narrative arc: mysterious beginning → lyrical theme → energetic contrast → dramatic development → return with resolution
- Use 2-3 main motifs that appear and develop throughout
- Build to a clear climax in the development section (around beat 120-140)
- Use dynamics to shape the overall arc: p → mf → f → ff (climax) → mf → p
- Include tempo changes: slight accelerando in the development, ritardando in the coda
- Ensure smooth transitions between all sections
- Fill all 250 beats with continuous music—no gaps or silences
```

#### Example 7: Passacaglia with Variations (200 beats)

```
Compose a piano passacaglia:

Title: "Passacaglia in D Minor"
Form: passacaglia (variations over ground bass)
Length: approximately 200 beats
Key: D minor
Tempo: 72
Time signature: 3/4
Style/Character: Baroque-inspired, serious, with increasing complexity

Structure:
- Ground bass (8 beats): A descending bass line in D minor, repeated throughout
- Variation 1 (8 beats): Simple counterpoint above the bass
- Variation 2 (8 beats): Add a melodic line in the right hand
- Variation 3 (8 beats): Increase rhythmic activity
- Variation 4 (8 beats): Introduce syncopation
- Variation 5 (8 beats): More complex harmonies and voice leading
- Variation 6 (8 beats): Faster note values, more virtuosic
- Variation 7 (8 beats): Peak of complexity, full texture
- Variation 8 (8 beats): Begin to simplify
- Variation 9 (8 beats): Return to simpler texture
- Variation 10 (8 beats): Final statement with coda (32 beats)

Musical elements:
- The ground bass should be clearly audible in every variation
- Each variation should build in complexity while maintaining the bass pattern
- Use proper Baroque counterpoint: avoid parallel fifths, maintain voice independence
- The final coda should bring the work to a satisfying conclusion
- Ensure continuous music throughout all 200 beats
```

#### Example 8: Romantic Fantasy (280 beats)

```
Create a romantic piano fantasy:

Title: "Fantasy in E Major"
Form: free-form fantasy
Length: approximately 280 beats
Key: E major (with extensive modulations)
Tempo: 88 (with tempo flexibility)
Time signature: 4/4
Style/Character: romantic, passionate, with dramatic contrasts and highly ornamented melodies

Structure:
- Introduction (24 beats): Improvisatory opening, establish E major, use rubato
- First theme (32 beats): Lyrical, song-like melody with rich harmonies
- Transition 1 (16 beats): Modulate to C# minor, build tension
- Second theme (40 beats): More dramatic, in C# minor, with chromaticism
- Development section (100 beats): Freely develop both themes, explore distant keys (Ab major, F# minor, Bb major), include cadenzas and virtuosic passages
- Recitative section (20 beats): Recitative-like passage, very expressive and free
- Final theme (32 beats): Return to E major, combine elements from both themes
- Coda (16 beats): Brilliant conclusion with final flourish

Musical elements:
- Use highly ornamented melodies with trills, turns, and appoggiaturas
- Include dramatic dynamic contrasts (pp to ff)
- Request extensive use of rubato and tempo flexibility
- Use rich chromatic harmonies and modulations
- Include virtuosic passages requiring technical skill
- Create a sense of improvisation and freedom
- Fill all 280 beats with continuous, flowing music
```

#### Example 9: Modern Toccata (180 beats)

```
Compose a modern piano toccata:

Title: "Toccata in Bb Minor"
Form: through-composed
Length: approximately 180 beats
Key: Bb minor (with modal and atonal elements)
Tempo: 160
Time signature: 4/4 (with metric shifts)
Style/Character: modern, aggressive, with percussive elements and complex rhythms

Structure:
- Opening (24 beats): Driving rhythmic ostinato, establish Bb minor
- First section (40 beats): Build intensity, add layers of complexity
- Contrasting section (32 beats): More lyrical but still intense, explore different textures
- Development (48 beats): Fragment and develop motifs, use polyrhythms and metric modulation
- Climax (24 beats): Maximum intensity, full keyboard, complex harmonies
- Coda (12 beats): Rapid conclusion with final statement

Musical elements:
- Use percussive, staccato attacks and sharp accents
- Include complex rhythms: syncopation, polyrhythms, metric shifts
- Explore dissonant harmonies and cluster chords
- Use the full range of the piano with wide leaps
- Create driving, motoric rhythms
- Include sudden dynamic contrasts
- Maintain high energy throughout
- Fill all 180 beats with continuous, intense music
```

#### Example 10: Suite of Character Pieces (320 beats)

```
Compose a suite of piano character pieces:

Title: "Four Character Pieces"
Form: suite (4 movements)
Length: approximately 320 beats total
Style/Character: Each movement has its own distinct character

Structure:
- Movement 1: "The Wanderer" (80 beats, E minor, 96 BPM, binary form) - Melancholic, searching, with a wandering melody
- Movement 2: "The Sprite" (64 beats, G major, 132 BPM, ternary form) - Playful, light, with staccato and quick passages
- Movement 3: "The Lament" (96 beats, C# minor, 56 BPM, ternary form) - Deeply expressive, slow, with rich harmonies and ornamentation
- Movement 4: "The Celebration" (80 beats, E major, 140 BPM, rondo form) - Joyful, energetic, with dance-like rhythms

Musical elements:
- Each movement should be complete and distinct
- Create strong contrast between movements in tempo, mood, and character
- Movement 1: Use a meandering, searching melody with modal inflections
- Movement 2: Light and airy, with quick scale passages and playful rhythms
- Movement 3: Very expressive, use rubato, rich chromatic harmonies, and a song-like melody
- Movement 4: Energetic and celebratory, with clear dance rhythms and bright harmonies
- Transitions between movements can be brief (1-2 beats)
- Each movement should fill its specified length with continuous music
```

#### Example 11: Slow Meditative Piece (220 beats)

```
Create a meditative piano composition:

Title: "Meditation in A Major"
Form: through-composed with recurring elements
Length: approximately 220 beats
Key: A major (with modal inflections)
Tempo: 52
Time signature: 4/4
Style/Character: meditative, serene, with sparse textures and long sustained notes

Structure:
- Opening (32 beats): Very sparse, single notes and simple intervals, establish A major
- First theme (40 beats): Gentle, flowing melody with minimal accompaniment
- Interlude (24 beats): Return to sparse texture, explore related keys
- Second theme (36 beats): Slightly more active, but still calm and contemplative
- Development (56 beats): Gradually build texture and complexity, but maintain serenity
- Return (24 beats): Return to opening material with variation
- Closing (8 beats): Fade to silence

Musical elements:
- Use very sparse textures - often single notes or simple intervals
- Include long sustained notes and pedal points
- Use modal scales (Lydian, Mixolydian) for color
- Maintain a sense of stillness and contemplation
- Avoid dramatic contrasts - keep dynamics mostly p to mp
- Use the sustain pedal extensively to create resonance
- Create a sense of timelessness and space
- Fill all 220 beats, but allow for moments of near-silence
```

#### Example 12: Complex Time Signature Piece (240 beats)

```
Compose a piano piece with complex meters:

Title: "Metrical Variations"
Form: theme and variations
Length: approximately 240 beats
Key: F# minor
Tempo: 108
Time signature: varies (5/4, 7/8, 9/8, 11/8)
Style/Character: modern, rhythmically complex, with shifting meters

Structure:
- Theme (32 beats, 5/4): Establish main melody and harmonic progression
- Variation 1 (32 beats, 7/8): Faster, more syncopated
- Variation 2 (32 beats, 9/8): Lighter, more flowing
- Variation 3 (32 beats, 11/8): More complex, with irregular groupings
- Variation 4 (32 beats, mixed meters): Combine different time signatures
- Variation 5 (32 beats, 5/4): Return to original meter with new material
- Coda (28 beats, 5/4): Extended conclusion

Musical elements:
- Each variation should explore a different time signature while maintaining the theme
- Use irregular rhythmic groupings within each meter
- Create a sense of forward motion despite the complex meters
- Maintain harmonic coherence throughout
- Use syncopation and cross-rhythms
- The theme should be recognizable in each variation
- Ensure smooth transitions between sections
- Fill all 240 beats with continuous music
```

---

# Part 2: For AI Models

This section contains the **System Prompt Template** (which you should copy into your system prompt) and optional **reference material** (Schema Reference and Example Output) that you can optionally include in your prompts if you need more detailed documentation.

- The **System Prompt Template** below is the primary content you should use - copy it into your system prompt.
- The **Schema Reference** and **Example Output** sections are optional reference material written in model-addressed language. If you include them in prompts, copy them as-is. If you're just reading them to understand the format, treat them as documentation.

## System Prompt Template

**Note for users**: Copy the template below into your system prompt. The template content is written to address the AI model directly.

**Template content (copy this into your system prompt)**:

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
      - For sustained pedaling (standard case): ALWAYS use duration > 0. This automatically creates a press at start and release at start+duration.
      - Example: {"type": "pedal", "start": 0, "duration": 4, "value": 127} holds the pedal for 4 beats.
      - Only use duration == 0 for rare special cases requiring manual control (not recommended for normal pedaling).
    - tempo: { type:"tempo", start: beats>=0,
               EITHER: bpm: number (instant tempo change at start beat)
               OR: start_bpm: number, end_bpm: number, duration: beats>0 (gradual tempo change from start_bpm to end_bpm over duration beats)
               optional: section/phrase }
    - section marker (optional but useful): { type:"section", start: beats>=0, label: string, optional: phrase }

Pitch format:
- Use MIDI numbers (0–127) OR scientific pitch strings ("C4", "F#3", "Bb2").

Time units:
- start/duration are in beats, where 1 beat == a quarter note.

Time continuity:
- Music must be continuous throughout the requested length. When a specific length is requested (e.g., "250 beats"), fill that entire duration with music, not silence.
- Avoid large gaps or silences between sections. Brief pauses (1-2 beats) between phrases are acceptable, but sections should flow continuously.
- Transitions between sections should be musical (e.g., connecting passages, cadential extensions, or brief modulatory bridges), not empty space.
- If the user requests "about 250 beats", generate approximately 250 beats of actual music. The last event's start + duration should be close to the requested length.
- Plan section lengths proportionally: for a 250-beat sonata, exposition might be 60-80 beats, development 80-100 beats, recapitulation 60-80 beats, with transitions filling any remaining space.

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

Sustain pedal:
- Use sustain pedal events to create rich, sustained sound, especially in lyrical passages, legato sections, and when creating harmonic resonance.
- ALWAYS use `duration > 0` for pedal events (e.g., `{"type": "pedal", "start": 0, "duration": 4, "value": 127}`). This automatically creates proper press-release pairs.
- Change pedal at chord changes to maintain clarity - end one pedal event's duration and start a new one at the chord change.
- For legato pedaling, overlap pedal events slightly (new pedal starts 0.1 beats before previous ends).
- Do NOT use `duration: 0` for sustained pedaling - this creates instant actions without automatic release.

Rhythm:
- Prefer simple rhythmic grids first (quarters/eighths), then add syncopation for interest where appropriate.

Tempo changes:
- Use tempo events to create ritardando (slowing down) or accelerando (speeding up) effects when musically appropriate.
- For instant tempo changes: use `{ type: "tempo", start: <beat>, bpm: <new_tempo> }` to change tempo immediately at a specific beat.
- For gradual tempo changes: use `{ type: "tempo", start: <beat>, start_bpm: <initial>, end_bpm: <final>, duration: <beats> }` to gradually change tempo over a duration. This is useful for ritardando at endings, accelerando in transitions, or expressive tempo flexibility.
- Tempo events can be placed in any track; they will be automatically collected and rendered in the conductor track.
- Use tempo changes musically: ritardando at phrase endings or final cadences, accelerando in transitions or climactic sections, or tempo flexibility for expressive purposes.

Output quality:
- Prefer events sorted by start time (not required, but reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start` time.
- Ensure all harmonies are complete and properly voiced.
- Maintain consistent key centers within sections unless intentionally modulating.
- Use the `section` annotation field liberally to mark formal divisions—it helps organize thinking even if it doesn't affect playback.
- CRITICAL: Fill the entire requested length with continuous music. The last event's (start + duration) should be close to the requested length (e.g., if 250 beats requested, last event should end around beat 250, not beat 50 with 200 beats of silence).
```

## Schema Reference

**Note for users**: The schema reference below provides detailed technical information about the JSON format. You can optionally include relevant portions in your system prompt if you need more detailed schema documentation than what's in the template above. The content below is written to address the AI model directly, so if you include it in a prompt, copy it as-is.

### High-Level Structure

The output JSON must have the following structure:

- Top level: `title`, `bpm`, `time_signature`, optional `key_signature`, `ppq`, `tracks`
- Each `track` has `name`, `program` (0=piano), `channel`, and `events`
- Each `event` is either:
  - `type: "note"` with `start` (beats), `duration` (beats), `velocity`, and pitch content in ONE of:
    - **Preferred**: `groups` (sub-chords with shared `hand`/`voice`)
    - **Preferred**: `notes` (per-note `hand`/`voice`)
    - Legacy: `pitches` / `pitch` (no per-note labeling)
  - `type: "pedal"` with `start`, `duration`, optional `value` (see **Sustain Pedal Control** below)
  - `type: "tempo"` with `start` (beats), and EITHER:
    - `bpm` (instant tempo change), OR
    - `start_bpm`, `end_bpm`, `duration` (gradual tempo change)
  - `type: "section"` with `start` (beats) and `label` (string) for section markers (ignored during rendering, useful for iteration/editing)

Optional annotation fields (do not affect rendering): `motif`, `section`, `phrase`.

### Pitch Format

You may provide pitches as:
- MIDI numbers (0–127), or
- scientific pitch strings (`"C4"`, `"F#3"`, `"Bb2"`)

Internally Pianist validates and converts pitches to MIDI numbers.

### Sustain Pedal Control

When generating sustain pedal events, ALWAYS use `duration > 0` for sustained pedaling. This is the standard pattern that automatically creates proper press-release pairs in the MIDI output.

**Standard Pattern (ALWAYS use this for sustained pedaling)**:
- Use `duration > 0` to specify how long the pedal should be held down
- The renderer automatically creates a press (CC64=127) at `start` and a release (CC64=0) at `start + duration`
- Example: `{"type": "pedal", "start": 0, "duration": 4, "value": 127}` holds the pedal for 4 beats
- `value` defaults to 127 (full pedal down) if not specified

**Common Pedaling Patterns**:
- Hold pedal for a measure (4 beats): `{"type": "pedal", "start": 0, "duration": 4, "value": 127}`
- Hold pedal for a phrase (8 beats): `{"type": "pedal", "start": 0, "duration": 8, "value": 127}`
- Change pedal with harmony: Create new pedal events at chord changes (release previous by ending its duration, start new at the chord change)
- Legato pedaling: Overlap pedal events slightly (e.g., new pedal starts 0.1 beats before previous ends)

**CRITICAL: What NOT to generate**:
- ❌ Do NOT use `duration: 0` for sustained pedaling - this creates instant actions without automatic release and results in missing sustain control
- ❌ Do NOT create separate press/release events manually - use `duration > 0` instead
- ❌ Do NOT forget to release the pedal - always specify a `duration` that ends before or at the next chord change

**Advanced (rare cases only)**:
- `duration: 0` is only for special cases requiring manual control (not recommended for normal pedaling)

### Hand/Voice Labeling

For piano writing, keep a **single Piano track** and label each generated note (or sub-chord) with:
- `hand`: `"lh"` or `"rh"` (required in `notes` / `groups`)
- `voice`: optional integer 1–4 (useful for downstream notation/analysis)

## Example Output

**Note for users**: The examples below show valid JSON output format. You can optionally include these examples in your system prompt to help the model understand the expected output structure. The content below is written to address the AI model directly, so if you include it in a prompt, copy it as-is.

Here are examples of valid JSON output you should generate:

### Basic Example

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
        { "type": "pedal", "start": 0, "duration": 4, "value": 127, "section": "A" },
        { "type": "tempo", "start": 120, "start_bpm": 84, "end_bpm": 60, "duration": 8, "section": "A" }
      ]
    }
  ]
}
```

### Example with Tempo Changes

```json
{
  "title": "Dramatic Piece with Ritardando",
  "bpm": 120,
  "time_signature": { "numerator": 4, "denominator": 4 },
  "key_signature": "C minor",
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
          "velocity": 80,
          "groups": [{ "hand": "rh", "pitches": ["C4"] }]
        },
        {
          "type": "tempo",
          "start": 60,
          "bpm": 100,
          "section": "middle"
        },
        {
          "type": "tempo",
          "start": 120,
          "start_bpm": 100,
          "end_bpm": 60,
          "duration": 16,
          "section": "ending"
        }
      ]
    }
  ]
}
```
