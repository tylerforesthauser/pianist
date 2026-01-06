"""
Fix incorrect sustain pedal patterns in compositions.

This module provides functions to automatically fix common pedal pattern issues,
converting duration=0 patterns to duration>0 patterns with reasonable defaults.
"""

from __future__ import annotations

from .schema import Composition, PedalEvent


def fix_pedal_patterns(comp: Composition) -> Composition:
    """
    Fix incorrect sustain pedal patterns in a composition.
    
    Converts problematic patterns:
    - duration=0, value=127 (press) followed by duration=0, value=0 (release) 
      → single duration>0 event
    - duration=0, value=127 without matching release 
      → extend to next pedal event or reasonable default (4-8 beats)
    
    Returns a new Composition with fixed pedal patterns.
    """
    fixed = comp.model_copy(deep=True)
    
    for track in fixed.tracks:
        events = track.events
        
        # Find all pedal events with their indices
        pedal_info: list[tuple[int, PedalEvent]] = [
            (i, ev) for i, ev in enumerate(events)
            if isinstance(ev, PedalEvent)
        ]
        
        if not pedal_info:
            continue
        
        # Process pedal events to fix duration=0 issues
        fixed_pedals: list[PedalEvent] = []
        processed_indices = set()
        
        for i, (idx, pedal) in enumerate(pedal_info):
            if idx in processed_indices:
                continue
            
            # Only fix duration=0 events
            if pedal.duration == 0:
                if pedal.value == 127:  # Press event
                    # Look for a matching release event (duration=0, value=0) after this
                    release_idx = None
                    release_pedal = None
                    
                    for j in range(i + 1, len(pedal_info)):
                        next_idx, next_pedal = pedal_info[j]
                        # pedal_info is already filtered to contain only PedalEvent instances
                        if (next_pedal.duration == 0 and 
                            next_pedal.value == 0 and
                            next_pedal.start > pedal.start):
                            release_idx = next_idx
                            release_pedal = next_pedal
                            break
                    
                    if release_pedal is not None:
                        # Found matching release - merge into single event
                        duration = release_pedal.start - pedal.start
                        if duration > 0:
                            fixed_pedal = PedalEvent(
                                type="pedal",
                                start=pedal.start,
                                duration=duration,
                                value=pedal.value,
                                section=pedal.section,
                                phrase=pedal.phrase,
                            )
                            fixed_pedals.append(fixed_pedal)
                            processed_indices.add(idx)
                            processed_indices.add(release_idx)
                            continue
                        else:
                            # Same start time - skip both events (invalid pattern)
                            processed_indices.add(idx)
                            processed_indices.add(release_idx)
                            continue
                    
                    # No matching release found - extend to next pedal or default
                    next_pedal_start = None
                    for j in range(i + 1, len(pedal_info)):
                        _, next_pedal = pedal_info[j]
                        if next_pedal.start > pedal.start:
                            next_pedal_start = next_pedal.start
                            break
                    
                    if next_pedal_start is not None:
                        # Extend to next pedal with small gap to avoid overlap
                        duration = max(0.1, next_pedal_start - pedal.start - 0.1)
                    else:
                        # No next pedal - extend to end of composition or default
                        last_event_end = max(
                            (
                                (ev.start + getattr(ev, 'duration', 0))
                                for ev in events
                                if hasattr(ev, 'duration')
                            ),
                            default=pedal.start,
                        )
                        # Use reasonable default: up to 8 beats, or to end of composition
                        duration = min(max(0.1, last_event_end - pedal.start), 8.0)
                        if duration <= 0:
                            duration = 4.0  # Fallback default
                    
                    fixed_pedal = PedalEvent(
                        type="pedal",
                        start=pedal.start,
                        duration=duration,
                        value=pedal.value,
                        section=pedal.section,
                        phrase=pedal.phrase,
                    )
                    fixed_pedals.append(fixed_pedal)
                    processed_indices.add(idx)
                
                elif pedal.value == 0:  # Release event without matching press
                    # Keep as-is (valid for instant release, though unusual)
                    fixed_pedals.append(pedal)
                    processed_indices.add(idx)
            else:
                # Already has duration>0 - keep as-is
                fixed_pedals.append(pedal)
                processed_indices.add(idx)
        
        # Replace pedal events in the events list
        # Remove old pedal events
        new_events = [ev for ev in events if not isinstance(ev, PedalEvent)]
        
        # Add fixed pedal events
        new_events.extend(fixed_pedals)
        
        # Sort events by start time (and type for stability)
        new_events.sort(key=lambda e: (
            getattr(e, 'start', 0),
            getattr(e, 'type', ''),
        ))
        
        track.events = new_events
    
    return fixed
