# Analysis Library Decision

## Recommendation: music21

Based on research and project requirements, **music21** is the recommended choice for the musical analysis module.

## Rationale

### 1. **Comprehensive Capabilities**
- ✅ **Harmonic Analysis**: Strong chord identification and Roman numeral analysis
- ✅ **Pattern Matching**: Built-in pattern search capabilities
- ✅ **Form Analysis**: Can identify musical forms and sections
- ✅ **MIDI Support**: Works with MIDI files (our format)
- ⚠️ **Motif/Phrase Detection**: Foundation exists, but we'll build custom algorithms on top

### 2. **Project Fit**
- **License**: MIT (compatible with our MIT license)
- **Maturity**: Well-established, actively maintained
- **Documentation**: Comprehensive documentation available
- **Community**: Active community and support

### 3. **Integration Strategy**
We'll use a hybrid approach:
- **Use music21 for**: Harmonic analysis, pattern matching foundation, form detection
- **Build custom for**: Motif detection, phrase detection, expansion strategies

### 4. **Compatibility**
- Works with MIDI files (we already use `mido` for I/O)
- Can convert our `Composition` format to music21's `stream` format
- No conflicts with existing dependencies

## Implementation Plan

### Phase 1: Setup
1. Add `music21>=9.0.0` to `pyproject.toml` dependencies
2. Create conversion utilities: `Composition` → `music21.stream.Stream`
3. Test basic conversion with sample compositions

### Phase 2: Basic Analysis
1. Implement harmonic analysis using music21
2. Implement basic pattern matching
3. Implement form detection (basic)

### Phase 3: Custom Algorithms
1. Build motif detection on top of music21's pattern matching
2. Build phrase detection using music21's structure analysis
3. Integrate with expansion strategy generation

## Alternative Considered: Custom Implementation

**Why not chosen:**
- Would require significant music theory expertise
- Time-consuming to develop from scratch
- music21 provides solid foundation we can build on
- Better to leverage existing, tested code

## Next Steps

1. ✅ **Decision made**: Use music21
2. [ ] Add music21 to dependencies
3. [ ] Create conversion layer (`Composition` → `music21.stream`)
4. [ ] Implement basic harmonic analysis
5. [ ] Test with sample compositions
6. [ ] Build custom motif/phrase detection on top

## Questions Answered

- **Which library?** → music21
- **Why music21?** → Comprehensive, mature, good fit for our needs
- **What will we build custom?** → Motif detection, phrase detection, expansion strategies
- **Integration approach?** → Hybrid: use music21 for foundation, build custom on top

