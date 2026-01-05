"""
MIDI file generation from composition structures.
"""

from typing import List, Optional
from midiutil import MIDIFile
from .composition import Composition, Note


class MIDIGenerator:
    """
    Generates MIDI files from Composition objects.
    """
    
    def __init__(self, composition: Composition):
        """
        Initialize the MIDI generator with a composition.
        
        Args:
            composition: The Composition object to convert to MIDI
        """
        self.composition = composition
    
    def generate(self, filename: str, track_name: Optional[str] = None):
        """
        Generate a MIDI file from the composition.
        
        Args:
            filename: Path to save the MIDI file
            track_name: Optional name for the MIDI track (defaults to composition title)
        """
        # Create MIDI file with 1 track
        midi = MIDIFile(1)
        
        # Set track name
        track = 0
        time = 0
        if track_name is None:
            track_name = self.composition.title
        midi.addTrackName(track, time, track_name)
        
        # Set tempo
        midi.addTempo(track, time, self.composition.tempo.bpm)
        
        # Add time signature
        midi.addTimeSignature(
            track,
            time,
            self.composition.time_signature.numerator,
            self.composition.time_signature.denominator,
            24,  # MIDI clocks per metronome click
            8    # Number of 32nd notes per beat
        )
        
        # Get all notes from the composition
        notes = self.composition.get_all_notes()
        
        # Add notes to MIDI file
        current_time = 0
        for note in notes:
            midi.addNote(
                track=track,
                channel=0,
                pitch=note.pitch,
                time=current_time,
                duration=note.duration,
                volume=note.velocity
            )
            current_time += note.duration
        
        # Write MIDI file
        with open(filename, "wb") as output_file:
            midi.writeFile(output_file)
    
    @staticmethod
    def from_notes(
        notes: List[Note],
        filename: str,
        title: str = "Generated Composition",
        tempo: int = 120,
        time_signature_num: int = 4,
        time_signature_den: int = 4
    ):
        """
        Quick method to generate a MIDI file directly from a list of notes.
        
        Args:
            notes: List of Note objects
            filename: Path to save the MIDI file
            title: Title of the composition
            tempo: Tempo in BPM
            time_signature_num: Time signature numerator
            time_signature_den: Time signature denominator
        """
        midi = MIDIFile(1)
        track = 0
        time = 0
        
        midi.addTrackName(track, time, title)
        midi.addTempo(track, time, tempo)
        midi.addTimeSignature(track, time, time_signature_num, time_signature_den, 24, 8)
        
        current_time = 0
        for note in notes:
            midi.addNote(
                track=track,
                channel=0,
                pitch=note.pitch,
                time=current_time,
                duration=note.duration,
                volume=note.velocity
            )
            current_time += note.duration
        
        with open(filename, "wb") as output_file:
            midi.writeFile(output_file)


class MultiTrackMIDIGenerator:
    """
    Generates multi-track MIDI files (e.g., for piano with separate hands or multiple instruments).
    """
    
    def __init__(self):
        self.tracks: List[tuple] = []  # List of (notes, track_name, channel) tuples
    
    def add_track(self, notes: List[Note], track_name: str = "Track", channel: int = 0):
        """
        Add a track to the multi-track MIDI file.
        
        Args:
            notes: List of Note objects for this track
            track_name: Name of the track
            channel: MIDI channel (0-15)
        """
        self.tracks.append((notes, track_name, channel))
    
    def generate(
        self,
        filename: str,
        tempo: int = 120,
        time_signature_num: int = 4,
        time_signature_den: int = 4
    ):
        """
        Generate a multi-track MIDI file.
        
        Args:
            filename: Path to save the MIDI file
            tempo: Tempo in BPM
            time_signature_num: Time signature numerator
            time_signature_den: Time signature denominator
        """
        # Create MIDI file with the number of tracks
        num_tracks = len(self.tracks)
        midi = MIDIFile(num_tracks)
        
        # Process each track
        for track_idx, (notes, track_name, channel) in enumerate(self.tracks):
            time = 0
            
            # Add track metadata
            midi.addTrackName(track_idx, time, track_name)
            midi.addTempo(track_idx, time, tempo)
            midi.addTimeSignature(track_idx, time, time_signature_num, time_signature_den, 24, 8)
            
            # Add notes
            current_time = 0
            for note in notes:
                midi.addNote(
                    track=track_idx,
                    channel=channel,
                    pitch=note.pitch,
                    time=current_time,
                    duration=note.duration,
                    volume=note.velocity
                )
                current_time += note.duration
        
        # Write MIDI file
        with open(filename, "wb") as output_file:
            midi.writeFile(output_file)
