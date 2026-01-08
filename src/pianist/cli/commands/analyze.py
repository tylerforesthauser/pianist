"""Analyze command: Analyze MIDI or JSON files."""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

from ..util import (
    derive_base_name_from_path,
    derive_raw_path,
    get_output_base_dir,
    prompt_from_template,
    read_text,
    resolve_output_path,
    write_text,
)
from ...ai_providers import GeminiError, OllamaError, OpenRouterError, generate_text_unified
from ...analyze import analyze_midi, analysis_prompt_template
from ...comprehensive_analysis import analyze_for_user
from ...iterate import composition_to_canonical_json
from ...musical_analysis import MUSIC21_AVAILABLE, analyze_composition as analyze_composition_musical
from ...output_util import write_output_with_sidecar
from ...parser import parse_composition_from_text
from ...renderers.mido_renderer import render_midi_mido


def format_analysis_text(analysis_result: dict[str, Any]) -> str:
    """Format analysis result as human-readable text."""
    lines: list[str] = []
    
    filename = analysis_result.get("filename", "Unknown")
    lines.append(f"Composition Analysis: {filename}")
    lines.append("=" * len(f"Composition Analysis: {filename}"))
    lines.append("")
    
    # Quality Assessment
    quality = analysis_result.get("quality", {})
    if quality:
        lines.append("Quality Assessment")
        lines.append("-" * 20)
        overall_score = quality.get("overall_score", 0.0)
        technical_score = quality.get("technical_score", 0.0)
        musical_score = quality.get("musical_score", 0.0)
        structure_score = quality.get("structure_score", 0.0)
        
        def score_label(score: float) -> str:
            if score >= 0.9:
                return "Excellent"
            elif score >= 0.7:
                return "Good"
            elif score >= 0.5:
                return "Acceptable"
            else:
                return "Needs Improvement"
        
        lines.append(f"Overall Score: {overall_score:.2%} ({score_label(overall_score)})")
        lines.append(f"  Technical:  {technical_score:.2%} ({score_label(technical_score)})")
        lines.append(f"  Musical:    {musical_score:.2%} ({score_label(musical_score)})")
        lines.append(f"  Structure:  {structure_score:.2%} ({score_label(structure_score)})")
        lines.append("")
        
        issues = quality.get("issues", [])
        if issues:
            lines.append(f"Issues Found: {len(issues)}")
            for issue in issues:
                lines.append(f"  - {issue}")
            lines.append("")
    
    # Technical Metadata
    technical = analysis_result.get("technical", {})
    if technical:
        lines.append("Technical Metadata")
        lines.append("-" * 20)
        if technical.get("duration_beats") is not None:
            lines.append(f"Duration: {technical['duration_beats']:.1f} beats ({technical.get('duration_seconds', 0):.1f} seconds, {technical.get('bars', 0):.1f} bars)")
        if technical.get("tempo_bpm") is not None:
            lines.append(f"Tempo: {technical['tempo_bpm']:.1f} BPM")
        if technical.get("time_signature"):
            lines.append(f"Time Signature: {technical['time_signature']}")
        if technical.get("key_signature"):
            lines.append(f"Key Signature: {technical['key_signature']}")
        lines.append(f"Tracks: {technical.get('tracks', 0)}")
        lines.append("")
    
    # Musical Analysis
    musical = analysis_result.get("musical_analysis", {})
    if musical:
        lines.append("Musical Analysis")
        lines.append("-" * 20)
        if musical.get("detected_key"):
            lines.append(f"Key: {musical['detected_key']}")
        if musical.get("detected_form"):
            lines.append(f"Form: {musical['detected_form']}")
        if musical.get("motif_count") is not None:
            lines.append(f"Motifs: {musical['motif_count']} detected")
        if musical.get("phrase_count") is not None:
            lines.append(f"Phrases: {musical['phrase_count']} detected")
        if musical.get("chord_count") is not None:
            lines.append(f"Chords: {musical['chord_count']} detected")
        if musical.get("harmonic_progression"):
            lines.append(f"Harmonic Progression: {musical['harmonic_progression']}")
        lines.append("")
    
    # Improvement Suggestions
    suggestions = analysis_result.get("improvement_suggestions", {})
    if suggestions:
        lines.append("Improvement Suggestions")
        lines.append("-" * 20)
        
        issues_to_fix = suggestions.get("issues_to_fix", [])
        if issues_to_fix:
            lines.append("Issues to Fix:")
            for issue in issues_to_fix:
                severity = issue.get("severity", "unknown")
                lines.append(f"  - {issue.get('issue', 'Unknown issue')} ({severity} severity)")
                if issue.get("suggestion"):
                    lines.append(f"    → {issue['suggestion']}")
            lines.append("")
        
        improvements = suggestions.get("improvements", [])
        if improvements:
            lines.append("Improvements:")
            for improvement in improvements:
                lines.append(f"  - {improvement}")
            lines.append("")
        
        recommendations = suggestions.get("quality_recommendations", [])
        if recommendations:
            lines.append("Quality Recommendations:")
            for rec in recommendations:
                lines.append(f"  - {rec}")
            lines.append("")
    
    # AI Insights (optional)
    ai_insights = analysis_result.get("ai_insights")
    if ai_insights:
        lines.append("AI Insights")
        lines.append("-" * 20)
        if ai_insights.get("suggested_name"):
            lines.append(f"Suggested Name: {ai_insights['suggested_name']}")
        if ai_insights.get("suggested_style"):
            lines.append(f"Suggested Style: {ai_insights['suggested_style']}")
        if ai_insights.get("suggested_description"):
            lines.append(f"Suggested Description: {ai_insights['suggested_description']}")
        lines.append("")
    
    return "\n".join(lines)


