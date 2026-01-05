import json
from typing import Dict, Any
from .schema import Composition, Track, Note

class CompositionParser:
    @staticmethod
    def parse(json_data: str | Dict[str, Any]) -> Composition:
        if isinstance(json_data, str):
            try:
                # specific cleanup for LLM output which often includes markdown code blocks
                clean_json = json_data.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                
                data = json.loads(clean_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON: {e}")
        else:
            data = json_data

        try:
            tracks = []
            for t_data in data.get("tracks", []):
                notes = []
                for n_data in t_data.get("notes", []):
                    notes.append(Note(
                        pitch=n_data["pitch"],
                        duration=float(n_data["duration"]),
                        start_time=float(n_data["start_time"]),
                        velocity=int(n_data.get("velocity", 80))
                    ))
                
                tracks.append(Track(
                    name=t_data.get("name", "Untitled Track"),
                    instrument=int(t_data.get("instrument", 0)),
                    notes=notes
                ))

            return Composition(
                title=data.get("title", "Untitled Composition"),
                tempo=int(data.get("tempo", 120)),
                time_signature=data.get("time_signature", "4/4"),
                tracks=tracks
            )
        except (KeyError, ValueError, TypeError) as e:
            # Preserve the original exception type and include a snippet of the problematic data
            data_snippet = ""
            try:
                data_snippet = json.dumps(data, ensure_ascii=False)[:200]
            except Exception:
                # Fallback if data cannot be serialized to JSON
                data_snippet = str(data)[:200]
            
            raise ValueError(
                f"Invalid composition structure ({e.__class__.__name__}): {e}. "
                f"Problematic data (truncated): {data_snippet}"
            ) from e
