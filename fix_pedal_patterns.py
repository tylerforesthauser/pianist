#!/usr/bin/env python3
"""
Fix incorrect sustain pedal patterns in existing composition JSON files.

This script converts problematic pedal patterns (duration=0) to correct patterns (duration>0)
using reasonable assumptions and defaults.
"""

import json
import sys
from pathlib import Path
from typing import Any

from pianist.schema import Composition, PedalEvent, validate_composition_dict


def fix_pedal_patterns(comp: Composition) -> Composition:
    """
    Fix incorrect sustain pedal patterns in a composition.
    
    Converts:
    - duration=0, value=127 followed by duration=0, value=0 → single duration>0 event
    - duration=0, value=127 without release → extend to next pedal or end of composition
    - Overlapping pedals → merge or adjust as needed
    
    Returns a new Composition with fixed pedal patterns.
    """
    fixed = comp.model_copy(deep=True)
    
    for track in fixed.tracks:
        # Collect all events with their indices
        events = track.events
        pedal_indices = [
            i for i, ev in enumerate(events)
            if isinstance(ev, PedalEvent)
        ]
        
        if not pedal_indices:
            continue
        
        # Strategy: Convert duration=0 patterns to duration>0
        # Find pairs of duration=0 events (press + release) and merge them
        i = 0
        while i < len(pedal_indices):
            idx = pedal_indices[i]
            pedal = events[idx]
            
            # Only fix duration=0 events
            if pedal.duration == 0:
                if pedal.value == 127:  # Press event
                    # Look for a release event (duration=0, value=0) after this
                    release_idx = None
                    for j in range(i + 1, len(pedal_indices)):
                        next_pedal = events[pedal_indices[j]]
                        if (isinstance(next_pedal, PedalEvent) and 
                            next_pedal.duration == 0 and 
                            next_pedal.value == 0 and
                            next_pedal.start > pedal.start):
                            release_idx = pedal_indices[j]
                            break
                    
                    if release_idx is not None:
                        # Found a matching release - merge into single event
                        release_pedal = events[release_idx]
                        duration = release_pedal.start - pedal.start
                        
                        if duration > 0:
                            # Update the press event with duration
                            pedal.duration = duration
                            # Remove the release event
                            events.pop(release_idx)
                            # Rebuild pedal_indices since we removed an event
                            pedal_indices = [
                                i for i, ev in enumerate(events)
                                if isinstance(ev, PedalEvent)
                            ]
                            continue
                    else:
                        # No release found - extend to next pedal event or reasonable default
                        next_pedal_start = None
                        for j in range(i + 1, len(pedal_indices)):
                            next_pedal = events[pedal_indices[j]]
                            if next_pedal.start > pedal.start:
                                next_pedal_start = next_pedal.start
                                break
                        
                        if next_pedal_start is not None:
                            # Extend to next pedal (but don't overlap)
                            duration = next_pedal_start - pedal.start - 0.1  # Small gap
                            if duration > 0:
                                pedal.duration = duration
                        else:
                            # No next pedal - use default duration (e.g., 4 beats or to end of composition)
                            # Find the last event to estimate composition end
                            last_event_start = max(
                                (ev.start + (getattr(ev, 'duration', 0) if hasattr(ev, 'duration') else 0))
                                for ev in events
                                if hasattr(ev, 'start')
                            )
                            if last_event_start > pedal.start:
                                duration = min(last_event_start - pedal.start, 8.0)  # Max 8 beats
                                if duration > 0:
                                    pedal.duration = duration
                            else:
                                # Fallback: 4 beats
                                pedal.duration = 4.0
                
                elif pedal.value == 0:  # Release event without matching press
                    # This is an orphaned release - we can remove it or keep it
                    # For now, keep it as-is (duration=0, value=0 is valid for instant release)
                    pass
            
            i += 1
        
        # Update track events
        track.events = events
    
    return fixed


