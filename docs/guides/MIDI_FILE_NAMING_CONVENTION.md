# MIDI File Naming Convention

This document defines the standard naming convention for MIDI files added to the reference database. Following this convention ensures accurate composer and work identification.

---

## Standard Format

### Format Pattern

```
[Composer] - [Title] [Catalog Number] [Additional Info].mid
```

### Components

1. **Composer** (required for known works)
   - Use canonical composer name
   - Examples: "J.S. Bach", "Mozart", "Chopin", "Scott Joplin"
   - See [Composer Name Standards](#composer-name-standards) below

2. **Title** (required)
   - Work title or movement name
   - Use standard English titles when available
   - Examples: "Prelude in C major", "Maple Leaf Rag", "Sonata No. 16"

3. **Catalog Number** (optional but recommended)
   - Opus numbers, BWV, K., etc.
   - Format: "Op. 28 No. 7", "BWV 772", "K. 545"
   - Place after title, in parentheses if needed

4. **Additional Info** (optional)
   - Movement numbers, alternative titles, etc.
   - Examples: "1st movement", "from Well-Tempered Clavier"

5. **File Extension**
   - Always use `.mid` extension

---

## Examples

### Classical Works

✅ **Good Examples:**
```
J.S. Bach - Two-Part Invention No. 1 in C major BWV 772.mid
Mozart - Piano Sonata No. 16 in C major K. 545 1st movement.mid
Chopin - Prelude in A major Op. 28 No. 7.mid
Beethoven - Piano Sonata No. 8 Pathétique Op. 13 1st movement.mid
```

✅ **With Alternative Formatting:**
```
J.S. Bach - Invention No. 1 BWV 772.mid
Mozart - Sonata K. 545 1st movement.mid
Chopin - Prelude Op. 28 No. 7.mid
```

### Modern/Contemporary Works

✅ **Good Examples:**
```
Scott Joplin - Maple Leaf Rag.mid
George Gershwin - Three Preludes No. 1.mid
Béla Bartók - Mikrokosmos No. 6.mid
Sergei Prokofiev - Visions fugitives Op. 22 No. 1.mid
```

### Works Without Clear Composer

For works where composer is unknown or you want to use AI identification:

✅ **Good Examples:**
```
Unknown - Elegiac Prelude in E-flat minor.mid
Traditional - Folk Song Arrangement.mid
Original - Modern Composition No. 1.mid
```

❌ **Avoid:**
```
output4_unknown.mid
gen-3-cef265_unknown.mid
untitled.mid
file1.mid
```

---

## Composer Name Standards

Use these canonical names for consistency:

### Baroque
- `J.S. Bach` (not "Johann Sebastian Bach" or "Bach")
- `George Frideric Handel` (or "Handel" if unambiguous)
- `Domenico Scarlatti` (or "Scarlatti" if unambiguous)

### Classical
- `Mozart` (not "W.A. Mozart" or "Wolfgang Amadeus Mozart")
- `Beethoven` (not "Ludwig van Beethoven")
- `Joseph Haydn` (or "Haydn" if unambiguous)
- `Muzio Clementi` (or "Clementi" if unambiguous)

### Romantic
- `Chopin` (not "Frédéric Chopin")
- `Robert Schumann` (or "Schumann" if unambiguous)
- `Felix Mendelssohn` (or "Mendelssohn" if unambiguous)
- `Liszt` (not "Franz Liszt")
- `Brahms` (not "Johannes Brahms")

### Late Romantic/Post-Romantic
- `César Franck`
- `Gabriel Fauré`
- `Edvard Grieg`
- `Sergei Rachmaninoff` (or "Rachmaninoff")
- `Alexander Scriabin` (or "Scriabin")

### Impressionist
- `Claude Debussy` (or "Debussy")
- `Maurice Ravel` (or "Ravel")
- `Erik Satie` (or "Satie")

### Modern
- `Béla Bartók` (or "Bartók")
- `Igor Stravinsky` (or "Stravinsky")
- `Arnold Schoenberg` (or "Schoenberg")
- `Sergei Prokofiev` (or "Prokofiev")
- `Dmitri Shostakovich` (or "Shostakovich")

### American
- `Scott Joplin`
- `George Gershwin`
- `Aaron Copland`
- `Charles Ives`
- `Amy Beach`
- `Florence Price`

### Jazz/Ragtime
- `Scott Joplin`
- `James Scott`
- `Jelly Roll Morton`
- `Fats Waller`

---

## Separator Options

You can use different separators, but be consistent:

### Option 1: Dash Separator (Recommended)
```
Composer - Title Catalog.mid
```
Example: `Chopin - Prelude Op. 28 No. 7.mid`

### Option 2: Double Dash Separator
```
Composer -- Title Catalog.mid
```
Example: `Chopin -- Prelude Op. 28 No. 7.mid`

### Option 3: Underscore Separator
```
Composer_Title_Catalog.mid
```
Example: `Chopin_Prelude_Op_28_No_7.mid`

**Note:** The script recognizes all these formats, but dash separators are preferred for readability.

---

## Catalog Number Formats

### Opus Numbers
- `Op. 28 No. 7` (preferred)
- `Op.28 No.7` (also accepted)
- `Opus 28 No. 7` (also accepted)

### BWV (Bach)
- `BWV 772` (preferred)
- `BWV772` (also accepted)

### Köchel (Mozart)
- `K. 545` (preferred)
- `K.545` (also accepted)
- `KV 545` (also accepted)

### Hoboken (Haydn)
- `Hob. XVI:35` (preferred)
- `Hob XVI:35` (also accepted)

### Other Catalog Systems
- Use standard format: `Catalog Prefix Number`
- Examples: `D. 664` (Schubert), `L. 117` (Debussy), `Wq. 49/1` (C.P.E. Bach)

---

## Special Cases

### Original/Unknown Compositions

For original compositions or works where composer is unknown:

**Format:**
```
Original - [Descriptive Title].mid
Unknown - [Descriptive Title].mid
Traditional - [Title].mid
```

**Examples:**
```
Original - Modern Composition in E-flat minor.mid
Unknown - Elegiac Prelude.mid
Traditional - Folk Song Arrangement.mid
```

**Why:** The script will recognize these prefixes and handle them appropriately, using AI identification if needed.

### Works with Multiple Movements

**Option 1: Separate Files**
```
Composer - Work Title Movement 1.mid
Composer - Work Title Movement 2.mid
Composer - Work Title Movement 3.mid
```

**Option 2: Combined with Movement Number**
```
Composer - Work Title 1st movement.mid
Composer - Work Title 2nd movement.mid
Composer - Work Title 3rd movement.mid
```

**Option 3: Movement in Title**
```
Composer - Work Title - Movement Name.mid
```

### Collections and Sets

**Format:**
```
Composer - Collection Name No. X.mid
```

**Examples:**
```
Chopin - 24 Preludes Op. 28 No. 7.mid
Bach - Well-Tempered Clavier Book 1 Prelude 1 BWV 846.mid
Bartók - Mikrokosmos No. 6.mid
```

---

## What to Avoid

### ❌ Generic Names
```
output1.mid
file.mid
untitled.mid
composition.mid
midi_file.mid
```

### ❌ Cryptic Names
```
gen-3-cef265_unknown.mid
output4_unknown.mid
temp_file.mid
test.mid
```

### ❌ Inconsistent Formatting
```
chopin-prelude-op28-no7.mid  (missing spaces, inconsistent)
Chopin Prelude Op 28 No 7.mid  (missing punctuation)
chopin_prelude_op_28_no_7.mid  (OK but less readable)
```

### ❌ Missing Composer (for known works)
```
Prelude in A major Op. 28 No. 7.mid  (missing composer)
Sonata K. 545.mid  (missing composer)
```

---

## Renaming Existing Files

If you have files with generic names, rename them before adding to the reference database:

### Before → After Examples

```
output4_unknown.mid
→ Original - Elegiac Prelude in E-flat minor.mid

gen-3-cef265_unknown.mid
→ Unknown - Modern Composition in D minor.mid

chopin---prelude-no.-7-in-a-major-op.-28.mid
→ Chopin - Prelude in A major Op. 28 No. 7.mid

j.s.-bach---invention-no.-1-bwv-772.mid
→ J.S. Bach - Invention No. 1 BWV 772.mid
```

### Renaming Script

You can use a simple script to batch rename files:

```bash
# Example: Rename generic files
for file in output*.mid; do
    # Extract info and rename
    mv "$file" "Original - $(basename "$file" .mid | sed 's/output[0-9]*_//').mid"
done
```

---

## Alternative: Metadata JSON Files

Instead of renaming files, you can create companion JSON metadata files (`filename.mid.json`) with explicit metadata. This is especially useful for:
- Files with generic names you don't want to rename
- Modern works that don't fit standard naming patterns
- Batch imports where renaming is impractical

**See [`MIDI_IDENTIFICATION_IMPLEMENTATION.md`](MIDI_IDENTIFICATION_IMPLEMENTATION.md) for details on metadata JSON files.**

## Integration with Review Script

The `review_and_categorize_midi.py` script automatically:

1. **Extracts composer** from filename using patterns
2. **Extracts title** from filename
3. **Extracts catalog numbers** (BWV, Op., K., etc.)
4. **Falls back to AI identification** if filename doesn't contain clear info
5. **Marks as original** if filename contains "original", "unknown", etc.

### How the Script Parses Names

The script recognizes these patterns:

1. **Composer at end:** `Title -- Composer.mid` or `Title - Composer.mid`
2. **Composer at start:** `Composer - Title.mid`
3. **Composer anywhere:** Simple pattern matching (e.g., "bach", "chopin")
4. **Catalog numbers:** BWV, Op., K., Hob., etc.

### Best Practices for Script Compatibility

1. **Put composer first or last** (not in middle)
2. **Use standard composer names** (see [Composer Name Standards](#composer-name-standards))
3. **Include catalog numbers** when available
4. **Use descriptive titles** for unknown works
5. **Avoid special characters** that might cause issues (use ASCII)

---

## Checklist Before Adding Files

Before adding MIDI files to the reference database:

- [ ] File follows naming convention: `[Composer] - [Title] [Catalog].mid`
- [ ] Composer name uses canonical form (see standards above)
- [ ] Title is descriptive and clear
- [ ] Catalog number included if available
- [ ] No generic names (output, file, untitled, etc.)
- [ ] File extension is `.mid`
- [ ] Special characters are ASCII-safe

---

## Examples by Category

### Baroque
```
J.S. Bach - Invention No. 1 BWV 772.mid
J.S. Bach - Prelude in C major BWV 846.mid
Handel - Suite in D minor HWV 437 Allemande.mid
Scarlatti - Sonata in D minor K. 9.mid
```

### Classical
```
Mozart - Piano Sonata No. 16 K. 545 1st movement.mid
Haydn - Piano Sonata Hob. XVI:35 1st movement.mid
Beethoven - Piano Sonata No. 8 Pathétique Op. 13 1st movement.mid
Clementi - Sonatina Op. 36 No. 1.mid
```

### Romantic
```
Chopin - Nocturne in E-flat major Op. 9 No. 2.mid
Schumann - Kinderszenen Op. 15 No. 7 Träumerei.mid
Mendelssohn - Songs Without Words Op. 19 No. 1.mid
Liszt - Liebestraum No. 3.mid
```

### Late Romantic
```
Franck - Prélude Choral et Fugue.mid
Fauré - Nocturne No. 1 Op. 33 No. 1.mid
Grieg - Lyric Pieces Op. 12 No. 1.mid
Rachmaninoff - Prelude in C-sharp minor Op. 3 No. 2.mid
```

### Impressionist
```
Debussy - Préludes Book 1 No. 8 La fille aux cheveux de lin.mid
Ravel - Jeux d'eau.mid
Satie - Gymnopédie No. 1.mid
```

### Modern
```
Bartók - Mikrokosmos No. 6.mid
Prokofiev - Visions fugitives Op. 22 No. 1.mid
Stravinsky - Piano Sonata 1st movement.mid
Schoenberg - Six Little Piano Pieces Op. 19 No. 1.mid
```

### Jazz/Ragtime
```
Scott Joplin - Maple Leaf Rag.mid
Scott Joplin - The Entertainer.mid
James Scott - Frog Legs Rag.mid
Jelly Roll Morton - Original Jelly Roll Blues.mid
```

### American
```
George Gershwin - Three Preludes No. 1.mid
Aaron Copland - Piano Variations.mid
Charles Ives - Three Page Sonata.mid
Amy Beach - Piano Sonata Op. 34.mid
```

### Original/Unknown
```
Original - Modern Composition in E-flat minor.mid
Unknown - Elegiac Prelude.mid
Traditional - Folk Song Arrangement.mid
```

---

## Summary

**Standard Format:**
```
[Composer] - [Title] [Catalog Number].mid
```

**Key Principles:**
1. Always include composer (or "Original"/"Unknown" prefix)
2. Use canonical composer names
3. Include catalog numbers when available
4. Use descriptive titles
5. Avoid generic names
6. Be consistent with separators

**Benefits:**
- Accurate composer identification
- Better organization
- Easier searching and filtering
- Reduced need for AI identification
- Consistent database structure

---

**Last Updated:** Initial creation  
**Next Review:** After implementation and testing

