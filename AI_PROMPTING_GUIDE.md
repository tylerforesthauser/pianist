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

**Important considerations for cohesive compositions:**
- **Thematic coherence**: When requesting longer works or multiple sections, emphasize that all themes should relate through motivic development. For example: "Develop 1-2 main motifs throughout all sections" or "Ensure all themes relate to the opening material."
- **Continuous music**: The system prompt already emphasizes this, but you can reinforce it by requesting "continuous music with no gaps between sections" or "smooth transitions throughout."
- **Regular phrase structure**: For works that need structural clarity, you can request "regular phrase lengths (4, 8, or 16 beats)" or "consistent measure structure within each section."

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
- Introduce 1-2 primary motifs in the exposition. These motifs MUST be developed and referenced throughout all sections (exposition, development, recapitulation). Every theme must relate to these motifs.
- Build dynamics: quiet opening → powerful climax in development → greater intensity in recapitulation
- Second theme should contrast but still relate to primary motifs through development techniques
- Use proper voice leading and functional harmony throughout
- Use regular phrase structure (4, 8, or 16 beats) with consistent lengths within each section
- Fill all 250 beats with continuous music—no gaps between sections, maximum 2-beat pauses only between phrases
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
- Each variation must transform the theme while remaining recognizable. All variations must relate to the original theme—avoid introducing completely unrelated material.
- Use different textures: homophonic, polyphonic, melody with accompaniment
- Explore different registers and hand distributions
- Build dynamic intensity: peak in variation 6, then reflective variation 7
- Use regular phrase structure (4, 8, or 16 beats) consistently within each variation
- Include smooth transitions between variations (2-4 beats each)
- Fill all 300 beats with continuous music—no gaps between variations
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
- Main theme should be catchy and easily recognizable when it returns
- Episodes contrast: B more lyrical, C more dramatic
- Modulate: A major → D major → A major → F# minor → A major
- Vary theme returns: first identical, later with variations or different dynamics
- Build energy: final A section most energetic
- Maintain 6/8 dance-like character throughout
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
- A section: memorable, flowing melody
- B section: strong contrast (different key, mood, texture)
- Dynamics: quiet opening → climax in B → greater depth in A'
- Tempo flexibility: slight ritardando at phrase endings, especially in A'
- Use pedal throughout for rich, sustained sound
- Smooth transitions between sections
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
- Each movement complete and satisfying, but also works as part of the whole
- Contrast between movements: fast-slow-dance-fast pattern
- Movement 1: Sonata form with clear themes, development, recapitulation
- Movement 2: Very expressive, rich harmonies, full dynamic range
- Movement 3: Light, dance-like, with contrasting trio section
- Movement 4: Brilliant, energetic conclusion
- Transitions between movements: brief (1-2 beats) or seamless
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
- Narrative arc: mysterious beginning → lyrical theme → energetic contrast → dramatic development → return with resolution
- Use 1-2 main motifs introduced early. ALL sections must develop and reference these motifs—avoid unrelated themes. The composition must sound cohesive, not like separate pieces.
- Climax in development section (around beat 120-140)
- Dynamics: p → mf → f → ff (climax) → mf → p
- Tempo changes: slight accelerando in development, ritardando in coda
- Use regular phrase structure (4, 8, or 16 beats) consistently within each section
- Smooth transitions between all sections—no gaps, maximum 2-beat pauses only between phrases
- Fill all 250 beats with continuous music
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
- Ground bass clearly audible in every variation
- Each variation builds in complexity while maintaining the bass pattern
- Use proper Baroque counterpoint: avoid parallel fifths, maintain voice independence
- Final coda brings the work to a satisfying conclusion
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
- Highly ornamented melodies with trills, turns, appoggiaturas
- Dramatic dynamic contrasts (pp to ff)
- Extensive rubato and tempo flexibility
- Rich chromatic harmonies and modulations
- Virtuosic passages requiring technical skill
- Sense of improvisation and freedom
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
- Percussive, staccato attacks and sharp accents
- Complex rhythms: syncopation, polyrhythms, metric shifts
- Dissonant harmonies and cluster chords
- Full range of piano with wide leaps
- Driving, motoric rhythms
- Sudden dynamic contrasts
- Maintain high energy throughout
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
- Transitions between movements: brief (1-2 beats)
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
- Very sparse textures: single notes or simple intervals
- Long sustained notes and pedal points
- Modal scales (Lydian, Mixolydian) for color
- Sense of stillness and contemplation
- Avoid dramatic contrasts: keep dynamics mostly p to mp
- Extensive sustain pedal for resonance
- Sense of timelessness and space
- Allow for moments of near-silence
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
- Each variation explores a different time signature while maintaining the theme
- Irregular rhythmic groupings within each meter
- Forward motion despite complex meters
- Maintain harmonic coherence throughout
- Syncopation and cross-rhythms
- Theme recognizable in each variation
- Smooth transitions between sections
```

---

# Part 2: For AI Models

This section contains the **System Prompt Template** (copy into your system prompt) and optional **reference material** (Schema Reference and Example Output) for more detailed documentation.

- **System Prompt Template**: Primary content—copy into your system prompt.
- **Schema Reference** and **Example Output**: Optional reference material in model-addressed language. If including in prompts, copy as-is. Otherwise, treat as documentation.

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

Time continuity (CRITICAL):
- Fill the ENTIRE requested length with continuous music. NO large gaps or silences between sections.
- Maximum gap between notes: 1 beat (professional compositions average 0.01 beats; 1 beat is generous but ensures continuity).
- Maximum gap at section boundaries: 2 beats (95th percentile from analysis of 50 professional compositions).
- Mean gap between notes should be < 0.1 beats (professional average: 0.01 beats).
- Use musical transitions (connecting passages, cadential extensions, modulatory bridges) between sections—NEVER empty space.
- The last event's (start + duration) MUST be within 5 beats of the requested length.
- Plan section lengths proportionally (e.g., 250-beat sonata: exposition 60-80, development 80-100, recapitulation 60-80, transitions ~20).
- If requested length is 250 beats, generate approximately 250 beats of actual music, not 200 beats with 50 beats of silence.
- Before outputting, verify: no gap between consecutive notes exceeds 1 beat; no gap at section boundaries exceeds 2 beats.

Section transitions (CRITICAL):
- Sections must connect seamlessly with MUSICAL MATERIAL, never with silence or empty space.
- Transitions are connecting musical passages (not silence) that bridge sections.
- Typical transition length: 4-9 beats (25th-75th percentile from analysis of professional compositions).
- Maximum transition length: 17 beats (observed maximum in professional compositions).
- Transition techniques:
  * Use sequences: repeat a motif from the previous section, modulating to the new key
  * Use scale passages or arpeggios to bridge sections smoothly
  * Extend the cadence of the previous section with additional material that leads into the next section
  * Fragment the main motif and use it as a bridge
  * Maintain harmonic motion—avoid static harmony at section boundaries
  * Keep rhythmic activity—avoid long sustained notes at section boundaries unless musically justified (e.g., dramatic pause before a new section)
- Overlap material when possible: if a section ends with a long-held note, begin the next section's material before the previous note ends, or add connecting material.
- Before outputting, verify: no section boundary has more than 2 beats of silence; the last event of one section and the first event of the next section should be connected by musical material.

Compositional approach:

Motivic development and thematic coherence (CRITICAL):
- Introduce 1-2 short (2-8 notes), memorable, distinctive motifs in the first 8-16 beats. These motifs MUST be developed and referenced throughout the entire composition.
- Every new theme or section should relate to the original motifs through development techniques (transposition, inversion, augmentation, diminution, fragmentation, sequence, rhythmic variation).
- Avoid introducing completely unrelated themes. If a contrasting section is needed, derive it from the original motifs or create clear motivic connections.
- The composition must sound like a SINGLE COHESIVE WORK, not a collection of unrelated ideas. Maintain thematic relationships throughout.
- Motifs should appear frequently throughout the composition. Motifs should not repeat in identical form more than 2-3 times consecutively—always vary at least one element (rhythm, pitch via transposition, texture, or harmony).
- Typical spacing between motif appearances: 1-16 beats. Space out exact repetitions: at least 4-8 beats between identical appearances.
- Adhere to established formal principles (binary, ternary, sonata, rondo, theme and variations, etc.) as appropriate.
- Use clear, regular phrase structure (typically 4, 8, or 16 beats) with antecedent-consequent relationships. Maintain consistent phrase lengths within sections.
- For longer works, plan structure first, then fill in details, ensuring motifs are developed across all sections.
- Mark formal sections using the `section` field (e.g., "exposition", "A", "development", "B", "recapitulation").
- Create contrast between sections (keys, textures, moods, registers) with musical transitions that maintain motivic connections.
- Maintain larger-scale coherence through motivic development and key relationships.

Harmony and voice leading:
- Functional harmony: Use proper chord progressions (I, ii, iii, IV, V, vi, vii°). Establish clear tonic-dominant relationships. Use secondary dominants (V/V, V/vi, etc.) and borrowed chords for color.
- Voice leading: Maintain smooth, stepwise motion. Avoid parallel fifths and octaves. Resolve leading tones upward (ti→do) and sevenths downward. Keep common tones when possible.
- Cadences: Use authentic (V→I) at phrase endings, half (ending on V) for continuation, plagal (IV→I) for closure, deceptive (V→vi) for surprise.
- Dissonance: Properly prepare and resolve dissonances (suspensions, appoggiaturas, passing tones). Use non-chord tones (passing, neighbor, escape, anticipation) for melodic interest while maintaining harmonic clarity.
- Harmonic rhythm: Vary chord change frequency—faster in active sections, slower in lyrical passages.
- Modulation: Use pivot chords, common-tone modulations, or direct modulations with proper preparation. Return to home key for structural closure.

Melody and counterpoint:
- Create melodic lines with clear direction and contour. Use non-chord tones for interest while maintaining harmonic clarity.
- With multiple voices, maintain independence while respecting harmonic function. Use contrary motion, avoid voice crossing, maintain appropriate spacing.

Texture and voicing:
- Balance melody and accompaniment. Left hand: harmonic foundation (bass + chord tones). Right hand: melody. Vary texture (homophonic, polyphonic, monophonic).
- Use appropriate spacing between hands. Utilize full piano range with clear bass and treble separation.
- Use a single Piano track with `groups` (preferred) or `notes`, labeling each note with `hand` ("lh"/"rh") and optional `voice` (1-4).

Dynamics and expression:
- Use velocity (p → mf → f and back) to shape phrases and sections.
- Build to climaxes: shape larger arcs, create tension and release across the work.

Sustain pedal:
- Use pedal events for rich, sustained sound, especially in lyrical passages and legato sections.
- ALWAYS use `duration > 0` (e.g., `{"type": "pedal", "start": 0, "duration": 4, "value": 127}`). This automatically creates press-release pairs.
- Change pedal at chord changes: end one pedal's duration and start a new one at the chord change.
- For legato pedaling, overlap slightly (new pedal starts 0.1 beats before previous ends).
- Do NOT use `duration: 0` for sustained pedaling.

Rhythm and phrase structure:
- Prefer simple rhythmic grids (quarters/eighths), then add syncopation where appropriate.
- Use regular, consistent phrase lengths within each section (typically 4, 8, or 16 beats).
- Maintain consistent measure structure: phrases should align with measure boundaries (e.g., 4-beat phrases in 4/4, 6-beat phrases in 6/8).
- While occasional phrase extensions or contractions are acceptable, avoid erratic, inconsistent phrase lengths that create an unstable rhythmic feel.
- Group phrases into larger units (e.g., two 8-beat phrases = 16-beat phrase group).
- Ensure cadences align with phrase endings and measure boundaries for structural clarity.

Tempo changes:
- Use tempo events for ritardando or accelerando when musically appropriate.
- Instant: `{ type: "tempo", start: <beat>, bpm: <new_tempo> }`
- Gradual: `{ type: "tempo", start: <beat>, start_bpm: <initial>, end_bpm: <final>, duration: <beats> }`
- Tempo events can be placed in any track; automatically collected in conductor track.
- Use musically: ritardando at phrase endings/cadences, accelerando in transitions/climaxes.

Output quality:
- Prefer events sorted by start time (reduces mistakes).
- For chords, use `groups: [{hand:"rh", pitches:["C4","E4","G4"]}]` at the same `start` time.
- Ensure harmonies are complete and properly voiced.
- Maintain consistent key centers within sections unless intentionally modulating.
- Use the `section` annotation field liberally to mark formal divisions.
- CRITICAL: Fill the entire requested length with continuous music. Last event's (start + duration) must be within 5 beats of requested length.
- CRITICAL: Maximum gap between notes: 1 beat. Maximum gap at section boundaries: 2 beats. Mean gap should be < 0.1 beats.
- CRITICAL: Maintain thematic coherence—all sections must relate through motivic development, not unrelated ideas.
- CRITICAL: Use regular phrase structure (4, 8, or 16 beats) with consistent lengths within sections. Avoid erratic, inconsistent phrase lengths.
- CRITICAL: Sections must connect with musical transitions (4-9 beats typical), never with silence or empty space.
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

ALWAYS use `duration > 0` for sustained pedaling. This automatically creates press-release pairs in MIDI output.

**Standard Pattern**:
- Use `duration > 0` to specify how long the pedal is held
- Renderer creates press (CC64=127) at `start` and release (CC64=0) at `start + duration`
- Example: `{"type": "pedal", "start": 0, "duration": 4, "value": 127}` holds pedal for 4 beats
- `value` defaults to 127 if not specified

**Common Patterns**:
- Measure (4 beats): `{"type": "pedal", "start": 0, "duration": 4, "value": 127}`
- Phrase (8 beats): `{"type": "pedal", "start": 0, "duration": 8, "value": 127}`
- Change with harmony: End previous pedal's duration, start new at chord change
- Legato: Overlap slightly (new pedal starts 0.1 beats before previous ends)

**CRITICAL: What NOT to generate**:
- ❌ Do NOT use `duration: 0` for sustained pedaling (creates instant actions without automatic release)
- ❌ Do NOT create separate press/release events manually (use `duration > 0` instead)
- ❌ Do NOT forget to release the pedal (specify `duration` ending before/at next chord change)

**Advanced (rare cases only)**:
- `duration: 0` only for special cases requiring manual control (not recommended)

### Hand/Voice Labeling

For piano writing, keep a **single Piano track** and label each generated note (or sub-chord) with:
- `hand`: `"lh"` or `"rh"` (required in `notes` / `groups`)
- `voice`: optional integer 1–4 (useful for downstream notation/analysis)

## Example Output

**Note for users**: Examples show valid JSON output format. Optionally include in system prompts. Content is model-addressed—copy as-is if including in prompts.

Examples of valid JSON output:

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
