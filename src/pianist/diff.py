"""
Diff utilities for comparing compositions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Composition, Event, NoteEvent, PedalEvent, SectionEvent, TempoEvent


@dataclass
class EventDiff:
    """Represents a difference in a single event."""

    event_type: str  # "added", "removed", "modified"
    original: Event | None
    modified: Event | None
    track_index: int
    event_index: int | None = None


@dataclass
class CompositionDiff:
    """Represents differences between two compositions."""

    original: Composition
    modified: Composition

    # Metadata differences
    title_changed: bool = False
    bpm_changed: bool = False
    time_signature_changed: bool = False
    key_signature_changed: bool = False
    ppq_changed: bool = False

    # Track differences
    track_count_changed: bool = False
    track_diffs: list[list[EventDiff]] = None  # List of event diffs per track

    # Summary statistics
    total_events_added: int = 0
    total_events_removed: int = 0
    total_events_modified: int = 0

    def __post_init__(self):
        if self.track_diffs is None:
            self.track_diffs = []


def _events_match(event1: Event, event2: Event, tolerance: float = 0.01) -> bool:
    """Check if two events are essentially the same."""
    if type(event1) is not type(event2):
        return False

    # Compare basic properties
    if abs(event1.start - event2.start) > tolerance:
        return False

    if (
        hasattr(event1, "duration")
        and hasattr(event2, "duration")
        and abs(event1.duration - event2.duration) > tolerance
    ):
        return False

    # Type-specific comparisons
    if isinstance(event1, NoteEvent) and isinstance(event2, NoteEvent):
        # Compare pitches (order-independent for chords)
        pitches1 = set(event1.pitches) if hasattr(event1, "pitches") else set()
        pitches2 = set(event2.pitches) if hasattr(event2, "pitches") else set()
        if pitches1 != pitches2:
            return False

        if event1.velocity != event2.velocity:
            return False

    elif isinstance(event1, PedalEvent) and isinstance(event2, PedalEvent):
        if abs(event1.duration - event2.duration) > tolerance:
            return False
        if event1.value != event2.value:
            return False

    elif isinstance(event1, TempoEvent) and isinstance(event2, TempoEvent):
        if event1.bpm is not None and event2.bpm is not None:
            if abs(event1.bpm - event2.bpm) > 0.1:
                return False
        elif event1.bpm != event2.bpm:
            return False

    elif isinstance(event1, SectionEvent) and isinstance(event2, SectionEvent):
        if event1.label != event2.label:
            return False

    return True


def _find_matching_event(
    event: Event, events: list[Event], start_index: int = 0, tolerance: float = 0.01
) -> int | None:
    """Find the index of a matching event in a list, starting from start_index."""
    for i in range(start_index, len(events)):
        if _events_match(event, events[i], tolerance):
            return i
    return None


def diff_compositions(original: Composition, modified: Composition) -> CompositionDiff:
    """
    Compare two compositions and return a diff.

    Uses a simple algorithm:
    1. Compare metadata
    2. For each track, compare events using a greedy matching algorithm
    3. Identify added, removed, and modified events
    """
    diff = CompositionDiff(original=original, modified=modified)

    # Compare metadata
    diff.title_changed = original.title != modified.title
    diff.bpm_changed = abs(original.bpm - modified.bpm) > 0.1
    diff.time_signature_changed = (
        original.time_signature.numerator != modified.time_signature.numerator
        or original.time_signature.denominator != modified.time_signature.denominator
    )
    diff.key_signature_changed = original.key_signature != modified.key_signature
    diff.ppq_changed = original.ppq != modified.ppq
    diff.track_count_changed = len(original.tracks) != len(modified.tracks)

    # Compare tracks
    max_tracks = max(len(original.tracks), len(modified.tracks))
    for track_idx in range(max_tracks):
        if track_idx >= len(original.tracks):
            # New track added
            track_diffs = []
            for event_idx, event in enumerate(modified.tracks[track_idx].events):
                track_diffs.append(
                    EventDiff(
                        event_type="added",
                        original=None,
                        modified=event,
                        track_index=track_idx,
                        event_index=event_idx,
                    )
                )
                diff.total_events_added += 1
            diff.track_diffs.append(track_diffs)
            continue

        if track_idx >= len(modified.tracks):
            # Track removed
            track_diffs = []
            for event_idx, event in enumerate(original.tracks[track_idx].events):
                track_diffs.append(
                    EventDiff(
                        event_type="removed",
                        original=event,
                        modified=None,
                        track_index=track_idx,
                        event_index=event_idx,
                    )
                )
                diff.total_events_removed += 1
            diff.track_diffs.append(track_diffs)
            continue

        # Compare events in this track
        original_events = original.tracks[track_idx].events
        modified_events = modified.tracks[track_idx].events
        track_diffs = []

        # Simple greedy matching algorithm
        original_used = [False] * len(original_events)
        modified_used = [False] * len(modified_events)

        # First pass: find exact matches
        for orig_idx, orig_event in enumerate(original_events):
            if original_used[orig_idx]:
                continue

            match_idx = _find_matching_event(orig_event, modified_events, 0)
            if match_idx is not None and not modified_used[match_idx]:
                original_used[orig_idx] = True
                modified_used[match_idx] = True
                # Events match - no diff entry needed

        # Second pass: identify removed events
        for orig_idx, orig_event in enumerate(original_events):
            if not original_used[orig_idx]:
                track_diffs.append(
                    EventDiff(
                        event_type="removed",
                        original=orig_event,
                        modified=None,
                        track_index=track_idx,
                        event_index=orig_idx,
                    )
                )
                diff.total_events_removed += 1

        # Third pass: identify added events
        for mod_idx, mod_event in enumerate(modified_events):
            if not modified_used[mod_idx]:
                track_diffs.append(
                    EventDiff(
                        event_type="added",
                        original=None,
                        modified=mod_event,
                        track_index=track_idx,
                        event_index=mod_idx,
                    )
                )
                diff.total_events_added += 1

        diff.track_diffs.append(track_diffs)

    return diff


def format_diff_text(diff: CompositionDiff, show_preserved: bool = False) -> str:  # noqa: ARG001
    """Format a diff as human-readable text."""
    lines = []

    lines.append("=" * 60)
    lines.append("Composition Diff")
    lines.append("=" * 60)
    lines.append("")

    # Metadata changes
    if (
        diff.title_changed
        or diff.bpm_changed
        or diff.time_signature_changed
        or diff.key_signature_changed
        or diff.ppq_changed
    ):
        lines.append("Metadata Changes:")
        if diff.title_changed:
            lines.append(f"  Title: '{diff.original.title}' → '{diff.modified.title}'")
        if diff.bpm_changed:
            lines.append(f"  BPM: {diff.original.bpm} → {diff.modified.bpm}")
        if diff.time_signature_changed:
            orig_ts = f"{diff.original.time_signature.numerator}/{diff.original.time_signature.denominator}"
            mod_ts = f"{diff.modified.time_signature.numerator}/{diff.modified.time_signature.denominator}"
            lines.append(f"  Time Signature: {orig_ts} → {mod_ts}")
        if diff.key_signature_changed:
            lines.append(f"  Key: {diff.original.key_signature} → {diff.modified.key_signature}")
        if diff.ppq_changed:
            lines.append(f"  PPQ: {diff.original.ppq} → {diff.modified.ppq}")
        lines.append("")

    # Track count changes
    if diff.track_count_changed:
        lines.append(f"Track Count: {len(diff.original.tracks)} → {len(diff.modified.tracks)}")
        lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  Events added: {diff.total_events_added}")
    lines.append(f"  Events removed: {diff.total_events_removed}")
    lines.append(f"  Events modified: {diff.total_events_modified}")
    lines.append("")

    # Event changes by track
    for track_idx, track_diff_list in enumerate(diff.track_diffs):
        if not track_diff_list:
            continue

        lines.append(
            f"Track {track_idx + 1} ({diff.original.tracks[track_idx].name if track_idx < len(diff.original.tracks) else diff.modified.tracks[track_idx].name}):"
        )

        for event_diff in track_diff_list:
            if event_diff.event_type == "removed":
                event = event_diff.original
                lines.append(f"  [-] Removed at beat {event.start:.2f}: {_event_summary(event)}")
            elif event_diff.event_type == "added":
                event = event_diff.modified
                lines.append(f"  [+] Added at beat {event.start:.2f}: {_event_summary(event)}")
            elif event_diff.event_type == "modified":
                orig = event_diff.original
                mod = event_diff.modified
                lines.append(f"  [~] Modified at beat {orig.start:.2f}:")
                lines.append(f"      Original: {_event_summary(orig)}")
                lines.append(f"      Modified: {_event_summary(mod)}")

        lines.append("")

    return "\n".join(lines)


def _event_summary(event: Event) -> str:
    """Get a brief summary of an event."""
    if isinstance(event, NoteEvent):
        pitches_str = ",".join(str(p) for p in event.pitches[:5])
        if len(event.pitches) > 5:
            pitches_str += "..."
        return f"Note({pitches_str}) duration={event.duration:.2f}"
    elif isinstance(event, PedalEvent):
        return f"Pedal(duration={event.duration:.2f}, value={event.value})"
    elif isinstance(event, TempoEvent):
        bpm = event.bpm or (f"{event.start_bpm}→{event.end_bpm}" if event.start_bpm else "?")
        return f"Tempo(bpm={bpm})"
    elif isinstance(event, SectionEvent):
        return f"Section('{event.label}')"
    else:
        return str(event.type)


def format_diff_json(diff: CompositionDiff) -> str:
    """Format a diff as JSON."""
    import json

    data = {
        "metadata_changes": {
            "title": diff.title_changed,
            "bpm": diff.bpm_changed,
            "time_signature": diff.time_signature_changed,
            "key_signature": diff.key_signature_changed,
            "ppq": diff.ppq_changed,
        },
        "track_count_changed": diff.track_count_changed,
        "summary": {
            "events_added": diff.total_events_added,
            "events_removed": diff.total_events_removed,
            "events_modified": diff.total_events_modified,
        },
        "tracks": [],
    }

    for track_idx, track_diff_list in enumerate(diff.track_diffs):
        track_data = {"track_index": track_idx, "changes": []}

        for event_diff in track_diff_list:
            change_data = {
                "type": event_diff.event_type,
                "start": None,
            }

            if event_diff.original:
                change_data["start"] = event_diff.original.start
                change_data["original"] = _event_summary(event_diff.original)
            if event_diff.modified:
                change_data["start"] = event_diff.modified.start
                change_data["modified"] = _event_summary(event_diff.modified)

            track_data["changes"].append(change_data)

        if track_data["changes"]:
            data["tracks"].append(track_data)

    return json.dumps(data, indent=2)


def format_diff_markdown(diff: CompositionDiff) -> str:
    """Format a diff as Markdown."""
    lines = []

    lines.append("# Composition Diff")
    lines.append("")

    # Metadata changes
    if (
        diff.title_changed
        or diff.bpm_changed
        or diff.time_signature_changed
        or diff.key_signature_changed
        or diff.ppq_changed
    ):
        lines.append("## Metadata Changes")
        lines.append("")
        if diff.title_changed:
            lines.append(f"- **Title**: `{diff.original.title}` → `{diff.modified.title}`")
        if diff.bpm_changed:
            lines.append(f"- **BPM**: `{diff.original.bpm}` → `{diff.modified.bpm}`")
        if diff.time_signature_changed:
            orig_ts = f"{diff.original.time_signature.numerator}/{diff.original.time_signature.denominator}"
            mod_ts = f"{diff.modified.time_signature.numerator}/{diff.modified.time_signature.denominator}"
            lines.append(f"- **Time Signature**: `{orig_ts}` → `{mod_ts}`")
        if diff.key_signature_changed:
            lines.append(
                f"- **Key**: `{diff.original.key_signature}` → `{diff.modified.key_signature}`"
            )
        if diff.ppq_changed:
            lines.append(f"- **PPQ**: `{diff.original.ppq}` → `{diff.modified.ppq}`")
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Events added**: {diff.total_events_added}")
    lines.append(f"- **Events removed**: {diff.total_events_removed}")
    lines.append(f"- **Events modified**: {diff.total_events_modified}")
    lines.append("")

    # Event changes by track
    for track_idx, track_diff_list in enumerate(diff.track_diffs):
        if not track_diff_list:
            continue

        track_name = (
            diff.original.tracks[track_idx].name
            if track_idx < len(diff.original.tracks)
            else diff.modified.tracks[track_idx].name
        )
        lines.append(f"## Track {track_idx + 1}: {track_name}")
        lines.append("")

        for event_diff in track_diff_list:
            if event_diff.event_type == "removed":
                event = event_diff.original
                lines.append(
                    f"- ❌ **Removed** at beat {event.start:.2f}: `{_event_summary(event)}`"
                )
            elif event_diff.event_type == "added":
                event = event_diff.modified
                lines.append(f"- ✅ **Added** at beat {event.start:.2f}: `{_event_summary(event)}`")
            elif event_diff.event_type == "modified":
                orig = event_diff.original
                mod = event_diff.modified
                lines.append(f"- 🔄 **Modified** at beat {orig.start:.2f}:")
                lines.append(f"  - Original: `{_event_summary(orig)}`")
                lines.append(f"  - Modified: `{_event_summary(mod)}`")

        lines.append("")

    return "\n".join(lines)
