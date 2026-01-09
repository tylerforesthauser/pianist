"""Tests for quality module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pianist.quality import (
    QualityIssue,
    QualityReport,
    check_musical_quality,
    check_structure_quality,
    check_technical_quality,
)


def test_quality_issue() -> None:
    """Test QualityIssue class."""
    issue = QualityIssue(
        severity="warning",
        category="technical",
        message="Test issue",
        details={"key": "value"},
    )
    assert issue.severity == "warning"
    assert issue.category == "technical"
    assert issue.message == "Test issue"
    assert issue.details == {"key": "value"}


def test_quality_report() -> None:
    """Test QualityReport class."""
    report = QualityReport(Path("test.mid"))
    assert report.file_path == Path("test.mid")
    assert len(report.issues) == 0
    assert report.overall_score == 0.0

    # Add issues
    issue1 = QualityIssue("error", "technical", "Error 1")
    issue2 = QualityIssue("warning", "musical", "Warning 1")
    report.add_issue(issue1)
    report.add_issue(issue2)

    assert len(report.issues) == 2

    # Calculate scores
    report.calculate_scores()
    assert report.overall_score < 1.0  # Should be penalized for errors
    assert "technical" in report.scores
    assert "musical" in report.scores
    assert "structure" in report.scores


def test_quality_report_to_dict() -> None:
    """Test QualityReport.to_dict() method."""
    report = QualityReport(Path("test.mid"))
    issue = QualityIssue("warning", "technical", "Test", {"detail": "value"})
    report.add_issue(issue)
    report.calculate_scores()

    result = report.to_dict()
    assert result["file"] == str(Path("test.mid"))
    assert result["overall_score"] >= 0.0
    assert "scores" in result
    assert len(result["issues"]) == 1
    assert result["issues"][0]["message"] == "Test"


def test_check_technical_quality(tmp_path: Path) -> None:
    """Test technical quality checking."""
    from pianist.analyze import analyze_midi

    # Create a minimal MIDI file
    midi_file = tmp_path / "test.mid"
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Piano", time=0))
    track.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_file)

    midi_analysis = analyze_midi(midi_file)
    report = QualityReport(midi_file)

    check_technical_quality(midi_analysis, report)

    # Should have some issues or at least run without error
    report.calculate_scores()
    assert report.overall_score >= 0.0


def test_check_structure_quality(tmp_path: Path) -> None:
    """Test structure quality checking."""
    from pianist.analyze import analyze_midi

    # Create a minimal MIDI file
    midi_file = tmp_path / "test.mid"
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Piano", time=0))
    track.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_file)

    midi_analysis = analyze_midi(midi_file)
    report = QualityReport(midi_file)

    check_structure_quality(midi_analysis, report)

    report.calculate_scores()
    assert report.overall_score >= 0.0


@pytest.mark.slow
def test_check_musical_quality(tmp_path: Path) -> None:
    """Test musical quality checking."""
    import mido

    from pianist.iterate import composition_from_midi

    # Create a minimal MIDI file
    midi_file = tmp_path / "test.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Piano", time=0))
    track.append(mido.Message("note_on", note=60, velocity=64, channel=0, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(midi_file)

    composition = composition_from_midi(midi_file)
    report = QualityReport(midi_file)

    check_musical_quality(composition, report)

    report.calculate_scores()
    assert report.overall_score >= 0.0


def test_score_calculation() -> None:
    """Test that scores are calculated correctly based on issues."""
    report = QualityReport(Path("test.mid"))

    # Add errors (should heavily penalize)
    report.add_issue(QualityIssue("error", "technical", "Error 1"))
    report.add_issue(QualityIssue("error", "technical", "Error 2"))
    report.add_issue(QualityIssue("warning", "musical", "Warning 1"))

    report.calculate_scores()

    # Technical score should be heavily penalized (2 errors * 0.3 = 0.6 reduction)
    assert report.scores["technical"] < 0.5
    # Musical score should be slightly penalized (1 warning * 0.05 = 0.05 reduction)
    assert report.scores["musical"] < 1.0
    # Structure score should be 1.0 (no issues)
    assert report.scores["structure"] == 1.0
    # Overall should be weighted average
    assert report.overall_score < 1.0
