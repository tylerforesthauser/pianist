import argparse
import os
import sys
import logging
from src.framework.agent import MockMusicAgent, OpenAIMusicAgent, MusicAgent
from src.framework.midi import MidiConverter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    parser = argparse.ArgumentParser(description="AI Music Generation Framework")
    parser.add_argument("prompt", help="Description of the music to compose")
    parser.add_argument("--output", "-o", default="output.mid", help="Output MIDI filename")
    parser.add_argument("--api-key", help="OpenAI API Key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--mock", action="store_true", help="Force use of Mock Agent")
    
    args = parser.parse_args()

    agent: MusicAgent
    
    # Determine which agent to use
    if args.mock:
        print("Using Mock Agent...")
        agent = MockMusicAgent()
    elif args.api_key or os.getenv("OPENAI_API_KEY"):
        print("Using OpenAI Agent...")
        agent = OpenAIMusicAgent(api_key=args.api_key)
    else:
        print("No API Key found. Using Mock Agent (pass --api-key or set OPENAI_API_KEY to use AI)...")
        agent = MockMusicAgent()

    try:
        print(f"Composing: '{args.prompt}'...")
        composition = agent.compose(args.prompt)
        
        print(f"Composition '{composition.title}' created.")
        print(f"Tempo: {composition.tempo} BPM, Time Sig: {composition.time_signature}")
        print(f"Tracks: {len(composition.tracks)}")
        
        converter = MidiConverter()
        converter.convert(composition, args.output)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
