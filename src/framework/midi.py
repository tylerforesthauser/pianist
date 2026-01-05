import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from .schema import Composition, Track

# Mapping for note names to MIDI numbers
NOTE_OFFSETS = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11
}

def note_to_midi(pitch: str) -> int:
    """Converts scientific pitch notation (e.g., 'C4') to MIDI note number."""
    if not pitch:
        raise ValueError("Empty pitch string")
        
    # Handle simple parsing of "C4", "F#3", "Bb5"
    # Find where the octave number starts
    idx = 0
    while idx < len(pitch) and not pitch[idx].isdigit():
        idx += 1
    
    note_name = pitch[:idx]
    try:
        octave = int(pitch[idx:])
    except ValueError:
        raise ValueError(f"Invalid pitch format: {pitch}")
        
    if note_name not in NOTE_OFFSETS:
        raise ValueError(f"Invalid note name: {note_name}")
        
    return NOTE_OFFSETS[note_name] + (octave + 1) * 12

def seconds_to_ticks(seconds: float, tempo: int, ticks_per_beat: int) -> int:
    # mido tempo is microseconds per beat
    # ticks = seconds * (ticks_per_beat * 1000000 / tempo_us)
    # But we are dealing with beat durations directly from the AI.
    # The AI gives duration in beats.
    # ticks = beats * ticks_per_beat
    return int(seconds * ticks_per_beat) # "seconds" here is actually beats in our schema context

class MidiConverter:
    def __init__(self, ticks_per_beat: int = 480):
        self.ticks_per_beat = ticks_per_beat

    def convert(self, composition: Composition, output_file: str):
        mid = MidiFile(ticks_per_beat=self.ticks_per_beat)
        
        # Create a tempo track
        tempo_track = MidiTrack()
        mid.tracks.append(tempo_track)
        
        # Add Time Signature
        # Assuming 4/4 for simplicity in parsing "4/4", but could be expanded
        num, den = map(int, composition.time_signature.split('/'))
        tempo_track.append(MetaMessage('time_signature', numerator=num, denominator=den))
        
        # Add Tempo
        tempo_us = mido.bpm2tempo(composition.tempo)
        tempo_track.append(MetaMessage('set_tempo', tempo=tempo_us))
        
        for track_data in composition.tracks:
            midi_track = MidiTrack()
            mid.tracks.append(midi_track)
            
            # Set Instrument
            midi_track.append(Message('program_change', program=track_data.instrument, time=0))
            
            # Create MIDI events
            events = []
            for note in track_data.notes:
                try:
                    midi_val = note_to_midi(note.pitch)
                except ValueError as e:
                    print(f"Warning: Skipping invalid note {note.pitch}: {e}")
                    continue
                    
                start_ticks = int(note.start_time * self.ticks_per_beat)
                duration_ticks = int(note.duration * self.ticks_per_beat)
                end_ticks = start_ticks + duration_ticks
                
                # Note On
                events.append({
                    'type': 'note_on',
                    'note': midi_val,
                    'velocity': note.velocity,
                    'time': start_ticks
                })
                
                # Note Off
                events.append({
                    'type': 'note_off',
                    'note': midi_val,
                    'velocity': 0,
                    'time': end_ticks
                })
            
            # Sort events by time
            events.sort(key=lambda x: (x['time'], 0 if x['type'] == 'note_off' else 1))
            
            # Convert absolute time to delta time
            last_time = 0
            for event in events:
                delta = event['time'] - last_time
                midi_track.append(Message(event['type'], note=event['note'], velocity=event['velocity'], time=delta))
                last_time = event['time']
                
        mid.save(output_file)
        print(f"MIDI file saved to {output_file}")
