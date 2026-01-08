"""
Comprehensive analysis module for user-focused composition analysis.

This module provides shared analysis functions used by both:
- CLI `analyze` command (user-focused analysis)
- Batch review scripts (database curation analysis)

The user-focused analysis includes:
- Quality assessment (technical, musical, structure scores)
- Musical analysis (motifs, phrases, harmony, form)
- Improvement suggestions (actionable advice)
- Technical metadata

It does NOT include:
- Duplicate detection (not relevant for user's own work)
- Suggested names/IDs (unless AI naming is requested)
- Suitability for database (not curating)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyze import analyze_midi
from .iterate import composition_from_midi
from .musical_analysis import MUSIC21_AVAILABLE, analyze_composition
from .parser import parse_composition_from_text

# Import quality checking functions
import importlib.util
import sys

# Import check_midi_quality module
check_midi_quality_path = Path(__file__).parent.parent.parent / "scripts" / "check_midi_quality.py"
spec = importlib.util.spec_from_file_location("check_midi_quality", check_midi_quality_path)
check_midi_quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_midi_quality)
check_midi_file = check_midi_quality.check_midi_file
QualityReport = check_midi_quality.QualityReport
QualityIssue = check_midi_quality.QualityIssue


def extract_technical_metadata(midi_analysis: Any) -> dict[str, Any]:
    """
    Extract technical metadata from MIDI analysis.
    
    Returns:
        Dictionary with technical metadata (duration, tempo, time/key signatures, tracks)
    """
    # Get initial tempo
    tempo_bpm = None
    if midi_analysis.tempo:
        tempo_bpm = midi_analysis.tempo[0].bpm
    
    # Get time signature
    time_signature = None
    if midi_analysis.time_signature:
        ts = midi_analysis.time_signature[0]
        time_signature = f"{ts.numerator}/{ts.denominator}"
    
    # Get key signature
    key_signature = None
    if midi_analysis.key_signature:
        key_signature = midi_analysis.key_signature[0].key
    
    # Calculate bars
    bars = midi_analysis.estimated_bar_count
    
    return {
        "duration_beats": midi_analysis.duration_beats,
        "duration_seconds": midi_analysis.duration_seconds,
        "bars": bars,
        "tempo_bpm": tempo_bpm,
        "time_signature": time_signature,
        "key_signature": key_signature,
        "tracks": len(midi_analysis.tracks),
    }


def generate_improvement_suggestions(quality_report: QualityReport, musical_analysis: Any | None) -> dict[str, Any]:
    """
    Generate improvement suggestions from quality issues and musical analysis.
    
    Returns:
        Dictionary with issues_to_fix, improvements, and quality_recommendations
    """
    issues_to_fix: list[dict[str, Any]] = []
    improvements: list[str] = []
    quality_recommendations: list[str] = []
    
    # Convert quality issues to improvement suggestions
    for issue in quality_report.issues:
        # Skip info-level issues (they're informational, not actionable)
        if issue.severity == "info":
            continue
        
        # Create suggestion based on issue
        suggestion = None
        if "pedal" in issue.message.lower() and "duration=0" in issue.message.lower():
            suggestion = "Review pedal timing - some events may be incorrectly encoded"
        elif "velocity" in issue.message.lower():
            if "sparse" in issue.message.lower() or "low" in issue.message.lower():
                suggestion = "Add more dynamic contrast for musical expression"
            elif "high" in issue.message.lower():
                suggestion = "Consider reducing velocity for better dynamic range"
        elif "note density" in issue.message.lower():
            if "low" in issue.message.lower():
                suggestion = "Consider adding more musical material to enrich the texture"
            elif "high" in issue.message.lower():
                suggestion = "Consider simplifying texture for clarity"
        elif "pitch range" in issue.message.lower():
            if "narrow" in issue.message.lower():
                suggestion = "Consider expanding pitch range for more musical interest"
        elif "motif" in issue.message.lower():
            suggestion = "Consider developing motifs with variations and sequences"
        elif "phrase" in issue.message.lower():
            suggestion = "Consider adding more phrase structure for musical coherence"
        elif "harmony" in issue.message.lower() or "chord" in issue.message.lower():
            suggestion = "Review harmonic progression for coherence and variety"
        elif "form" in issue.message.lower():
            suggestion = "Consider adding clearer form structure (binary, ternary, etc.)"
        elif "short" in issue.message.lower() or "length" in issue.message.lower():
            suggestion = "Consider expanding the composition for more development"
        elif "track" in issue.message.lower() and "no notes" in issue.message.lower():
            suggestion = "Remove or fix empty tracks"
        else:
            # Generic suggestion
            suggestion = f"Review and address: {issue.message}"
        
        if suggestion:
            issues_to_fix.append({
                "issue": issue.message,
                "severity": issue.severity,
                "category": issue.category,
                "suggestion": suggestion,
            })
    
    # Generate musical improvements based on analysis
    if musical_analysis:
        if not musical_analysis.motifs or len(musical_analysis.motifs) < 2:
            improvements.append("Consider adding more recurring motifs for structural coherence")
        
        if not musical_analysis.phrases or len(musical_analysis.phrases) < 2:
            improvements.append("Consider adding more phrase structure for musical flow")
        
        if musical_analysis.harmonic_progression:
            chords = musical_analysis.harmonic_progression.chords
            if len(chords) < 4:
                improvements.append("Consider adding more harmonic variety")
            elif len(chords) > 50:
                improvements.append("Consider simplifying harmonic progression for clarity")
        
        if not musical_analysis.form:
            improvements.append("Consider adding clearer form structure (binary, ternary, etc.)")
    
    # Generate quality recommendations based on scores
    overall_score = quality_report.overall_score
    technical_score = quality_report.scores.get("technical", 0.0)
    musical_score = quality_report.scores.get("musical", 0.0)
    structure_score = quality_report.scores.get("structure", 0.0)
    
    if overall_score >= 0.9:
        quality_recommendations.append("Overall quality is excellent - composition is well-structured and polished")
    elif overall_score >= 0.7:
        quality_recommendations.append("Overall quality is good - composition is well-structured")
    elif overall_score >= 0.5:
        quality_recommendations.append("Overall quality is acceptable - some improvements would enhance the composition")
    else:
        quality_recommendations.append("Overall quality needs improvement - address technical and musical issues")
    
    if technical_score >= 0.9:
        quality_recommendations.append("Technical execution is excellent")
    elif technical_score < 0.7:
        quality_recommendations.append("Technical execution needs improvement - review MIDI encoding and structure")
    
    if musical_score >= 0.9:
        quality_recommendations.append("Musical coherence is excellent")
    elif musical_score < 0.7:
        quality_recommendations.append("Musical coherence needs improvement - review harmony, motifs, and form")
    
    if structure_score >= 0.9:
        quality_recommendations.append("Structural organization is excellent")
    elif structure_score < 0.7:
        quality_recommendations.append("Structural organization needs improvement - review form and balance")
    
    return {
        "issues_to_fix": issues_to_fix,
        "improvements": improvements,
        "quality_recommendations": quality_recommendations,
    }


def analyze_for_user(
    file_path: Path,
    use_ai_insights: bool = False,
    ai_provider: str = "gemini",
    ai_model: str | None = None,
    composition: Any | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Perform user-focused comprehensive analysis of a MIDI or JSON file.
    
    This function provides:
    - Quality assessment (technical, musical, structure scores)
    - Musical analysis (motifs, phrases, harmony, form)
    - Improvement suggestions (actionable advice)
    - Technical metadata
    
    It does NOT include:
    - Duplicate detection
    - Suggested names/IDs (unless use_ai_insights=True)
    - Suitability for database
    
    Args:
        file_path: Path to MIDI (.mid/.midi) or JSON (.json) file
        use_ai_insights: If True, include AI-generated name, style, and description
        ai_provider: AI provider for insights ("gemini", "ollama", "openrouter")
        ai_model: Model name (defaults based on provider)
    
    Returns:
        Dictionary with comprehensive analysis results
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    # Initialize result structure
    result: dict[str, Any] = {
        "filename": file_path.name,
        "filepath": str(file_path),
        "quality": {},
        "technical": {},
        "musical_analysis": {},
        "improvement_suggestions": {},
    }
    
    # Handle MIDI files
    if suffix in (".mid", ".midi"):
        # Basic MIDI analysis
        midi_analysis = analyze_midi(file_path)
        
        # Extract technical metadata
        result["technical"] = extract_technical_metadata(midi_analysis)
        
        # Quality check
        quality_report = check_midi_file(file_path, use_ai=False)
        
        # Quality scores
        result["quality"] = {
            "overall_score": round(quality_report.overall_score, 3),
            "technical_score": round(quality_report.scores.get("technical", 0.0), 3),
            "musical_score": round(quality_report.scores.get("musical", 0.0), 3),
            "structure_score": round(quality_report.scores.get("structure", 0.0), 3),
            "issues": [issue.message for issue in quality_report.issues if issue.severity != "info"],
        }
        
        # Musical analysis (if music21 is available)
        musical_analysis = None
        music21_stream = None
        if MUSIC21_AVAILABLE:
            try:
                import time
                import time
                # Use provided composition if available, otherwise load it
                if composition is None:
                    load_start = time.time()
                    composition = composition_from_midi(file_path)
                    load_time = time.time() - load_start
                    if verbose:
                        print(f"  [Timing] Load MIDI: {load_time:.2f}s", file=sys.stderr)
                else:
                    load_time = 0.0
                
                # Convert to music21 stream once and reuse (major performance improvement)
                from .musical_analysis import _composition_to_music21_stream
                stream_start = time.time()
                music21_stream = _composition_to_music21_stream(composition)
                stream_time = time.time() - stream_start
                if verbose:
                    print(f"  [Timing] Convert to music21 stream: {stream_time:.2f}s", file=sys.stderr)
                
                # Pass stream to avoid re-conversion in each analysis function
                analysis_start = time.time()
                musical_analysis = analyze_composition(composition, music21_stream=music21_stream, verbose=verbose)
                analysis_time = time.time() - analysis_start
                if verbose:
                    print(f"  [Timing] Musical analysis (motifs/phrases/harmony/form): {analysis_time:.2f}s", file=sys.stderr)
                
                # Format musical analysis
                result["musical_analysis"] = {
                    "detected_key": musical_analysis.harmonic_progression.key if musical_analysis.harmonic_progression else None,
                    "detected_form": musical_analysis.form,
                    "motif_count": len(musical_analysis.motifs),
                    "phrase_count": len(musical_analysis.phrases),
                    "chord_count": len(musical_analysis.harmonic_progression.chords) if musical_analysis.harmonic_progression else 0,
                    "harmonic_progression": " ".join(musical_analysis.harmonic_progression.progression[:10]) if musical_analysis.harmonic_progression and musical_analysis.harmonic_progression.progression else None,
                    "motifs": [
                        {
                            "start": m.start,
                            "duration": m.duration,
                            "pitches": m.pitches,
                            "description": m.description,
                        }
                        for m in musical_analysis.motifs
                    ],
                    "phrases": [
                        {
                            "start": p.start,
                            "duration": p.duration,
                            "description": p.description,
                        }
                        for p in musical_analysis.phrases
                    ],
                    "harmony": {
                        "chords": [
                            {
                                "start": c.start,
                                "pitches": c.pitches,
                                "name": c.name,
                                "roman_numeral": c.roman_numeral,
                                "function": c.function,
                                "inversion": c.inversion,
                                "is_cadence": c.is_cadence,
                                "cadence_type": c.cadence_type,
                            }
                            for c in musical_analysis.harmonic_progression.chords[:20]  # Limit to first 20 chords
                        ] if musical_analysis.harmonic_progression else [],
                        "key": musical_analysis.harmonic_progression.key if musical_analysis.harmonic_progression else None,
                        "roman_numerals": musical_analysis.harmonic_progression.roman_numerals if musical_analysis.harmonic_progression else None,
                        "progression": musical_analysis.harmonic_progression.progression if musical_analysis.harmonic_progression else None,
                        "cadences": musical_analysis.harmonic_progression.cadences if musical_analysis.harmonic_progression else None,
                    } if musical_analysis.harmonic_progression else None,
                }
            except Exception:
                # Musical analysis failed, continue without it
                pass
        
        # Generate improvement suggestions
        result["improvement_suggestions"] = generate_improvement_suggestions(quality_report, musical_analysis)
        
        # AI insights (optional)
        if use_ai_insights and MUSIC21_AVAILABLE:
            try:
                from .iterate import composition_to_canonical_json
                from .ai_providers import generate_text_unified, GeminiError, OllamaError
                
                # Set default model if not provided
                if ai_model is None:
                    if ai_provider == "gemini":
                        ai_model = "gemini-flash-latest"
                    elif ai_provider == "openrouter":
                        # Default to a free OpenRouter model (recommended: mistralai/devstral-2512:free)
                        # Other free options: xiaomi/mimo-v2-flash:free, tngtech/deepseek-r1t2-chimera:free, nex-agi/deepseek-v3.1-nex-n1:free
                        ai_model = "mistralai/devstral-2512:free"
                    else:  # ollama
                        ai_model = "gpt-oss:20b"
                
                # Get composition for AI analysis (reuse if already loaded)
                if composition is None:
                    composition = composition_from_midi(file_path)
                
                comp_json = composition_to_canonical_json(composition)
                
                # Extract key info for prompt
                detected_key = result["musical_analysis"].get("detected_key") or result["technical"].get("key_signature") or "Unknown"
                detected_form = result["musical_analysis"].get("detected_form") or "Unknown"
                tempo_bpm = result["technical"].get("tempo_bpm") or "Unknown"
                duration_beats = result["technical"].get("duration_beats", 0)
                bars = result["technical"].get("bars", 0)
                motif_count = result["musical_analysis"].get("motif_count", 0)
                phrase_count = result["musical_analysis"].get("phrase_count", 0)
                
                prompt = f"""You are a musicologist analyzing a piano composition.

