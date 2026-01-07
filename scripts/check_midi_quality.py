#!/usr/bin/env python3
"""
Quality check tool for MIDI files before importing into reference database.

This script analyzes MIDI files for:
- Technical quality (timing, velocity, structure)
- Musical coherence (harmony, form, motifs)
- Common issues (missing notes, timing errors, etc.)
- Optional AI-based quality assessment

Usage:
    # Check single file
    python3 scripts/check_midi_quality.py file.mid

    # Check directory of files
    python3 scripts/check_midi_quality.py --dir references/ --verbose

    # Check with AI assessment
    python3 scripts/check_midi_quality.py file.mid --ai --provider gemini
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.analyze import analyze_midi
from pianist.iterate import composition_from_midi
from pianist.musical_analysis import analyze_composition, MUSIC21_AVAILABLE
from pianist.parser import parse_composition_from_text
from pianist.iterate import composition_to_canonical_json


class QualityIssue:
    """Represents a quality issue found in a MIDI file."""
    
    def __init__(
        self,
        severity: str,  # "error", "warning", "info"
        category: str,  # "technical", "musical", "structure"
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.severity = severity
        self.category = category
        self.message = message
        self.details = details or {}
    
    def __repr__(self) -> str:
        return f"QualityIssue({self.severity}, {self.category}, {self.message})"


class QualityReport:
    """Quality assessment report for a MIDI file."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.issues: list[QualityIssue] = []
        self.scores: dict[str, float] = {}  # Category scores (0-1)
        self.overall_score: float = 0.0
        self.summary: dict[str, Any] = {}
        self.ai_assessment: str | None = None
    
    def add_issue(self, issue: QualityIssue) -> None:
        """Add a quality issue."""
        self.issues.append(issue)
    
    def calculate_scores(self) -> None:
        """
        Calculate quality scores based on issues.
        
        Scoring system:
        - Technical score: Starts at 1.0, -0.3 per error, -0.1 per warning
        - Musical score: Starts at 1.0, -0.2 per error, -0.05 per warning
        - Structure score: Starts at 1.0, -0.25 per error, -0.1 per warning
        - Overall score: Weighted average (40% technical, 40% musical, 20% structure)
        
        Note: "info" severity issues don't affect scores - they're informational only.
        """
        # Technical score (penalize errors and warnings)
        technical_errors = sum(1 for i in self.issues if i.category == "technical" and i.severity == "error")
        technical_warnings = sum(1 for i in self.issues if i.category == "technical" and i.severity == "warning")
        technical_score = max(0.0, 1.0 - (technical_errors * 0.3) - (technical_warnings * 0.1))
        
        # Musical score
        musical_errors = sum(1 for i in self.issues if i.category == "musical" and i.severity == "error")
        musical_warnings = sum(1 for i in self.issues if i.category == "musical" and i.severity == "warning")
        musical_score = max(0.0, 1.0 - (musical_errors * 0.2) - (musical_warnings * 0.05))
        
        # Structure score
        structure_errors = sum(1 for i in self.issues if i.category == "structure" and i.severity == "error")
        structure_warnings = sum(1 for i in self.issues if i.category == "structure" and i.severity == "warning")
        structure_score = max(0.0, 1.0 - (structure_errors * 0.25) - (structure_warnings * 0.1))
        
        self.scores = {
            "technical": technical_score,
            "musical": musical_score,
            "structure": structure_score,
        }
        
        # Overall score (weighted average)
        self.overall_score = (
            technical_score * 0.4 +
            musical_score * 0.4 +
            structure_score * 0.2
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "file": str(self.file_path),
            "overall_score": round(self.overall_score, 3),
            "scores": {k: round(v, 3) for k, v in self.scores.items()},
            "issue_count": len(self.issues),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "details": i.details,
                }
                for i in self.issues
            ],
            "summary": self.summary,
            "ai_assessment": self.ai_assessment,
        }


