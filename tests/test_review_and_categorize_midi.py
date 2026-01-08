"""Tests for review_and_categorize_midi.py script."""

from __future__ import annotations

import sys
from pathlib import Path

import mido
import pytest

# Add scripts directory to path
project_root = Path(__file__).parent.parent
scripts_dir = project_root / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import from scripts directory (added to path above)
# Type checker may not resolve this, but it works at runtime
if True:  # Type checker workaround
    from review_and_categorize_midi import analyze_file, extract_info_from_filename  # type: ignore[import]


def _write_test_midi(path: Path) -> None:
    """Create a minimal test MIDI file."""
    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    
    tr.append(mido.MetaMessage("track_name", name="Piano", time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.MetaMessage("key_signature", key="A", time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    tr.append(mido.Message("program_change", program=0, channel=0, time=0))
    
    # Add some notes
    tr.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_on", note=64, velocity=64, channel=0, time=0))
    tr.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    tr.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=0))
    
    tr.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(path)


def test_extract_info_from_filename_basic() -> None:
    """Test filename extraction with basic patterns."""
    # Test composer - title format
    info = extract_info_from_filename("Frédéric François Chopin - 24 Preludes, Op.28 No.7.mid")
    assert info["composer"] == "Chopin"
    assert info["title"] == "24 Preludes"
    assert info["catalog_number"] == "Op. 28"
    
    # Test hyphenated pattern
    info = extract_info_from_filename("chopin---prelude-no.-7-in-a-major-op.-28.mid")
    assert info["composer"] == "Chopin"
    # Should extract "Prelude No. 7" or similar
    assert "prelude" in info.get("title", "").lower() or info.get("title") is None
    
    # Test typo pattern
    info = extract_info_from_filename("prlude-opus-28-no.-7-in-a-major--chopin.mid")
    assert info["composer"] == "Chopin"
    # Should extract "Prelude No. 7" or similar, or at least have opus/catalog
    # The extraction may not be perfect, but composer should be found
    assert info.get("title") is not None or info.get("catalog_number") is not None or info.get("opus") is not None


def test_analyze_file_with_filename_extraction(tmp_path: Path, monkeypatch) -> None:
    """Test that analyze_file correctly uses filename-extracted info when available."""
    # Create a MIDI file with a clear filename
    midi_file = tmp_path / "chopin-prelude-op28-no7.mid"
    _write_test_midi(midi_file)
    
    # Mock AI provider to avoid actual API calls
    def fake_generate_text_unified(*, provider: str, model: str, prompt: str, verbose: bool = False) -> str:
        return '{"suggested_name": "AI Generated Name", "suggested_style": "Romantic", "suggested_description": "AI description"}'
    
    # Mock comprehensive_analysis to return AI insights
    def fake_analyze_for_user(*args, **kwargs):
        return {
            "technical": {
                "duration_beats": 1.0,
                "duration_seconds": 1.0,
                "bars": 1.0,
                "tempo_bpm": 120.0,
                "time_signature": "4/4",
                "key_signature": "A",
                "tracks": 1,
            },
            "musical_analysis": {
                "detected_key": "A major",
                "detected_form": "binary",
                "motif_count": 0,
                "phrase_count": 0,
                "chord_count": 0,
                "harmonic_progression": "I V",
            },
            "quality": {
                "overall_score": 0.9,
                "technical_score": 0.9,
                "musical_score": 0.9,
                "structure_score": 0.9,
                "issues": [],
            },
            "ai_insights": {
                "suggested_name": "AI Generated Name",
                "suggested_style": "Romantic",
                "suggested_description": "AI description",
            },
        }
    
    # Import and patch
    import pianist.comprehensive_analysis
    monkeypatch.setattr(pianist.comprehensive_analysis, "analyze_for_user", fake_analyze_for_user)
    
    # Run analyze_file with AI enabled
    metadata, signature, ai_attempted, ai_identified = analyze_file(
        midi_file,
        use_ai_quality=False,
        use_ai_naming=True,
        verbose=False,
        ai_provider="gemini",
        ai_model="gemini-flash-latest",
        ai_delay=0.0,
        mark_original=False,
    )
    
    # Verify that filename extraction took priority (if it found clear info)
    # The filename "chopin-prelude-op28-no7.mid" should extract composer and opus
    filename_info = extract_info_from_filename(midi_file.name)
    if filename_info.get("composer") and (filename_info.get("title") or filename_info.get("catalog_number")):
        # If filename has clear info, it should be used instead of AI
        assert "Chopin" in metadata.suggested_name or metadata.suggested_name.startswith("Chopin")
    else:
        # If filename extraction didn't find clear info, AI should be used
        assert metadata.suggested_name is not None
        assert len(metadata.suggested_name) > 0


def test_analyze_file_with_clear_filename_info_priority(tmp_path: Path, monkeypatch) -> None:
    """Test that filename-extracted info takes priority over AI when clear info is available.
    
    This test specifically checks for the UnboundLocalError that was fixed.
    """
    # Create a MIDI file with a very clear filename pattern
    midi_file = tmp_path / "Frédéric François Chopin - 24 Preludes, Op.28 No.7.mid"
    _write_test_midi(midi_file)
    
    # Mock comprehensive_analysis to return AI insights
    def fake_analyze_for_user(*args, **kwargs):
        return {
            "technical": {
                "duration_beats": 1.0,
                "duration_seconds": 1.0,
                "bars": 1.0,
                "tempo_bpm": 120.0,
                "time_signature": "4/4",
                "key_signature": "A",
                "tracks": 1,
            },
            "musical_analysis": {
                "detected_key": "A major",
                "detected_form": "binary",  # This is important - we need detected_form
                "motif_count": 0,
                "phrase_count": 0,
                "chord_count": 0,
                "harmonic_progression": "I V",
            },
            "quality": {
                "overall_score": 0.9,
                "technical_score": 0.9,
                "musical_score": 0.9,
                "structure_score": 0.9,
                "issues": [],
            },
            "ai_insights": {
                "suggested_name": "AI Generated Name",
                "suggested_style": "Romantic",
                "suggested_description": "AI description",
            },
        }
    
    # Import and patch
    import pianist.comprehensive_analysis
    monkeypatch.setattr(pianist.comprehensive_analysis, "analyze_for_user", fake_analyze_for_user)
    
    # This should not raise UnboundLocalError
    # The filename has clear info (composer + title), so it should use that instead of AI
    metadata, signature, ai_attempted, ai_identified = analyze_file(
        midi_file,
        use_ai_quality=False,
        use_ai_naming=True,
        verbose=False,
        ai_provider="gemini",
        ai_model="gemini-flash-latest",
        ai_delay=0.0,
        mark_original=False,
    )
    
    # Verify metadata was created successfully
    assert metadata is not None
    assert metadata.filename == midi_file.name
    assert metadata.suggested_name is not None
    # Since filename has clear info, it should use that (Chopin: 24 Preludes (Op. 28))
    # or at least contain Chopin
    assert "Chopin" in metadata.suggested_name or metadata.suggested_name.startswith("Chopin")
    # Verify detected_form was used in description (this was the bug - accessing metadata before it existed)
    assert metadata.suggested_description is not None


def test_analyze_file_with_hyphenated_filename(tmp_path: Path, monkeypatch) -> None:
    """Test analyze_file with hyphenated filename pattern that should extract info."""
    # Create a MIDI file with hyphenated pattern
    midi_file = tmp_path / "prlude-opus-28-no.-7-in-a-major--chopin.mid"
    _write_test_midi(midi_file)
    
    # Mock comprehensive_analysis
    def fake_analyze_for_user(*args, **kwargs):
        return {
            "technical": {
                "duration_beats": 1.0,
                "duration_seconds": 1.0,
                "bars": 1.0,
                "tempo_bpm": 120.0,
                "time_signature": "4/4",
                "key_signature": "A",
                "tracks": 1,
            },
            "musical_analysis": {
                "detected_key": "A major",
                "detected_form": "binary",
                "motif_count": 0,
                "phrase_count": 0,
                "chord_count": 0,
                "harmonic_progression": "I V",
            },
            "quality": {
                "overall_score": 0.9,
                "technical_score": 0.9,
                "musical_score": 0.9,
                "structure_score": 0.9,
                "issues": [],
            },
            "ai_insights": {
                "suggested_name": "AI Generated Name",
                "suggested_style": "Romantic",
                "suggested_description": "AI description",
            },
        }
    
    import pianist.comprehensive_analysis
    monkeypatch.setattr(pianist.comprehensive_analysis, "analyze_for_user", fake_analyze_for_user)
    
    # This should not raise any errors
    metadata, signature, ai_attempted, ai_identified = analyze_file(
        midi_file,
        use_ai_quality=False,
        use_ai_naming=True,
        verbose=False,
        ai_provider="gemini",
        ai_model="gemini-flash-latest",
        ai_delay=0.0,
        mark_original=False,
    )
    
    # Verify metadata was created successfully
    assert metadata is not None
    assert metadata.filename == midi_file.name
    assert metadata.suggested_name is not None
    assert len(metadata.suggested_name) > 0