def handle_analyze(args) -> int:
    """Handle the analyze command."""
    try:
        suffix = args.in_path.suffix.lower()
        
        # Handle JSON input (composition analysis)
        if suffix == ".json":
            if not MUSIC21_AVAILABLE:
                sys.stderr.write(
                    "warning: music21 is not installed. Musical analysis requires music21. "
                    "Install with: pip install music21\n"
                )
                return 1
            
            # Get AI provider and model from config or args
            from ...config import get_ai_provider, get_ai_model
            ai_provider = args.ai_provider or get_ai_provider()
            ai_model = args.ai_model or get_ai_model(ai_provider)
            
            # Perform comprehensive analysis
            analysis_result = analyze_for_user(
                args.in_path,
                ai_provider=ai_provider,
                ai_model=ai_model,
                verbose=args.verbose,
            )
            
            # Determine output directory and paths
            base_name = derive_base_name_from_path(args.in_path, "analyze-output")
            output_dir = get_output_base_dir(base_name, "analyze")
            
            if args.out_path is not None:
                out_json_path = resolve_output_path(
                    args.out_path, output_dir, "analysis.json", "analyze"
                )
            else:
                out_json_path = None
            
            # Output based on format
            if args.format == "text":
                output_text = format_analysis_text(analysis_result)
                if args.out_path is None:
                    sys.stdout.write(output_text)
                else:
                    write_text(out_json_path, output_text)
                    sys.stdout.write(str(out_json_path) + "\n")
            else:
                # JSON output (default)
                analysis_json = json.dumps(analysis_result, indent=2)
                if args.out_path is None:
                    sys.stdout.write(analysis_json)
                else:
                    write_text(out_json_path, analysis_json)
                    sys.stdout.write(str(out_json_path) + "\n")
            
            return 0
        
        # Handle MIDI input
        if suffix not in (".mid", ".midi"):
            raise ValueError("Input must be a .mid, .midi, or .json file.")

        # If provider is specified, use old behavior (for composition generation)
        if args.provider:
            analysis = analyze_midi(args.in_path)

        # Determine output directory and paths
        base_name = derive_base_name_from_path(args.in_path, "analyze-output")
        output_dir = get_output_base_dir(base_name, "analyze")
        
        # Resolve output paths (only if provided, to maintain stdout behavior when not provided)
        if args.out_path is not None:
            out_json_path = resolve_output_path(
                args.out_path, output_dir, "analysis.json", "analyze"
            )
        else:
            out_json_path = None
        
        # For MIDI, auto-generate path if --render is used without explicit path
        if args.render and args.provider:
            if args.out_midi_path is None:
                # Auto-generate MIDI path from input/output name
                if args.out_path is not None:
                    midi_name = args.out_path.stem + ".mid"
                else:
                    midi_name = args.in_path.stem + ".mid"
                out_midi_path = resolve_output_path(
                    Path(midi_name), output_dir, "composition.mid", "analyze"
                )
            else:
                out_midi_path = resolve_output_path(
                    args.out_midi_path, output_dir, "composition.mid", "analyze"
                )
        else:
            out_midi_path = resolve_output_path(
                args.out_midi_path, output_dir, "composition.mid", "analyze"
            ) if args.out_midi_path is not None else None
        prompt_out_path = resolve_output_path(
            args.prompt_out_path, output_dir, "prompt.txt", "analyze"
        ) if args.prompt_out_path is not None else None

        if args.provider:
            instructions = (args.instructions or "").strip()
            # Instructions are optional but recommended
            template = analysis_prompt_template(analysis, instructions=instructions)
            prompt = prompt_from_template(template)

            if prompt_out_path is not None:
                write_text(prompt_out_path, template)

            # Determine raw output path (for both reading cached and saving new)
            raw_out_path: Path | None = args.raw_out_path
            if raw_out_path is None and out_json_path is not None:
                # Default: next to JSON output (only if --out was provided)
                raw_out_path = derive_raw_path(out_json_path, args.provider)
            elif raw_out_path is not None and not raw_out_path.is_absolute():
                # Relative path: resolve relative to output directory
                raw_out_path = output_dir / raw_out_path.name
            
            # Store original raw_out_path for custom path handling (before resolution)
            custom_raw_path = args.raw_out_path
            
            # Check if we have a cached response
            raw_text: str | None = None
            if raw_out_path is not None and raw_out_path.exists():
                if args.verbose:
                    sys.stderr.write(f"Using cached AI response from {raw_out_path}\n")
                raw_text = read_text(raw_out_path)
            
            # If no cached response, call AI provider
            if raw_text is None:
                # Set default model if not provided
                from ...config import get_ai_model
                from ...ai_providers import get_default_model
                model = args.model or get_ai_model(args.provider) or get_default_model(args.provider)
                
                try:
                    raw_text = generate_text_unified(
                        provider=args.provider,
                        model=model,
                        prompt=prompt,
                        verbose=args.verbose
                    )
                except (GeminiError, OllamaError, OpenRouterError) as e:
                    sys.stderr.write(f"error: {type(e).__name__}: {e}\n")
                    return 1

            comp = parse_composition_from_text(raw_text)
            out_json = composition_to_canonical_json(comp)

            if args.out_path is None:
                sys.stdout.write(out_json)
                # Save raw response if we have it and no JSON output path
                if raw_text is not None and raw_out_path is not None:
                    write_text(raw_out_path, raw_text, version_if_exists=not args.overwrite)
                elif raw_text is not None:
                    # No path to save raw response - show warning
                    sys.stderr.write(
                        "warning: AI raw output was not saved. Provide --raw (-r) "
                        "or also provide --output (-o) to enable an automatic default.\n"
                    )
            else:
                # If custom raw path is provided, write it separately
                if custom_raw_path is not None:
                    write_text(out_json_path, out_json, version_if_exists=not args.overwrite)
                    write_text(custom_raw_path, raw_text, version_if_exists=not args.overwrite)
                    sys.stdout.write(str(out_json_path) + "\n")
                else:
                    # Use unified output utility for coordinated versioning
                    # Always write sidecar if we have raw_text (even if cached)
                    result = write_output_with_sidecar(
                        out_json_path,
                        out_json,
                        sidecar_content=raw_text,
                        provider=args.provider,
                        overwrite=args.overwrite,
                    )
                    sys.stdout.write(str(result.primary_path) + "\n")

            if args.render:
                render_midi_mido(comp, out_midi_path)
            return 0

        if args.render:
            raise ValueError("--render is only supported with --provider for 'analyze'.")

        # If provider is not specified, use comprehensive analysis
        if not args.provider:
            # Get AI provider and model from config or args
            from ...config import get_ai_provider, get_ai_model
            ai_provider = args.ai_provider or get_ai_provider()
            ai_model = args.ai_model or get_ai_model(ai_provider)
            
            # Perform comprehensive analysis
            analysis_result = analyze_for_user(
                args.in_path,
                ai_provider=ai_provider,
                ai_model=ai_model,
                verbose=args.verbose,
            )
            
            # Output based on format
            if args.format == "text":
                output_text = format_analysis_text(analysis_result)
                if args.out_path is None:
                    sys.stdout.write(output_text)
                else:
                    write_text(out_json_path, output_text)
                    sys.stdout.write(str(out_json_path) + "\n")
            elif args.format == "prompt":
                # For prompt format, still use old analysis for prompt generation
                analysis = analyze_midi(args.in_path)
                prompt = analysis_prompt_template(analysis, instructions=args.instructions)
                if prompt_out_path is not None:
                    write_text(prompt_out_path, prompt)
                    sys.stdout.write(str(prompt_out_path) + "\n")
                else:
                    # If --out was provided and we're in prompt-only mode, treat it as prompt output.
                    if args.out_path is not None:
                        write_text(out_json_path, prompt)
                        sys.stdout.write(str(out_json_path) + "\n")
                    else:
                        sys.stdout.write(prompt)
            else:
                # JSON output (default)
                analysis_json = json.dumps(analysis_result, indent=2)
                if args.out_path is None:
                    sys.stdout.write(analysis_json)
                else:
                    write_text(out_json_path, analysis_json)
                    sys.stdout.write(str(out_json_path) + "\n")
        else:
            # Old behavior: prompt format with provider
            if args.format in ("json", "both"):
                out_json = analysis.to_pretty_json()
                if args.out_path is None:
                    sys.stdout.write(out_json)
                else:
                    write_text(out_json_path, out_json)
                    sys.stdout.write(str(out_json_path) + "\n")

            if args.format in ("prompt", "both"):
                prompt = analysis_prompt_template(analysis, instructions=args.instructions)
                if prompt_out_path is not None:
                    write_text(prompt_out_path, prompt)
                    # Only print the path if we didn't already print JSON path.
                    if args.format == "prompt":
                        sys.stdout.write(str(prompt_out_path) + "\n")
                else:
                    # If --out was provided and we're in prompt-only mode, treat it as prompt output.
                    if args.format == "prompt" and args.out_path is not None:
                        write_text(out_json_path, prompt)
                        sys.stdout.write(str(out_json_path) + "\n")
                    else:
                        sys.stdout.write(prompt)
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0


