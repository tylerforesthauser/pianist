# AI Music Generation Framework

This framework allows you to prompt AI agents to compose piano music using music theory principles and convert the output to MIDI files.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set your OpenAI API Key:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

## Usage

Run the main script with a prompt:

```bash
python main.py "A melancholic piano waltz in A minor" --output waltz.mid
```

If you don't have an API key, the system will default to a Mock Agent that produces a simple test scale. To force the mock agent:

```bash
python main.py "Test" --mock
```

## Structure

- `src/framework/schema.py`: Data structures for music (Composition, Track, Note).
- `src/framework/prompts.py`: System prompts encoding music theory knowledge.
- `src/framework/midi.py`: MIDI file generation engine.
- `src/framework/parser.py`: Robust JSON parsing for AI outputs.
- `src/framework/agent.py`: Interface for AI agents (includes OpenAI implementation).

## Extending

To add a new AI model (e.g., Anthropic), subclass `MusicAgent` in `src/framework/agent.py` and implement the `compose` method.
