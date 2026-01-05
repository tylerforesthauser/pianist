"""
Example: Parsing AI-generated music from dictionary format.
"""

from pianist import MusicParser, MIDIGenerator

# AI model response as a dictionary
ai_composition = {
    "title": "Pastoral Sonata in F Major",
    "composer": "AI Composer",
    "tempo": 90,
    "time_signature": [3, 4],  # Waltz time
    "key_signature": "F major",
    "form": "Sonata",
    "sections": [
        {
            "name": "Exposition",
            "repeat": True,
            "phrases": [
                {
                    "name": "First Theme",
                    "motifs": [
                        {
                            "name": "Opening Gesture",
                            "notes": "F4:1.0:64 A4:1.0:64 C5:1.0:80"
                        },
                        {
                            "name": "Continuation",
                            "notes": "D5:0.5:70 C5:0.5:70 A4:1.0:64 F4:1.0:64"
                        }
                    ]
                },
                {
                    "name": "Second Theme",
                    "motifs": [
                        {
                            "name": "Lyrical Melody",
                            "notes": "C5:1.5:64 D5:0.5:64 E5:1.0:70 F5:2.0:80"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Development",
            "phrases": [
                {
                    "name": "Fragmentation",
                    "motifs": [
                        "F4:0.5:64 A4:0.5:64",
                        "G4:0.5:64 B4:0.5:64",
                        "A4:0.5:64 C5:0.5:64",
                        "B4:1.0:70 C5:2.0:80"
                    ]
                }
            ]
        },
        {
            "name": "Recapitulation",
            "phrases": [
                {
                    "name": "First Theme Return",
                    "motifs": ["F4:1.0:64 A4:1.0:64 C5:1.0:80"]
                },
                {
                    "name": "Closing",
                    "motifs": ["C5:1.0:64 A4:1.0:64 F4:2.0:64"]
                }
            ]
        }
    ]
}

# Parse the AI response
parser = MusicParser()
composition = parser.parse_composition(ai_composition)

# Generate MIDI file
generator = MIDIGenerator(composition)
generator.generate("ai_sonata.mid")

print("✓ Generated ai_sonata.mid")
print(f"  Title: {composition.title}")
print(f"  Form: {composition.form}")
print(f"  Tempo: {composition.tempo.bpm} BPM")
print(f"  Time Signature: {composition.time_signature.numerator}/{composition.time_signature.denominator}")
print(f"  Sections: {len(composition.sections)}")
print(f"  Total duration: {composition.duration_in_seconds():.2f} seconds")
