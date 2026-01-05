import os
import json
from abc import ABC, abstractmethod
from typing import Optional
from .schema import Composition
from .prompts import MUSIC_THEORY_SYSTEM_PROMPT, create_composition_prompt
from .parser import CompositionParser

class MusicAgent(ABC):
    @abstractmethod
    def compose(self, description: str) -> Composition:
        pass

class MockMusicAgent(MusicAgent):
    def compose(self, description: str) -> Composition:
        """Returns a hardcoded simple composition for testing."""
        print(f"MockAgent: Composing piece based on: {description}")
        # A simple C Major scale / motif
        mock_json = {
            "title": "Mock Composition",
            "tempo": 100,
            "time_signature": "4/4",
            "tracks": [
                {
                    "name": "Right Hand",
                    "instrument": 0,
                    "notes": [
                        {"pitch": "C4", "duration": 1.0, "start_time": 0.0, "velocity": 100},
                        {"pitch": "D4", "duration": 1.0, "start_time": 1.0, "velocity": 90},
                        {"pitch": "E4", "duration": 1.0, "start_time": 2.0, "velocity": 95},
                        {"pitch": "F4", "duration": 1.0, "start_time": 3.0, "velocity": 90},
                        {"pitch": "G4", "duration": 4.0, "start_time": 4.0, "velocity": 110}
                    ]
                }
            ]
        }
        return CompositionParser.parse(mock_json)

class OpenAIMusicAgent(MusicAgent):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        try:
            import openai
        except ImportError:
            raise ImportError("openai package is not installed. Please run 'pip install openai'")
            
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def compose(self, description: str) -> Composition:
        prompt = create_composition_prompt(description)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": MUSIC_THEORY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        return CompositionParser.parse(content)
