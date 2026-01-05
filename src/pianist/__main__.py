"""Allow running pianist as a module: python -m pianist"""
from __future__ import annotations

import site
import sys
from pathlib import Path

# Ensure .pth files are processed
site.main()

# Fallback: add src to path if needed
try:
    from .cli import main
except (ImportError, ModuleNotFoundError):
    # Find src directory
    this_file = Path(__file__).resolve()
    src_path = this_file.parent.parent
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
