"""Main CLI entry point with argparse setup."""
from __future__ import annotations

import argparse
import sys

# Import refactored command modules
from .commands import render, import_, modify, fix, diff

# For commands not yet fully refactored, we'll import from legacy
# This allows incremental refactoring while maintaining full compatibility
from ..cli_legacy import main as legacy_main


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    # Prepare argv
    if argv is None:
        argv_copy = sys.argv[1:]
    else:
        argv_copy = list(argv) if argv else []
    
    # Check for help or no arguments - use legacy to show all commands
    if not argv_copy or argv_copy[0] in ('-h', '--help'):
        return legacy_main(argv)
    
    # Check for legacy commands and delegate to legacy implementation
    legacy_commands = {"annotate", "expand", "analyze", "generate", "reference"}
    if argv_copy[0] in legacy_commands:
        return legacy_main(argv)
    
    # Otherwise, use the new refactored implementation
    parser = argparse.ArgumentParser(
        prog="pianist",
        description="Framework for human-AI collaboration in musical composition. Convert between JSON and MIDI, analyze compositions, and expand incomplete works.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Setup refactored command parsers
    render.setup_parser(sub)
    import_.setup_parser(sub)
    modify.setup_parser(sub)
    fix.setup_parser(sub)
    diff.setup_parser(sub)
    
    # Parse arguments
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse raises SystemExit on errors, convert to return code
        return e.code if e.code is not None else 1

    # Dispatch to command handlers
    if args.cmd == "render":
        return render.handle(args)
    elif args.cmd == "import":
        return import_.handle(args)
    elif args.cmd == "modify":
        return modify.handle(args)
    elif args.cmd == "fix":
        return fix.handle(args)
    elif args.cmd == "diff":
        return diff.handle(args)
    else:
        # This shouldn't happen if we set up parsers correctly
        raise RuntimeError(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