def check_technical_quality(midi_analysis: Any, report: QualityReport) -> None:
    """Check technical quality of MIDI file."""
    # Check for very short or very long files
    duration = midi_analysis.duration_beats
    if duration < 4:
        report.add_issue(QualityIssue(
            "warning",
            "technical",
            f"Very short file ({duration:.1f} beats)",
            {"duration_beats": duration}
        ))
    elif duration > 2000:
        report.add_issue(QualityIssue(
            "info",
            "technical",
            f"Very long file ({duration:.1f} beats)",
            {"duration_beats": duration}
        ))
    
    # Check for tracks
    if not midi_analysis.tracks:
        report.add_issue(QualityIssue(
            "error",
            "technical",
            "No tracks found in MIDI file",
        ))
        return
    
    # Check each track
    for track in midi_analysis.tracks:
        # Check note count
        if track.note_count == 0:
            report.add_issue(QualityIssue(
                "error",
                "technical",
                f"Track '{track.name}' has no notes",
                {"track": track.name, "channel": track.channel}
            ))
        
        # Check for reasonable note density
        if track.note_density_per_bar is not None:
            if track.note_density_per_bar < 0.5:
                report.add_issue(QualityIssue(
                    "warning",
                    "technical",
                    f"Very low note density ({track.note_density_per_bar:.1f} notes/bar)",
                    {"track": track.name, "density": track.note_density_per_bar}
                ))
            elif track.note_density_per_bar > 50:
                report.add_issue(QualityIssue(
                    "warning",
                    "technical",
                    f"Very high note density ({track.note_density_per_bar:.1f} notes/bar)",
                    {"track": track.name, "density": track.note_density_per_bar}
                ))
        
        # Check velocity distribution
        if track.velocity.median is not None:
            if track.velocity.median < 20:
                report.add_issue(QualityIssue(
                    "warning",
                    "technical",
                    f"Very quiet track (median velocity: {track.velocity.median:.0f})",
                    {"track": track.name, "median_velocity": track.velocity.median}
                ))
            elif track.velocity.median > 120:
                report.add_issue(QualityIssue(
                    "info",
                    "technical",
                    f"Very loud track (median velocity: {track.velocity.median:.0f})",
                    {"track": track.name, "median_velocity": track.velocity.median}
                ))
        
        # Check pitch range
        if track.pitch_min is not None and track.pitch_max is not None:
            pitch_range = track.pitch_max - track.pitch_min
            if pitch_range < 12:  # Less than an octave
                report.add_issue(QualityIssue(
                    "warning",
                    "technical",
                    f"Very narrow pitch range ({pitch_range} semitones)",
                    {"track": track.name, "min": track.pitch_min, "max": track.pitch_max}
                ))
            elif pitch_range > 60:  # More than 5 octaves
                report.add_issue(QualityIssue(
                    "info",
                    "technical",
                    f"Very wide pitch range ({pitch_range} semitones)",
                    {"track": track.name, "min": track.pitch_min, "max": track.pitch_max}
                ))
    
    # Check tempo consistency
    if len(midi_analysis.tempo) > 5:
        report.add_issue(QualityIssue(
            "info",
            "technical",
            f"Many tempo changes ({len(midi_analysis.tempo)})",
            {"tempo_changes": len(midi_analysis.tempo)}
        ))
    
    # Check time signature consistency
    if len(midi_analysis.time_signature) > 1:
        report.add_issue(QualityIssue(
            "info",
            "technical",
            f"Multiple time signatures ({len(midi_analysis.time_signature)})",
            {"time_signatures": len(midi_analysis.time_signature)}
        ))


def check_musical_quality(composition: Any, report: QualityReport) -> None:
    """Check musical quality using analysis."""
    if not MUSIC21_AVAILABLE:
        report.add_issue(QualityIssue(
            "warning",
            "musical",
            "music21 not available - skipping musical analysis",
        ))
        return
    
    try:
        analysis = analyze_composition(composition)
        
        # Check for motifs
        if not analysis.motifs:
            report.add_issue(QualityIssue(
                "warning",
                "musical",
                "No motifs detected",
            ))
        elif len(analysis.motifs) < 2:
            report.add_issue(QualityIssue(
                "info",
                "musical",
                f"Only {len(analysis.motifs)} motif(s) detected",
                {"motif_count": len(analysis.motifs)}
            ))
        else:
            report.summary["motifs"] = len(analysis.motifs)
        
        # Check for phrases
        if not analysis.phrases:
            report.add_issue(QualityIssue(
                "warning",
                "musical",
                "No phrases detected",
            ))
        else:
            report.summary["phrases"] = len(analysis.phrases)
        
        # Check harmony
        if analysis.harmonic_progression:
            chords = analysis.harmonic_progression.chords
            if not chords:
                report.add_issue(QualityIssue(
                    "warning",
                    "musical",
                    "No chords detected in harmonic analysis",
                ))
            else:
                report.summary["chords"] = len(chords)
                
                # Check for key
                if analysis.harmonic_progression.key:
                    report.summary["key"] = analysis.harmonic_progression.key
                else:
                    report.add_issue(QualityIssue(
                        "info",
                        "musical",
                        "Key not detected in harmonic analysis",
                    ))
        else:
            report.add_issue(QualityIssue(
                "warning",
                "musical",
                "Harmonic analysis failed or returned no results",
            ))
        
        # Check form
        if analysis.form:
            report.summary["form"] = analysis.form
        else:
            report.add_issue(QualityIssue(
                "info",
                "musical",
                "Form not detected",
            ))
        
    except Exception as e:
        report.add_issue(QualityIssue(
            "error",
            "musical",
            f"Musical analysis failed: {e}",
            {"error": str(e)}
        ))