Filename: {file_path.name}
Key: {detected_key}
Form: {detected_form}
Time Signature: {result['technical'].get('time_signature', 'Unknown')}
Tempo: {tempo_bpm} BPM
Duration: {duration_beats:.1f} beats (~{bars:.1f} bars)
Motifs: {motif_count}
Phrases: {phrase_count}

Musical content (first 2000 characters):
{comp_json[:2000]}

Provide a brief analysis. Respond with JSON:
{{
  "suggested_name": "Descriptive title based on musical characteristics",
  "suggested_style": "Baroque|Classical|Romantic|Modern|Other",
  "suggested_description": "Brief description of the piece's musical characteristics, style, and mood"
}}

Respond ONLY with valid JSON, no other text."""
                
                response = generate_text_unified(
                    provider=ai_provider,
                    model=ai_model,
                    prompt=prompt,
                    verbose=False
                )
                
                # Parse JSON from response
                import json
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                if json_match:
                    try:
                        ai_data = json.loads(json_match.group())
                        result["ai_insights"] = {
                            "suggested_name": ai_data.get("suggested_name", "Unknown"),
                            "suggested_style": ai_data.get("suggested_style", "Unknown"),
                            "suggested_description": ai_data.get("suggested_description", "No description available"),
                        }
                    except json.JSONDecodeError:
                        # Failed to parse, skip AI insights
                        pass
            except (GeminiError, OllamaError, Exception):
                # AI insights failed, continue without them
                pass
    
    # Handle JSON files
    elif suffix == ".json":
        if not MUSIC21_AVAILABLE:
            raise ImportError(
                "music21 is required for JSON analysis. Install with: pip install music21"
            )
        
        # Load composition from JSON
        # Read text directly to avoid circular import with cli.util
        try:
            text = file_path.read_text(encoding="utf-8")
            if not text.strip():
                raise ValueError(f"Input file is empty: {file_path}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Input file not found: {file_path}") from e
        except PermissionError as e:
            raise PermissionError(f"Input file not readable: {file_path}") from e
        
        from .parser import parse_composition_from_text
        composition = parse_composition_from_text(text)
        
        # Extract technical metadata from composition
        result["technical"] = {
            "duration_beats": None,  # Not directly available from JSON
            "duration_seconds": None,
            "bars": None,
            "tempo_bpm": composition.bpm,
            "time_signature": f"{composition.time_signature.numerator}/{composition.time_signature.denominator}",
            "key_signature": composition.key_signature,
            "tracks": len(composition.tracks),
        }
        
        # Musical analysis (convert to music21 stream once and reuse)
        from .musical_analysis import _composition_to_music21_stream
        music21_stream = _composition_to_music21_stream(composition)
        musical_analysis = analyze_composition(composition, music21_stream=music21_stream)
        
        # Format musical analysis
        result["musical_analysis"] = {
            "detected_key": musical_analysis.harmonic_progression.key if musical_analysis.harmonic_progression else None,
            "detected_form": musical_analysis.form,
            "motif_count": len(musical_analysis.motifs),
            "phrase_count": len(musical_analysis.phrases),
            "chord_count": len(musical_analysis.harmonic_progression.chords) if musical_analysis.harmonic_progression else 0,
            "harmonic_progression": " ".join(musical_analysis.harmonic_progression.progression[:10]) if musical_analysis.harmonic_progression and musical_analysis.harmonic_progression.progression else None,
            "motifs": [
                {
                    "start": m.start,
                    "duration": m.duration,
                    "pitches": m.pitches,
                    "description": m.description,
                }
                for m in musical_analysis.motifs
            ],
            "phrases": [
                {
                    "start": p.start,
                    "duration": p.duration,
                    "description": p.description,
                }
                for p in musical_analysis.phrases
            ],
            "harmony": {
                "chords": [
                    {
                        "start": c.start,
                        "pitches": c.pitches,
                        "name": c.name,
                        "roman_numeral": c.roman_numeral,
                        "function": c.function,
                        "inversion": c.inversion,
                        "is_cadence": c.is_cadence,
                        "cadence_type": c.cadence_type,
                    }
                    for c in musical_analysis.harmonic_progression.chords[:20]  # Limit to first 20 chords
                ] if musical_analysis.harmonic_progression else [],
                "key": musical_analysis.harmonic_progression.key if musical_analysis.harmonic_progression else None,
                "roman_numerals": musical_analysis.harmonic_progression.roman_numerals if musical_analysis.harmonic_progression else None,
                "progression": musical_analysis.harmonic_progression.progression if musical_analysis.harmonic_progression else None,
                "cadences": musical_analysis.harmonic_progression.cadences if musical_analysis.harmonic_progression else None,
            } if musical_analysis.harmonic_progression else None,
        }
        
        # For JSON files, we can't do full quality checking (no MIDI file)
        # But we can still provide basic quality assessment based on musical analysis
        quality_score = 0.8  # Default for JSON files
        if not musical_analysis.motifs:
            quality_score -= 0.1
        if not musical_analysis.phrases:
            quality_score -= 0.1
        if not musical_analysis.harmonic_progression or not musical_analysis.harmonic_progression.chords:
            quality_score -= 0.1
        if not musical_analysis.form:
            quality_score -= 0.05
        
        result["quality"] = {
            "overall_score": round(max(0.0, quality_score), 3),
            "technical_score": 0.9,  # JSON files are typically well-structured
            "musical_score": round(max(0.0, quality_score - 0.1), 3),
            "structure_score": round(max(0.0, quality_score - 0.05), 3),
            "issues": [],  # No specific issues for JSON files
        }
        
        # Generate improvement suggestions
        # Create a minimal quality report for JSON files
        quality_report = QualityReport(file_path)
        result["improvement_suggestions"] = generate_improvement_suggestions(quality_report, musical_analysis)
        
        # AI insights (optional)
        if use_ai_insights:
            try:
                from .iterate import composition_to_canonical_json
                from .ai_providers import generate_text_unified, GeminiError, OllamaError
                
                # Set default model if not provided
                if ai_model is None:
                    if ai_provider == "gemini":
                        ai_model = "gemini-flash-latest"
                    elif ai_provider == "openrouter":
                        # Default to a free OpenRouter model (recommended: mistralai/devstral-2512:free)
                        # Other free options: xiaomi/mimo-v2-flash:free, tngtech/deepseek-r1t2-chimera:free, nex-agi/deepseek-v3.1-nex-n1:free
                        ai_model = "mistralai/devstral-2512:free"
                    else:  # ollama
                        ai_model = "gpt-oss:20b"
                
                comp_json = composition_to_canonical_json(composition)
                
                # Extract key info for prompt
                detected_key = result["musical_analysis"].get("detected_key") or result["technical"].get("key_signature") or "Unknown"
                detected_form = result["musical_analysis"].get("detected_form") or "Unknown"
                tempo_bpm = result["technical"].get("tempo_bpm") or "Unknown"
                motif_count = result["musical_analysis"].get("motif_count", 0)
                phrase_count = result["musical_analysis"].get("phrase_count", 0)
                
                prompt = f"""You are a musicologist analyzing a piano composition.