def setup_parser(parser):
    """Set up the analyze command parser."""
    parser.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input file: MIDI (.mid/.midi) or JSON composition (.json).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["prompt", "json", "text", "both"],
        default="json",
        help="Output format: 'json' (default), 'text' (human-readable), 'prompt', or 'both'.",
    )
    from ...config import get_ai_provider, get_ai_model
    
    parser.add_argument(
        "--ai-provider",
        type=str,
        choices=["gemini", "ollama", "openrouter"],
        default=None,
        help="AI provider for analysis insights: 'gemini', 'ollama', or 'openrouter'. AI is always used for generating suggested name, style, and description. Defaults to config file or 'openrouter'.",
    )
    parser.add_argument(
        "--ai-model",
        type=str,
        default=None,
        help="Model name for AI analysis. Defaults to config file or provider default. Free OpenRouter options: mistralai/devstral-2512:free (recommended), xiaomi/mimo-v2-flash:free, tngtech/deepseek-r1t2-chimera:free, nex-agi/deepseek-v3.1-nex-n1:free",
    )
    parser.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output path for JSON (or prompt if --format prompt and --prompt not provided). If omitted, prints to stdout.",
    )
    parser.add_argument(
        "-p", "--prompt",
        dest="prompt_out_path",
        type=Path,
        default=None,
        help="Write the prompt text to this path.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "ollama", "openrouter"],
        default=None,
        help=f"AI provider to use for generating a new composition: 'gemini' (cloud), 'ollama' (local), or 'openrouter' (cloud). Defaults to config file or '{get_ai_provider()}'. If omitted, only generates analysis/prompt.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Model name to use with the provider. Defaults to config file or provider default. Only used with --provider.",
    )
    parser.add_argument(
        "-r", "--raw",
        dest="raw_out_path",
        type=Path,
        default=None,
        help="Save the raw AI response text to this path. Auto-generated if --output is provided. Only used with --provider.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Also render the AI-generated composition to MIDI (only valid with --provider).",
    )
    parser.add_argument(
        "-m", "--midi",
        dest="out_midi_path",
        type=Path,
        default=None,
        help="Output MIDI path. Auto-generated from input/output name if --render is used without this flag.",
    )
    parser.add_argument(
        "--instructions",
        type=str,
        default="",
        help="Instructions for composing a new piece (optional, but recommended when using --provider).",
    )
