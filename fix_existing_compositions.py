#!/usr/bin/env python3
"""
Fix sustain pedal patterns in existing composition files.

This script fixes the specific files mentioned by the user:
- Nocturne in Eb Major.json
- Rhapsody in G Minor - Mono no Aware.json
- Sonata in D Major (2).json

Usage:
    python fix_existing_compositions.py <output_directory>
"""

import json
import sys
from pathlib import Path

# Add src to path so we can import pianist modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pianist.parser import parse_composition_from_text
from pianist.pedal_fix import fix_pedal_patterns
from pianist.iterate import composition_to_canonical_json
from pianist.renderers.mido_renderer import render_midi_mido


def analyze_and_fix_file(json_path: Path, output_dir: Path) -> dict:
    """Analyze and fix a single JSON file."""
    print(f"\n{'=' * 80}")
    print(f"Processing: {json_path.name}")
    print(f"{'=' * 80}")
    
    # Load composition
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            text = f.read()
        comp = parse_composition_from_text(text)
    except Exception as e:
        return {"error": str(e), "fixed": False}
    
    # Analyze before
    pedal_events_before = []
    for track in comp.tracks:
        for ev in track.events:
            if hasattr(ev, 'type') and ev.type == 'pedal':
                pedal_events_before.append({
                    "start": ev.start,
                    "duration": ev.duration,
                    "value": ev.value,
                })
    
    duration_zero_before = sum(1 for p in pedal_events_before if p["duration"] == 0)
    duration_positive_before = sum(1 for p in pedal_events_before if p["duration"] > 0)
    
    print(f"\nBefore fix:")
    print(f"  Total pedal events: {len(pedal_events_before)}")
    print(f"  Events with duration=0: {duration_zero_before}")
    print(f"  Events with duration>0: {duration_positive_before}")
    
    if duration_zero_before > 0:
        print(f"\n  Problematic events (duration=0):")
        for i, p in enumerate(pedal_events_before):
            if p["duration"] == 0:
                print(f"    {i+1}. start={p['start']:.2f}, duration={p['duration']}, value={p['value']}")
    
    # Fix pedal patterns
    fixed = fix_pedal_patterns(comp)
    
    # Analyze after
    pedal_events_after = []
    for track in fixed.tracks:
        for ev in track.events:
            if hasattr(ev, 'type') and ev.type == 'pedal':
                pedal_events_after.append({
                    "start": ev.start,
                    "duration": ev.duration,
                    "value": ev.value,
                })
    
    duration_zero_after = sum(1 for p in pedal_events_after if p["duration"] == 0)
    duration_positive_after = sum(1 for p in pedal_events_after if p["duration"] > 0)
    
    print(f"\nAfter fix:")
    print(f"  Total pedal events: {len(pedal_events_after)}")
    print(f"  Events with duration=0: {duration_zero_after}")
    print(f"  Events with duration>0: {duration_positive_after}")
    
    if duration_positive_after > 0:
        print(f"\n  Fixed events (duration>0):")
        for i, p in enumerate(pedal_events_after[:10]):  # Show first 10
            if p["duration"] > 0:
                print(f"    {i+1}. start={p['start']:.2f}, duration={p['duration']:.2f}, value={p['value']}")
        if len(pedal_events_after) > 10:
            print(f"    ... and {len(pedal_events_after) - 10} more")
    
    # Save fixed JSON
    fixed_json_path = output_dir / json_path.name
    fixed_json = composition_to_canonical_json(fixed)
    fixed_json_path.write_text(fixed_json, encoding='utf-8')
    print(f"\n  Saved fixed JSON to: {fixed_json_path}")
    
    # Render to MIDI
    midi_path = output_dir / json_path.with_suffix('.mid').name
    try:
        render_midi_mido(fixed, midi_path)
        print(f"  Rendered MIDI to: {midi_path}")
    except Exception as e:
        print(f"  Warning: Could not render MIDI: {e}")
        midi_path = None
    
    return {
        "fixed": True,
        "before": {
            "total": len(pedal_events_before),
            "duration_zero": duration_zero_before,
            "duration_positive": duration_positive_before,
        },
        "after": {
            "total": len(pedal_events_after),
            "duration_zero": duration_zero_after,
            "duration_positive": duration_positive_after,
        },
        "json_path": fixed_json_path,
        "midi_path": midi_path,
    }


def main():
    """Fix the specified composition files."""
    if len(sys.argv) < 2:
        print("Usage: fix_existing_compositions.py <output_directory>")
        print("\nThis script fixes pedal patterns in:")
        print("  - Nocturne in Eb Major.json")
        print("  - Rhapsody in G Minor - Mono no Aware.json")
        print("  - Sonata in D Major (2).json")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)
    
    # Files to fix
    files_to_fix = [
        "Nocturne in Eb Major.json",
        "Rhapsody in G Minor - Mono no Aware.json",
        "Sonata in D Major (2).json",
    ]
    
    results = {}
    for filename in files_to_fix:
        json_path = output_dir / filename
        if not json_path.exists():
            print(f"\nWarning: File not found: {json_path}")
            results[filename] = {"error": "File not found", "fixed": False}
            continue
        
        results[filename] = analyze_and_fix_file(json_path, output_dir)
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    
    fixed_count = sum(1 for r in results.values() if r.get("fixed", False))
    total_count = len(results)
    
    print(f"\nFixed {fixed_count} out of {total_count} files:")
    for filename, result in results.items():
        if result.get("fixed"):
            before = result["before"]
            after = result["after"]
            print(f"\n  {filename}:")
            print(f"    Before: {before['duration_zero']} duration=0, {before['duration_positive']} duration>0")
            print(f"    After:  {after['duration_zero']} duration=0, {after['duration_positive']} duration>0")
            if result.get("midi_path"):
                print(f"    MIDI: {result['midi_path']}")
        else:
            error = result.get("error", "Unknown error")
            print(f"\n  {filename}: FAILED - {error}")


if __name__ == "__main__":
    main()