def check_structure_quality(midi_analysis: Any, report: QualityReport) -> None:
    """Check structural quality."""
    # Check for reasonable bar count
    bars = midi_analysis.estimated_bar_count
    if bars < 1:
        report.add_issue(QualityIssue(
            "error",
            "structure",
            "File is too short (< 1 bar)",
            {"bars": bars}
        ))
    elif bars < 4:
        report.add_issue(QualityIssue(
            "warning",
            "structure",
            f"Very short file ({bars:.1f} bars)",
            {"bars": bars}
        ))
    
    # Check for multiple tracks (could indicate multi-instrument, which is fine)
    if len(midi_analysis.tracks) > 1:
        report.add_issue(QualityIssue(
            "info",
            "structure",
            f"Multiple tracks ({len(midi_analysis.tracks)}) - may need to extract piano track",
            {"track_count": len(midi_analysis.tracks)}
        ))


def get_ai_assessment(
    composition: Any,
    report: QualityReport,
    provider: str = "gemini",
    model: str | None = None,
) -> None:
    """Get AI assessment of musical quality."""
    try:
        from pianist.ai_providers import generate_text_unified, GeminiError, OllamaError, OpenRouterError
        
        # Set default model if not provided
        if model is None:
            if provider == "gemini":
                model = "gemini-flash-latest"
            elif provider == "openrouter":
                model = "openai/gpt-4o"
            else:  # ollama
                model = "gpt-oss:20b"
        
        comp_json = composition_to_canonical_json(composition)
        
        prompt = f"""You are a music expert evaluating a MIDI file for quality and suitability as a reference example.

The composition JSON is:
{comp_json[:2000]}...

Quality issues found so far:
- Technical: {len([i for i in report.issues if i.category == "technical"])} issues
- Musical: {len([i for i in report.issues if i.category == "musical"])} issues
- Structure: {len([i for i in report.issues if i.category == "structure"])} issues

Please provide a brief assessment (2-3 sentences) of:
1. Overall musical quality and coherence
2. Whether this would be a good reference example
3. Any notable strengths or weaknesses

Be concise and specific."""
        
        response = generate_text_unified(provider=provider, model=model, prompt=prompt, verbose=False)
        report.ai_assessment = response.strip()
        
    except (GeminiError, OllamaError, OpenRouterError) as e:
        report.add_issue(QualityIssue(
            "warning",
            "technical",
            f"AI assessment failed: {e}",
            {"error": str(e)}
        ))
    except Exception as e:
        report.add_issue(QualityIssue(
            "warning",
            "technical",
            f"AI assessment failed: {e}",
            {"error": str(e)}
        ))


def check_midi_file(
    file_path: Path,
    use_ai: bool = False,
    provider: str = "gemini",
    model: str | None = None,
) -> QualityReport:
    """Check quality of a single MIDI file."""
    report = QualityReport(file_path)
    
    try:
        # Basic MIDI analysis
        midi_analysis = analyze_midi(file_path)
        report.summary["duration_beats"] = midi_analysis.duration_beats
        report.summary["duration_seconds"] = midi_analysis.duration_seconds
        report.summary["tracks"] = len(midi_analysis.tracks)
        
        # Add tempo information
        if midi_analysis.tempo:
            initial_tempo = midi_analysis.tempo[0].bpm
            report.summary["initial_tempo_bpm"] = round(initial_tempo, 1)
            if len(midi_analysis.tempo) > 1:
                report.summary["tempo_changes"] = len(midi_analysis.tempo) - 1
        
        # Technical checks
        check_technical_quality(midi_analysis, report)
        
        # Structure checks
        check_structure_quality(midi_analysis, report)
        
        # Convert to composition for musical analysis
        try:
            composition = composition_from_midi(file_path)
            check_musical_quality(composition, report)
            
            # AI assessment if requested
            if use_ai:
                get_ai_assessment(composition, report, provider, model)
        except Exception as e:
            report.add_issue(QualityIssue(
                "error",
                "technical",
                f"Failed to convert MIDI to composition: {e}",
                {"error": str(e)}
            ))
        
        # Calculate scores
        report.calculate_scores()
        
    except Exception as e:
        report.add_issue(QualityIssue(
            "error",
            "technical",
            f"Failed to analyze MIDI file: {e}",
            {"error": str(e)}
        ))
        report.calculate_scores()
    
    return report


