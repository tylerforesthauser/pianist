"""Main CLI entry point with argparse setup and command routing."""
from __future__ import annotations

import argparse

from .commands import (
    analyze,
    annotate,
    diff,
    expand,
    fix,
    generate,
    import_,
    modify,
    reference,
    render,
)
from .util import add_common_flags


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pianist",
        description="Framework for human-AI collaboration in musical composition. Convert between JSON and MIDI, analyze compositions, and expand incomplete works.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Render command
    render_parser = sub.add_parser("render", help="Parse model output and render a MIDI file.")
    render.setup_parser(render_parser)
    add_common_flags(render_parser)

    # Import command
    import_parser = sub.add_parser(
        "import",
        help="Import a MIDI file and convert it to Pianist JSON format.",
    )
    import_.setup_parser(import_parser)
    add_common_flags(import_parser)

    # Modify command
    modify_parser = sub.add_parser(
        "modify",
        help="Modify an existing composition (transpose, fix, or modify with AI).",
    )
    modify.setup_parser(modify_parser)
    add_common_flags(modify_parser)

    # Analyze command
    analyze_parser = sub.add_parser(
        "analyze",
        help="Analyze a .mid/.midi file and emit prompt-friendly output.",
    )
    analyze.setup_parser(analyze_parser)
    add_common_flags(analyze_parser)

    # Fix command
    fix_parser = sub.add_parser(
        "fix",
        help="Fix composition issues (pedal patterns, etc.).",
    )
    fix.setup_parser(fix_parser)
    add_common_flags(fix_parser)

    # Annotate command
    annotate_parser = sub.add_parser(
        "annotate",
        help="Mark musical intent (key ideas, expansion points, etc.).",
    )
    annotate.setup_parser(annotate_parser)
    add_common_flags(annotate_parser)

    # Expand command
    expand_parser = sub.add_parser(
        "expand",
        help="Expand an incomplete composition to a complete work.",
    )
    expand.setup_parser(expand_parser)
    add_common_flags(expand_parser)

    # Diff command
    diff_parser = sub.add_parser(
        "diff",
        help="Show what changed between two compositions.",
    )
    diff.setup_parser(diff_parser)
    add_common_flags(diff_parser)

    # Generate command
    generate_parser = sub.add_parser(
        "generate",
        help="Generate a new composition from a text description.",
    )
    generate.setup_parser(generate_parser)
    add_common_flags(generate_parser)

    # Reference command
    reference_parser = sub.add_parser(
        "reference",
        help="Manage musical reference database (add, list, search, get, delete).",
    )
    reference.setup_parser(reference_parser)
    add_common_flags(reference_parser)

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse raises SystemExit on errors, convert to return code
        return e.code if e.code is not None else 1

    # Route to appropriate command handler
    if args.cmd == "render":
        return render.handle_render(args)
    elif args.cmd == "import":
        return import_.handle_import(args)
    elif args.cmd == "modify":
        return modify.handle_modify(args)
    elif args.cmd == "analyze":
        return analyze.handle_analyze(args)
    elif args.cmd == "fix":
        return fix.handle_fix(args)
    elif args.cmd == "annotate":
        return annotate.handle_annotate(args)
    elif args.cmd == "expand":
        return expand.handle_expand(args)
    elif args.cmd == "diff":
        return diff.handle_diff(args)
    elif args.cmd == "generate":
        return generate.handle_generate(args)
    elif args.cmd == "reference":
        return reference.handle_reference(args)
    else:
        raise RuntimeError("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())
