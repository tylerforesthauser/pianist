# Sustain Pedal Control Analysis

## Executive Summary

After deep analysis of the codebase and composition examples, I've identified the root cause of missing sustain pedal control in generated MIDI files:

**Problem**: Models are generating pedal events with `duration=0`, which the renderer treats as instant actions (single control_change message). For sustained pedaling, models should use `duration>0` to create press-release pairs.

## Key Findings

### 1. Schema Design

The `PedalEvent` schema (in `src/pianist/schema.py:256-271`) allows `duration=0`:

```python
class PedalEvent(BaseModel):
    """
    Sustain pedal (CC 64) event. `value` defaults to 127.
    
    Duration can be 0 for instant pedal releases (value=0) or instant pedal presses.
    """
    type: Literal["pedal"] = "pedal"
    start: Beat
    duration: Annotated[float, Field(ge=0)]  # Allows 0
    value: int = Field(default=127, ge=0, le=127)
```

**Issue**: The schema allows `duration=0`, but the documentation doesn't clearly explain when to use it vs `duration>0`.

### 2. Renderer Behavior

The renderer (in `src/pianist/renderers/mido_renderer.py:206-248`) handles pedal events differently based on duration:

- **`duration=0`**: Creates a single `control_change` message (instant action)
- **`duration>0`**: Creates two messages: press at `start`, release at `start+duration`

```python
if dur_ticks == 0:
    # Instant action: only send the value change, no release
    abs_msgs.append(_AbsMsg(start_tick, mido.Message("control_change", control=64, value=ev.value, ...)))
else:
    # Sustained pedal: press at start, release at end
    abs_msgs.append(_AbsMsg(start_tick, mido.Message("control_change", control=64, value=ev.value, ...)))
    abs_msgs.append(_AbsMsg(end_tick, mido.Message("control_change", control=64, value=0, ...)))
```

**Issue**: When models use `duration=0`, no release message is generated, so the pedal stays down indefinitely (or until the next pedal event).

### 3. Model Behavior Patterns

From analyzing example JSON files, models are generating patterns like:

```json
{"type": "pedal", "start": 0, "duration": 0, "value": 127}      // Instant press
{"type": "pedal", "start": 16, "duration": 0, "value": 0}     // Instant release
{"type": "pedal", "start": 16.5, "duration": 0, "value": 127}  // Instant press
```

**Problem**: This pattern requires the model to manually create press-release pairs using two separate events. This is error-prone and models often:
1. Forget to add the release event
2. Use incorrect timing
3. Create overlapping pedal events

### 4. Documentation Gap

The `AI_PROMPTING_GUIDE.md` shows a correct example:
```json
{ "type": "pedal", "start": 0, "duration": 4, "value": 127, "section": "A" }
```

But it doesn't explicitly explain:
- When to use `duration=0` vs `duration>0`
- That `duration>0` automatically creates press-release pairs
- That `duration=0` is only for special cases

## Root Cause Analysis

**Primary Issue**: Models are treating pedal events like note events, where `duration=0` might seem reasonable for "instant" actions. However, for sustain pedal, `duration` represents how long the pedal should be held down, not the duration of an action.

**Secondary Issues**:
1. Schema allows `duration=0` without clear guidance on when to use it
2. Documentation doesn't emphasize that `duration>0` is the standard pattern
3. Models may be inferring from the schema that `duration=0` is acceptable for all cases

## Recommended Fixes

### Fix 1: Improve Schema Documentation

Update `PedalEvent` docstring to be more explicit:

```python
class PedalEvent(BaseModel):
    """
    Sustain pedal (CC 64) event.
    
    For sustained pedaling (most common case):
    - Set `duration` > 0 to specify how long the pedal should be held down
    - The renderer will automatically create a press at `start` and release at `start+duration`
    - Example: {"type": "pedal", "start": 0, "duration": 4, "value": 127}
      This holds the pedal down for 4 beats, then releases it.
    
    For instant press/release (rare, advanced use):
    - Set `duration` = 0 for a single control_change message
    - Use value=127 for instant press, value=0 for instant release
    - You must manually manage press-release pairs
    - Example: {"type": "pedal", "start": 0, "duration": 0, "value": 127}
      This sends a single press message (no automatic release).
    
    Default value is 127 (full pedal down).
    """
```