def fix_pedal_patterns_advanced(comp: Composition) -> Composition:
    """
    Advanced fix with better handling of overlapping and complex patterns.
    """
    fixed = comp.model_copy(deep=True)
    
    for track in fixed.tracks:
        events = track.events
        
        # Separate pedal events from other events
        pedal_events: list[tuple[int, PedalEvent]] = [
            (i, ev) for i, ev in enumerate(events)
            if isinstance(ev, PedalEvent)
        ]
        
        if not pedal_events:
            continue
        
        # Process pedal events
        fixed_pedals: list[PedalEvent] = []
        i = 0
        
        while i < len(pedal_events):
            idx, pedal = pedal_events[i]
            
            if pedal.duration == 0:
                if pedal.value == 127:  # Press
                    # Look for release
                    release_found = False
                    for j in range(i + 1, len(pedal_events)):
                        next_idx, next_pedal = pedal_events[j]
                        if (next_pedal.duration == 0 and 
                            next_pedal.value == 0 and
                            next_pedal.start > pedal.start):
                            # Found release - merge
                            duration = next_pedal.start - pedal.start
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
                                # Skip the release event
                                i = j + 1
                                release_found = True
                                break
                    
                    if not release_found:
                        # No release found - extend to next pedal or default
                        next_start = None
                        for j in range(i + 1, len(pedal_events)):
                            _, next_pedal = pedal_events[j]
                            if next_pedal.start > pedal.start:
                                next_start = next_pedal.start
                                break
                        
                        if next_start:
                            duration = max(0.1, next_start - pedal.start - 0.1)
                        else:
                            # Default: 4 beats or to end of composition
                            last_end = max(
                                (ev.start + getattr(ev, 'duration', 0))
                                for ev in events
                                if hasattr(ev, 'duration')
                            )
                            duration = min(max(0.1, last_end - pedal.start), 8.0)
                        
                        fixed_pedal = PedalEvent(
                            type="pedal",
                            start=pedal.start,
                            duration=duration,
                            value=pedal.value,
                            section=pedal.section,
                            phrase=pedal.phrase,
                        )
                        fixed_pedals.append(fixed_pedal)
                        i += 1
                
                elif pedal.value == 0:  # Release without press
                    # Keep as-is (valid for instant release)
                    fixed_pedals.append(pedal)
                    i += 1
            else:
                # Already has duration>0 - keep as-is
                fixed_pedals.append(pedal)
                i += 1
        
        # Replace pedal events in the events list
        # Remove old pedal events
        events = [ev for ev in events if not isinstance(ev, PedalEvent)]
        
        # Add fixed pedal events
        for fixed_pedal in fixed_pedals:
            events.append(fixed_pedal)
        
        # Sort events by start time
        events.sort(key=lambda e: (getattr(e, 'start', 0), getattr(e, 'type', '')))
        
        track.events = events
    
    return fixed


def fix_composition_file(json_path: Path, output_path: Path | None = None) -> Composition:
    """Load, fix, and save a composition JSON file."""
    # Load composition
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    comp = validate_composition_dict(data)
    
    # Count pedal issues before fix
    pedal_issues_before = sum(
        1 for track in comp.tracks
        for ev in track.events
        if isinstance(ev, PedalEvent) and ev.duration == 0 and ev.value == 127
    )
    
    # Fix pedal patterns
    fixed = fix_pedal_patterns_advanced(comp)
    
    # Count after fix
    pedal_issues_after = sum(
        1 for track in fixed.tracks
        for ev in track.events
        if isinstance(ev, PedalEvent) and ev.duration == 0 and ev.value == 127
    )
    
    # Save fixed composition
    output_path = output_path or json_path
    fixed_data = fixed.model_dump(mode='json', exclude_none=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)
    
    print(f"Fixed {json_path.name}:")
    print(f"  Pedal issues before: {pedal_issues_before}")
    print(f"  Pedal issues after: {pedal_issues_after}")
    print(f"  Saved to: {output_path}")
    
    return fixed


def main():
    """Fix pedal patterns in provided JSON files."""
    if len(sys.argv) < 2:
        print("Usage: fix_pedal_patterns.py <json_file1> [json_file2] ...")
        print("  Or: fix_pedal_patterns.py --all <directory>")
        sys.exit(1)
    
    if sys.argv[1] == "--all" and len(sys.argv) > 2:
        # Fix all JSON files in directory
        dir_path = Path(sys.argv[2])
        json_files = list(dir_path.glob("*.json"))
        for json_path in json_files:
            try:
                fix_composition_file(json_path)
            except Exception as e:
                print(f"Error fixing {json_path.name}: {e}")
    else:
        # Fix specific files
        for json_path_str in sys.argv[1:]:
            json_path = Path(json_path_str)
            if not json_path.exists():
                print(f"Error: File not found: {json_path}")
                continue
            try:
                fix_composition_file(json_path)
            except Exception as e:
                print(f"Error fixing {json_path}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
