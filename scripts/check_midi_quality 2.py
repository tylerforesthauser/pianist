#!/usr/bin/env python3
"""
Quality check tool for MIDI files before importing into reference database.

This script analyzes MIDI files for:
- Technical quality (timing, velocity, structure)
- Musical coherence (harmony, form, motifs)
- Common issues (missing notes, timing errors, etc.)
- AI-based quality assessment

Usage:
    # Check single file
    python3 scripts/check_midi_quality.py file.mid

    # Check directory of files
    python3 scripts/check_midi_quality.py --dir references/ --verbose

    # Check with AI assessment (always used)
    python3 scripts/check_midi_quality.py file.mid --provider gemini
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pianist.ai_providers import get_default_model
from pianist.config import get_ai_model, get_ai_provider
from pianist.quality import (
    QualityReport,
    check_midi_file,
    print_report,
)


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
        "--provider",
        type=str,
        default=None,
        choices=["gemini", "ollama", "openrouter"],
        help=f"AI provider for assessment: 'gemini' (cloud), 'ollama' (local), or 'openrouter' (cloud). Defaults to config file or '{get_ai_provider()}'. AI is always used for quality assessment.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name. Defaults to config file or provider default (mistralai/devstral-2512:free for OpenRouter).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
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
        # Get provider and model from args or config
        provider = args.provider or get_ai_provider()
        model = args.model or get_ai_model(provider) or get_default_model(provider)

        report = check_midi_file(file_path, provider, model)
        reports.append(report)
        print_report(report, args.verbose)

    # Summary
    if len(reports) > 1:
        print(f"\n{'=' * 60}")
        print(f"Summary: {len(reports)} files checked")
        print(f"{'=' * 60}")

        passed = [r for r in reports if r.overall_score >= args.min_score]
        failed = [r for r in reports if r.overall_score < args.min_score]

        print(f"✅ Passed (score >= {args.min_score:.0%}): {len(passed)}")
        print(f"❌ Failed (score < {args.min_score:.0%}): {len(failed)}")

        if passed:
            avg_score = sum(r.overall_score for r in passed) / len(passed)
            print(f"\nAverage score (passed): {avg_score:.2%}")

        if failed:
            print("\nFailed files:")
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
