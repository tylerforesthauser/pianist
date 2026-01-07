# `reference` Command

## Purpose

Manage the musical reference database. The reference database stores example compositions that can be used to guide AI expansion, demonstrating techniques like motif development, phrase extension, transitions, and form structures.

## Syntax

```bash
pianist reference <subcommand> [options]
```

## Subcommands

### `add` - Add a Reference

Add a composition to the reference database.

```bash
pianist reference add -i <composition.json> [options]
```

**Options:**
- `-i, --input` - Input composition JSON file (required)
- `--id` - Reference ID (auto-generated from title if not provided)
- `--title` - Reference title (uses composition title if not provided)
- `--description` - Description of the reference
- `--style` - Musical style (e.g., Baroque, Classical, Romantic, Modern)
- `--form` - Musical form (e.g., binary, ternary, sonata)
- `--techniques` - Comma-separated list of techniques (e.g., `sequence,inversion,augmentation`)

**Examples:**

```bash
# Add a reference with metadata
pianist reference add -i example.json \
  --id motif_sequence_example \
  --description "Demonstrates sequential motif development" \
  --style Classical \
  --form binary \
  --techniques sequence,motif_development

# Add with auto-generated ID
pianist reference add -i example.json \
  --description "Phrase extension example" \
  --style Romantic
```

### `list` - List All References

List all references in the database.

```bash
pianist reference list
```

**Example:**

```bash
pianist reference list
```

### `search` - Search References

Search for references matching specific criteria.

```bash
pianist reference search [options]
```

**Options:**
- `--style` - Filter by musical style
- `--form` - Filter by musical form
- `--technique` - Filter by technique
- `--title-contains` - Filter by title substring
- `--description-contains` - Filter by description substring
- `--limit` - Maximum number of results (default: 10)

**Examples:**

```bash
# Search by style
pianist reference search --style Classical

# Search by technique
pianist reference search --technique sequence

# Search by form
pianist reference search --form ternary

# Combine filters
pianist reference search --style Classical --technique sequence --limit 5
```

### `get` - Get a Reference

Retrieve a reference by ID and output its composition.

```bash
pianist reference get <id> [-o <output.json>]
```

**Options:**
- `id` - Reference ID (required)
- `-o, --output` - Output JSON path (prints to stdout if omitted)

**Examples:**

```bash
# Get and print to stdout
pianist reference get motif_sequence_example

# Get and save to file
pianist reference get motif_sequence_example -o retrieved.json
```

### `delete` - Delete a Reference

Delete a reference from the database.

```bash
pianist reference delete <id>
```

**Example:**

```bash
pianist reference delete old_reference_id
```

### `count` - Count References

Get the total number of references in the database.

```bash
pianist reference count
```

**Example:**

```bash
pianist reference count
```

## How It Works

The reference database is stored in SQLite at `~/.pianist/references.db`. Each reference includes:

- **Composition**: The full composition JSON
- **Metadata**: Style, form, techniques, description
- **Searchable fields**: All metadata fields are indexed for fast searching

When you use `pianist expand` with an AI provider, the system automatically:

1. Analyzes your composition
2. Finds relevant references based on style, form, and detected patterns
3. Includes up to 3 relevant references in the expansion prompt
4. Provides the reference compositions as examples for the AI to learn from

## Use Cases

1. **Build a Library of Examples**: Add compositions that demonstrate specific techniques
2. **Style-Specific Expansion**: Add examples for different musical styles
3. **Technique Examples**: Add examples showing motif development, phrase extension, transitions
4. **Form Examples**: Add examples of different musical forms (binary, ternary, sonata, etc.)

## Integration

- **Automatic Integration**: References are automatically used by `expand` command when available
- **Manual Curation**: Use `add` to build your reference library
- **Search**: Use `search` to find relevant examples before expansion

## Initial Examples

Run the initialization script to add some basic examples:

```bash
python3 scripts/add_initial_references.py
```

This adds examples for:
- Motif sequence development
- Phrase extension
- Section transitions

## See Also

- [`expand`](./expand.md) - Uses references automatically during expansion
- [`analyze`](./analyze.md) - Analyze compositions before adding as references