### Fix 2: Update AI_PROMPTING_GUIDE.md

Add a dedicated section on pedal usage:

```markdown
#### Sustain Pedal Control

For sustain pedal events, **always use `duration > 0`** to specify how long the pedal should be held down:

```json
{ "type": "pedal", "start": 0, "duration": 4, "value": 127 }
```

This automatically creates:
- A pedal press (CC64=127) at `start`
- A pedal release (CC64=0) at `start + duration`

**Important**: 
- Use `duration > 0` for all normal pedaling (this is the standard pattern)
- The renderer handles press/release automatically - you don't need separate events
- Only use `duration = 0` in special cases where you need manual control

**Common Patterns**:
- Hold pedal for a measure: `{"type": "pedal", "start": 0, "duration": 4, "value": 127}`
- Hold pedal for a phrase: `{"type": "pedal", "start": 0, "duration": 8, "value": 127}`
- Change pedal with harmony: Release and press at chord changes
```

### Fix 3: Add Validation Warning (Optional)

Consider adding a validator that warns when `duration=0` is used with `value=127` (common mistake):

```python
@model_validator(mode="after")
def _warn_duration_zero(self) -> "PedalEvent":
    if self.duration == 0 and self.value == 127:
        # This is likely a mistake - duration=0 with value=127 creates an instant press
        # with no automatic release. Most pedaling should use duration>0.
        import warnings
        warnings.warn(
            f"PedalEvent at start={self.start} has duration=0 with value=127. "
            "This creates an instant press with no automatic release. "
            "For sustained pedaling, use duration>0 instead.",
            UserWarning,
            stacklevel=2
        )
    return self
```

### Fix 4: Update Schema Examples

Ensure all schema examples use `duration>0`:

- Update `schema.openapi.json` examples
- Update `schema.gemini.json` examples
- Update any test examples that might be used as templates

### Fix 5: Post-Processing Fix (Code-Level)

As a safety net, we could add a post-processing step that converts problematic `duration=0` patterns:

```python
def _fix_pedal_durations(comp: Composition) -> Composition:
    """Fix common pedal duration issues."""
    fixed = comp.model_copy(deep=True)
    
    for track in fixed.tracks:
        # Find pedal events with duration=0 and value=127
        # If followed by a release, convert to duration>0
        events = track.events
        i = 0
        while i < len(events):
            if isinstance(events[i], PedalEvent) and events[i].duration == 0 and events[i].value == 127:
                # Look for next release
                for j in range(i + 1, len(events)):
                    if isinstance(events[j], PedalEvent) and events[j].duration == 0 and events[j].value == 0:
                        # Convert to single event with duration
                        duration = events[j].start - events[i].start
                        if duration > 0:
                            events[i].duration = duration
                            # Remove the release event
                            events.pop(j)
                        break
            i += 1
    
    return fixed
```

**Note**: This is a workaround. The better fix is to improve prompts/documentation so models generate correct patterns from the start.

## Implementation Priority

1. **High Priority**: Fix 1 (Schema docs) + Fix 2 (Prompt guide) - These address the root cause
2. **Medium Priority**: Fix 4 (Schema examples) - Ensures consistency
3. **Low Priority**: Fix 3 (Validation warning) - Helpful for debugging
4. **Optional**: Fix 5 (Post-processing) - Safety net, but shouldn't be needed if Fixes 1-2 work

## Testing Recommendations

1. Generate test compositions with explicit pedal instructions
2. Verify that `duration>0` events create proper press-release pairs in MIDI
3. Test edge cases: overlapping pedals, very short durations, etc.
4. Compare before/after MIDI files to ensure pedaling is preserved

## Conclusion

The issue is primarily a documentation and guidance problem. Models are using `duration=0` because:
1. The schema allows it without clear guidance
2. The documentation doesn't emphasize `duration>0` as the standard pattern
3. Models may be inferring incorrect usage patterns

By improving documentation and examples, we can guide models to use the correct pattern (`duration>0`) which will automatically create proper press-release pairs in the MIDI output.