def print_report(report: QualityReport, verbose: bool = False) -> None:
    """Print quality report to console."""
    print(f"\n{'='*60}")
    print(f"Quality Check: {report.file_path.name}")
    print(f"{'='*60}")
    
    # Overall score
    score_emoji = "✅" if report.overall_score >= 0.8 else "⚠️" if report.overall_score >= 0.6 else "❌"
    print(f"\n{score_emoji} Overall Score: {report.overall_score:.2%}")
    print(f"   Technical: {report.scores.get('technical', 0):.2%}")
    print(f"   Musical:   {report.scores.get('musical', 0):.2%}")
    print(f"   Structure: {report.scores.get('structure', 0):.2%}")
    
    # Summary
    if report.summary:
        print(f"\nSummary:")
        for key, value in report.summary.items():
            print(f"  {key}: {value}")
    
    # Issues
    if report.issues:
        print(f"\nIssues Found ({len(report.issues)}):")
        for issue in report.issues:
            severity_emoji = {
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
            }.get(issue.severity, "•")
            print(f"  {severity_emoji} [{issue.category}] {issue.message}")
            if verbose and issue.details:
                for key, value in issue.details.items():
                    print(f"      {key}: {value}")
    else:
        print(f"\n✅ No issues found!")
    
    # AI assessment
    if report.ai_assessment:
        print(f"\n🤖 AI Assessment:")
        print(f"  {report.ai_assessment}")
    
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check quality of MIDI files before importing to reference database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "file",
        type=Path,
        nargs="?",
        help="MIDI file to check",
    )
    input_group.add_argument(
        "--dir",
        type=Path,
        help="Directory containing MIDI files to check",
    )
    
    # Options
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.mid",
        help="Glob pattern for files in directory (default: *.mid)",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Use AI to assess musical quality",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="gemini",
        choices=["gemini", "ollama", "openrouter"],
        help="AI provider for assessment: 'gemini' (cloud), 'ollama' (local), or 'openrouter' (cloud). Default: gemini",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name. Default: gemini-flash-latest (Gemini), gpt-oss:20b (Ollama), or openai/gpt-4o (OpenRouter)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed information",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Output results as JSON to file",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum overall score to pass (0-1, default: 0.0)",
    )
    
    args = parser.parse_args()
    
    # Find files
    files: list[Path] = []
    if args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1
        files = [args.file]
    elif args.dir:
        if not args.dir.is_dir():
            print(f"Error: Not a directory: {args.dir}", file=sys.stderr)
            return 1
        files = list(args.dir.glob(args.pattern)) + list(args.dir.glob("*.midi"))
        if not files:
            print(f"Error: No MIDI files found in {args.dir}", file=sys.stderr)
            return 1
    
    # Check files
    reports: list[QualityReport] = []
    for file_path in sorted(files):
        if args.verbose:
            print(f"Checking: {file_path.name}...")
        report = check_midi_file(file_path, args.ai, args.provider, args.model)
        reports.append(report)
        print_report(report, args.verbose)
    
    # Summary
    if len(reports) > 1:
        print(f"\n{'='*60}")
        print(f"Summary: {len(reports)} files checked")
        print(f"{'='*60}")
        
        passed = [r for r in reports if r.overall_score >= args.min_score]
        failed = [r for r in reports if r.overall_score < args.min_score]
        
        print(f"✅ Passed (score >= {args.min_score:.0%}): {len(passed)}")
        print(f"❌ Failed (score < {args.min_score:.0%}): {len(failed)}")
        
        if passed:
            avg_score = sum(r.overall_score for r in passed) / len(passed)
            print(f"\nAverage score (passed): {avg_score:.2%}")
        
        if failed:
            print(f"\nFailed files:")
            for r in failed:
                print(f"  {r.file_path.name}: {r.overall_score:.2%}")
    
    # JSON output
    if args.json:
        output = {
            "files_checked": len(reports),
            "reports": [r.to_dict() for r in reports],
        }
        args.json.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults saved to: {args.json}")
    
    # Return code
    failed_count = sum(1 for r in reports if r.overall_score < args.min_score)
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