Filename: {file_path.name}
Key: {detected_key}
Form: {detected_form}
Time Signature: {result['technical'].get('time_signature', 'Unknown')}
Tempo: {tempo_bpm} BPM
Motifs: {motif_count}
Phrases: {phrase_count}

Musical content (first 2000 characters):
{comp_json[:2000]}

Provide a brief analysis. Respond with JSON:
{{
  "suggested_name": "Descriptive title based on musical characteristics",
  "suggested_style": "Baroque|Classical|Romantic|Modern|Other",
  "suggested_description": "Brief description of the piece's musical characteristics, style, and mood"
}}

Respond ONLY with valid JSON, no other text."""
                
                response = generate_text_unified(
                    provider=ai_provider,
                    model=ai_model,
                    prompt=prompt,
                    verbose=False
                )
                
                # Parse JSON from response
                import json
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                if json_match:
                    try:
                        ai_data = json.loads(json_match.group())
                        result["ai_insights"] = {
                            "suggested_name": ai_data.get("suggested_name", "Unknown"),
                            "suggested_style": ai_data.get("suggested_style", "Unknown"),
                            "suggested_description": ai_data.get("suggested_description", "No description available"),
                        }
                    except json.JSONDecodeError:
                        # Failed to parse, skip AI insights
                        pass
            except (GeminiError, OllamaError, Exception):
                # AI insights failed, continue without them
                pass
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Expected .mid, .midi, or .json")
    
    return result

