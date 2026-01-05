import pretty_midi
import logging
from .schema import Composition

# Configure logging
logger = logging.getLogger(__name__)

class MidiConverter:
    def convert(self, composition: Composition, output_file: str):
        # Validate tempo
        if composition.tempo <= 0:
            raise ValueError(f"Invalid tempo: {composition.tempo}. Tempo must be positive.")

        # Create a PrettyMIDI object
        # initial_tempo is optional in constructor, but we can set it via the tempo map if needed.
        # However, pretty_midi init allows creating an empty object.
        pm = pretty_midi.PrettyMIDI(initial_tempo=composition.tempo)
        
        # Calculate seconds per beat for timing conversion
        # beats * (60 / bpm) = seconds
        seconds_per_beat = 60.0 / composition.tempo
        
        for track_data in composition.tracks:
            # Create an Instrument instance
            # pretty_midi requires program number (0-127) and is_drum
            instrument = pretty_midi.Instrument(program=track_data.instrument)
            instrument.name = track_data.name
            
            for note_data in track_data.notes:
                try:
                    # Retrieve the MIDI note number for the pitch name
                    # pretty_midi.note_name_to_number handles "C4", "F#3", etc.
                    note_number = pretty_midi.note_name_to_number(note_data.pitch)
                    
                    # Convert beats to seconds
                    start_time_sec = note_data.start_time * seconds_per_beat
                    duration_sec = note_data.duration * seconds_per_beat
                    end_time_sec = start_time_sec + duration_sec
                    
                    # Create a Note instance
                    note = pretty_midi.Note(
                        velocity=note_data.velocity,
                        pitch=note_number,
                        start=start_time_sec,
                        end=end_time_sec
                    )
                    
                    instrument.notes.append(note)
                except ValueError as e:
                    logger.warning(f"Skipping invalid note {note_data.pitch}: {e}")
                    continue
            
            # Add the instrument to the PrettyMIDI object
            pm.instruments.append(instrument)
            
        # Write out the MIDI data
        pm.write(output_file)
        logger.info(f"MIDI file saved to {output_file}")
