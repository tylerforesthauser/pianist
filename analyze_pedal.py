#!/usr/bin/env python3
"""
Deep analysis of sustain pedal control in pianist compositions.

This script analyzes JSON composition files and their corresponding MIDI outputs
to identify issues with sustain pedal handling.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import mido


def analyze_json_pedal_events(json_path: Path) -> dict[str, Any]:
    """Analyze pedal events in a JSON composition file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pedal_events = []
    for track_idx, track in enumerate(data.get("tracks", [])):
        for event_idx, event in enumerate(track.get("events", [])):
            if event.get("type") == "pedal":
                pedal_events.append({
                    "track": track_idx,
                    "event_index": event_idx,
                    "start": event.get("start", 0),
                    "duration": event.get("duration", 0),
                    "value": event.get("value", 127),
                })
    
    # Sort by start time
    pedal_events.sort(key=lambda x: x["start"])
    
    return {
        "total_pedal_events": len(pedal_events),
        "events": pedal_events,
        "duration_zero_count": sum(1 for e in pedal_events if e["duration"] == 0),
        "duration_positive_count": sum(1 for e in pedal_events if e["duration"] > 0),
        "value_127_count": sum(1 for e in pedal_events if e["value"] == 127),
        "value_0_count": sum(1 for e in pedal_events if e["value"] == 0),
    }


def analyze_midi_pedal_events(midi_path: Path) -> dict[str, Any]:
    """Analyze sustain pedal (CC 64) events in a MIDI file."""
    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        return {"error": str(e), "total_cc64_events": 0, "events": []}
    
    cc64_events = []
    ppq = mid.ticks_per_beat
    
    for track_idx, track in enumerate(mid.tracks):
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if isinstance(msg, mido.Message) and msg.type == "control_change" and msg.control == 64:
                beat_position = abs_tick / ppq
                cc64_events.append({
                    "track": track_idx,
                    "beat": beat_position,
                    "value": msg.value,
                    "tick": abs_tick,
                })
    
    # Sort by beat position
    cc64_events.sort(key=lambda x: x["beat"])
    
    # Analyze patterns
    press_release_pairs = []
    i = 0
    while i < len(cc64_events):
        if cc64_events[i]["value"] > 0:  # Press
            press_tick = cc64_events[i]["tick"]
            press_beat = cc64_events[i]["beat"]
            # Look for corresponding release
            release_tick = None
            release_beat = None
            for j in range(i + 1, len(cc64_events)):
                if cc64_events[j]["value"] == 0:
                    release_tick = cc64_events[j]["tick"]
                    release_beat = cc64_events[j]["beat"]
                    break
            if release_tick is not None:
                duration_ticks = release_tick - press_tick
                duration_beats = duration_ticks / ppq
                press_release_pairs.append({
                    "press_beat": press_beat,
                    "release_beat": release_beat,
                    "duration_beats": duration_beats,
                    "duration_ticks": duration_ticks,
                })
            i += 1
        else:
            i += 1
    
    return {
        "total_cc64_events": len(cc64_events),
        "events": cc64_events,
        "press_release_pairs": press_release_pairs,
        "press_count": sum(1 for e in cc64_events if e["value"] > 0),
        "release_count": sum(1 for e in cc64_events if e["value"] == 0),
        "unpaired_presses": sum(1 for e in cc64_events if e["value"] > 0) - len(press_release_pairs),
    }


def compare_json_vs_midi(json_path: Path, midi_path: Path) -> dict[str, Any]:
    """Compare pedal events in JSON vs MIDI."""
    json_analysis = analyze_json_pedal_events(json_path)
    midi_analysis = analyze_midi_pedal_events(midi_path)
    
    # Match JSON events to MIDI events
    matches = []
    json_events = json_analysis["events"]
    midi_events = midi_analysis.get("events", [])
    
    # For each JSON pedal event, try to find corresponding MIDI events
    for json_event in json_events:
        start = json_event["start"]
        duration = json_event["duration"]
        value = json_event["value"]
        
        # Find MIDI events near this start time (within 0.1 beats)
        matching_midi = [
            e for e in midi_events
            if abs(e["beat"] - start) < 0.1
        ]
        
        matches.append({
            "json_event": json_event,
            "matching_midi_events": matching_midi,
            "has_match": len(matching_midi) > 0,
        })
    
    return {
        "json_analysis": json_analysis,
        "midi_analysis": midi_analysis,
        "matches": matches,
        "json_has_pedals": json_analysis["total_pedal_events"] > 0,
        "midi_has_pedals": midi_analysis.get("total_cc64_events", 0) > 0,
        "pedals_lost": json_analysis["total_pedal_events"] > 0 and midi_analysis.get("total_cc64_events", 0) == 0,
    }


def analyze_all_compositions(output_dir: Path) -> dict[str, Any]:
    """Analyze all JSON/MIDI pairs in the output directory."""
    results = {}
    
    # Find all JSON files
    json_files = list(output_dir.glob("*.json"))
    
    for json_path in json_files:
        # Look for corresponding MIDI file
        midi_path = json_path.with_suffix(".mid")
        if not midi_path.exists():
            # Try with (1), (2) variants
            base_name = json_path.stem
            if "(" in base_name:
                base = base_name.rsplit("(", 1)[0].strip()
                midi_path = json_path.parent / f"{base}.mid"
        
        if midi_path.exists():
            try:
                comparison = compare_json_vs_midi(json_path, midi_path)
                results[json_path.name] = comparison
            except Exception as e:
                results[json_path.name] = {"error": str(e)}
    
    return results


