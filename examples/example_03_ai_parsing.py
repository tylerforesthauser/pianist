"""
Example: Parsing AI-generated composition from JSON format.
"""

from pianist import MusicParser

# AI model response as a dictionary
ai_composition = {
    "title": "Pastoral Sonata in F Major",
    "composer": "AI Composer",
    "tempo": 90,
    "time_signature": [3, 4],  # Waltz time
    "sections": [
        {
            "name": "Exposition",
            "repeat": True,
            "phrases": [
                {
                    "name": "First Theme",
                    "motifs": [
                        "F4:1.0:64 A4:1.0:64 C5:1.0:80",
                        "D5:0.5:70 C5:0.5:70 A4:1.0:64 F4:1.0:64"
                    ]
                },
                {
                    "name": "Second Theme",
                    "motifs": ["C5:1.5:64 D5:0.5:64 E5:1.0:70 F5:2.0:80"]
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

# Parse the AI response using our custom parser
parser = MusicParser()
score = parser.parse_composition(ai_composition)

# Export to MIDI using music21
score.write('midi', fp='ai_sonata.mid')

print("✓ Generated ai_sonata.mid")
print(f"  Title: {score.metadata.title}")
print(f"  Composer: {score.metadata.composer}")
print(f"  Sections: {len(ai_composition['sections'])}")
print(f"  Built on music21 for professional-grade output")
