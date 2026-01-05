from __future__ import annotations

import copy
from pathlib import Path

from music21 import chord, instrument, meter, metadata, midi, note, stream, tempo

from ..schema import Composition, NoteEvent, PedalEvent


def _beats_to_quarter_length(beats: float) -> float:
    # Schema defines "beat" as quarter-note beat for simplicity.
    return float(beats)


def to_music21_score(composition: Composition) -> stream.Score:
    """
    Convert a validated Composition into a music21 Score.
    """
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = composition.title

    for t in composition.tracks:
        part = stream.Part()
        part.partName = t.name

        # Instrument: keep it simple for now; set MIDI program.
        inst = instrument.Instrument()
        inst.midiProgram = int(t.program)
        part.insert(0, inst)
        part.insert(
            0,
            meter.TimeSignature(
                f"{composition.time_signature.numerator}/{composition.time_signature.denominator}"
            ),
        )
        part.insert(0, tempo.MetronomeMark(number=float(composition.bpm)))

        # We currently ignore key_signature for rendering, since music21's
        # key signature parsing is nuanced (major/minor vs mode strings).
        # It can be added once we standardize accepted formats.

        for ev in t.events:
            start = _beats_to_quarter_length(ev.start)
            dur = _beats_to_quarter_length(ev.duration)

            if isinstance(ev, NoteEvent):
                if len(ev.pitches) == 1:
                    n = note.Note(midi=int(ev.pitches[0]))
                    n.volume.velocity = int(ev.velocity)
                    n.duration.quarterLength = dur
                    part.insert(start, n)
                else:
                    c = chord.Chord([note.Note(midi=int(p)) for p in ev.pitches])
                    for cn in c.notes:
                        cn.volume.velocity = int(ev.velocity)
                    c.duration.quarterLength = dur
                    part.insert(start, c)
            elif isinstance(ev, PedalEvent):
                # Store pedal events to add to MIDI stream later.
                # We'll handle these in render_midi_music21 after score creation.
                # For now, we skip adding them to the stream (they'll be added to MIDI).
                pass
            else:
                raise TypeError(f"Unsupported event type: {type(ev)}")

        # Avoid containment issues if callers later reuse elements/score.
        score.append(copy.deepcopy(part))

    return score


def render_midi_music21(composition: Composition, out_path: str | Path) -> Path:
    """
    Render a validated Composition to a MIDI file via music21.
    """
    out_path = Path(out_path)
    score = to_music21_score(composition)
    
    # Convert score to MIDI file format
    mf = midi.translate.streamToMidiFile(score)
    
    # Add pedal control change events to the appropriate tracks
    # Note: track 0 is usually the conductor/metadata track, so we offset by 1
    for track_idx, track in enumerate(composition.tracks):
        # music21 creates tracks: [conductor, track1, track2, ...]
        midi_track_idx = track_idx + 1
        if midi_track_idx >= len(mf.tracks):
            continue
        
        midi_track = mf.tracks[midi_track_idx]
        
        # Collect all pedal events for this track
        pedal_events = [
            ev for ev in track.events if isinstance(ev, PedalEvent)
        ]
        
        # Convert all existing events to absolute time, add pedal events, then convert back to delta
        # First, convert existing delta times to absolute times
        absolute_time = 0
        for existing_event in midi_track.events:
            absolute_time += existing_event.time
            existing_event.time = absolute_time
        
        # Now add pedal events with absolute times
        for pedal_ev in pedal_events:
            pedal_start_ticks = int(round(pedal_ev.start * composition.ppq))
            pedal_end_ticks = int(round((pedal_ev.start + pedal_ev.duration) * composition.ppq))
            
            # Create control change event for pedal on (CC 64)
            # parameter1 = controller number (64), parameter2 = value
            cc_on_event = midi.MidiEvent(
                track=midi_track,
                type=midi.ChannelVoiceMessages.CONTROLLER_CHANGE,
                time=pedal_start_ticks,
                channel=track.channel,
            )
            cc_on_event.parameter1 = 64  # Sustain pedal controller number
            cc_on_event.parameter2 = pedal_ev.value
            midi_track.events.append(cc_on_event)
            
            # Create control change event for pedal off (CC 64, value 0)
            cc_off_event = midi.MidiEvent(
                track=midi_track,
                type=midi.ChannelVoiceMessages.CONTROLLER_CHANGE,
                time=pedal_end_ticks,
                channel=track.channel,
            )
            cc_off_event.parameter1 = 64  # Sustain pedal controller number
            cc_off_event.parameter2 = 0
            midi_track.events.append(cc_off_event)
        
        # Sort all events by absolute time
        midi_track.events.sort(key=lambda e: e.time)
        
        # Convert back to delta times
        last_time = 0
        for event in midi_track.events:
            current_time = event.time
            event.time = current_time - last_time
            last_time = current_time
    
    # Write the modified MIDI file
    mf.open(out_path, "wb")
    mf.write()
    mf.close()
    return out_path