def print_analysis_report(results: dict[str, Any]) -> None:
    """Print a comprehensive analysis report."""
    print("=" * 80)
    print("SUSTAIN PEDAL CONTROL ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    total_files = len(results)
    files_with_json_pedals = sum(1 for r in results.values() if r.get("json_has_pedals", False))
    files_with_midi_pedals = sum(1 for r in results.values() if r.get("midi_has_pedals", False))
    files_with_lost_pedals = sum(1 for r in results.values() if r.get("pedals_lost", False))
    
    print(f"Total compositions analyzed: {total_files}")
    print(f"Compositions with pedal events in JSON: {files_with_json_pedals}")
    print(f"Compositions with pedal events in MIDI: {files_with_midi_pedals}")
    print(f"Compositions with LOST pedals (JSON has, MIDI doesn't): {files_with_lost_pedals}")
    print()
    
    # Detailed analysis for each file
    for filename, data in sorted(results.items()):
        if "error" in data:
            print(f"\n{filename}: ERROR - {data['error']}")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"File: {filename}")
        print(f"{'=' * 80}")
        
        json_analysis = data.get("json_analysis", {})
        midi_analysis = data.get("midi_analysis", {})
        
        print(f"\nJSON Analysis:")
        print(f"  Total pedal events: {json_analysis.get('total_pedal_events', 0)}")
        print(f"  Events with duration=0: {json_analysis.get('duration_zero_count', 0)}")
        print(f"  Events with duration>0: {json_analysis.get('duration_positive_count', 0)}")
        print(f"  Events with value=127: {json_analysis.get('value_127_count', 0)}")
        print(f"  Events with value=0: {json_analysis.get('value_0_count', 0)}")
        
        if json_analysis.get("events"):
            print(f"\n  Pedal Events in JSON:")
            for i, event in enumerate(json_analysis["events"][:10]):  # Show first 10
                print(f"    {i+1}. start={event['start']:.2f}, duration={event['duration']:.2f}, value={event['value']}")
            if len(json_analysis["events"]) > 10:
                print(f"    ... and {len(json_analysis['events']) - 10} more")
        
        print(f"\nMIDI Analysis:")
        if "error" in midi_analysis:
            print(f"  ERROR: {midi_analysis['error']}")
        else:
            print(f"  Total CC64 events: {midi_analysis.get('total_cc64_events', 0)}")
            print(f"  Press events (value>0): {midi_analysis.get('press_count', 0)}")
            print(f"  Release events (value=0): {midi_analysis.get('release_count', 0)}")
            print(f"  Press-release pairs: {len(midi_analysis.get('press_release_pairs', []))}")
            print(f"  Unpaired presses: {midi_analysis.get('unpaired_presses', 0)}")
            
            if midi_analysis.get("events"):
                print(f"\n  CC64 Events in MIDI:")
                for i, event in enumerate(midi_analysis["events"][:10]):  # Show first 10
                    print(f"    {i+1}. beat={event['beat']:.2f}, value={event['value']}")
                if len(midi_analysis["events"]) > 10:
                    print(f"    ... and {len(midi_analysis['events']) - 10} more")
        
        # Comparison
        print(f"\nComparison:")
        if data.get("pedals_lost"):
            print(f"  ⚠️  WARNING: JSON has pedals but MIDI has NONE!")
        elif json_analysis.get("total_pedal_events", 0) > 0:
            json_count = json_analysis.get("total_pedal_events", 0)
            midi_count = midi_analysis.get("total_cc64_events", 0)
            if midi_count < json_count * 2:  # Each pedal event should create at least 2 MIDI events (press+release)
                print(f"  ⚠️  WARNING: MIDI has fewer CC64 events than expected")
                print(f"     Expected at least {json_count * 2} MIDI events, got {midi_count}")
            else:
                print(f"  ✓ Pedals appear to be rendered correctly")
        
        # Analyze duration=0 issue
        duration_zero = json_analysis.get("duration_zero_count", 0)
        if duration_zero > 0:
            print(f"\n  ⚠️  ISSUE: {duration_zero} pedal events have duration=0")
            print(f"     These are treated as instant press/release and may not create sustained pedaling")
    
    # Summary statistics
    print(f"\n{'=' * 80}")
    print("SUMMARY STATISTICS")
    print(f"{'=' * 80}")
    
    all_duration_zero = []
    all_duration_positive = []
    
    for data in results.values():
        if "error" in data:
            continue
        json_analysis = data.get("json_analysis", {})
        for event in json_analysis.get("events", []):
            if event["duration"] == 0:
                all_duration_zero.append(event)
            else:
                all_duration_positive.append(event)
    
    print(f"\nTotal pedal events across all files:")
    print(f"  Events with duration=0: {len(all_duration_zero)}")
    print(f"  Events with duration>0: {len(all_duration_positive)}")
    
    if all_duration_zero:
        print(f"\nPatterns in duration=0 events:")
        value_127_zero = sum(1 for e in all_duration_zero if e["value"] == 127)
        value_0_zero = sum(1 for e in all_duration_zero if e["value"] == 0)
        print(f"  duration=0, value=127 (instant press): {value_127_zero}")
        print(f"  duration=0, value=0 (instant release): {value_0_zero}")


def main():
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        # Try to find output directory
        possible_dirs = [
            Path("/workspace/output"),
            Path("output"),
            Path("../output"),
        ]
        output_dir = None
        for d in possible_dirs:
            if d.exists() and d.is_dir():
                output_dir = d
                break
        
        if output_dir is None:
            print("Error: Could not find output directory. Please specify as argument.")
            sys.exit(1)
    
    print(f"Analyzing compositions in: {output_dir}")
    print()
    
    results = analyze_all_compositions(output_dir)
    print_analysis_report(results)


if __name__ == "__main__":
    main()
