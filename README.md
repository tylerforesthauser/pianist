# aimusicgen

`aimusicgen` is the package inside this repository (repo name: `pianist`).

A small framework to **turn AI model outputs into playable MIDI** (piano compositions).

## Design goals

- **Let the model “compose”** using theory/form/motifs (free-form reasoning), but require a **strict JSON output** for rendering.
- Use established libraries where it makes sense:
  - **Pydantic**: schema validation and type coercion
  - **json-repair**: repair common JSON issues from LLM outputs
  - **mido**: MIDI file writing

## Install

```bash
python3 -m pip install -e .
```

## Usage

Render a MIDI file from an LLM response saved as text:

```bash
python3 -m aimusicgen.cli render --in examples/model_output.txt --out out.mid
```

Or pipe directly:

```bash
cat examples/model_output.txt | python3 -m aimusicgen.cli render --out out.mid
```

## Expected model output shape (JSON)

The model should output a JSON object with this high-level structure:

- `title`, `bpm`, `time_signature`, optional `key_signature`
- `tracks[]` each with `events[]`
- events are:
  - `{"type":"note","start":...,"duration":...,"pitch":"C4"}` (single note)
  - `{"type":"note","start":...,"duration":...,"pitches":["C4","E4","G4"]}` (chord)
  - `{"type":"pedal","start":...,"duration":...}` (sustain pedal)

See `examples/model_output.txt` for a working example.