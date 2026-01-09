"""Entry point wrapper for editable install compatibility.

This module ensures .pth files are processed correctly for editable installs
by handling path setup before importing the main module. This addresses an
issue where entry point scripts may not process .pth files correctly in
some Python versions (notably Python 3.14+).
"""

from __future__ import annotations

import site
import sys
from pathlib import Path

# Process .pth files for editable installs
# This must be called before importing the main module
# site.main() is idempotent and safe to call unconditionally
site.main()

# Fallback: If pianist still can't be imported, manually add src to path
# This handles cases where .pth file processing doesn't work as expected
try:
    from .cli import main
except (ImportError, ModuleNotFoundError):
    # Find the src directory by locating this file
    # entry.py is at src/pianist/entry.py, so src is parent.parent
    this_file = Path(__file__).resolve()
    src_path = this_file.parent.parent
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    # Also try to find and process .pth files manually
    try:
        import sysconfig

        # Find site-packages directory
        site_packages = Path(sysconfig.get_path("purelib"))
        if site_packages.exists():
            # Look for our .pth file
            pth_files = list(site_packages.glob("__editable__.*.pth"))
            for pth_file in pth_files:
                if "pianist" in pth_file.name:
                    pth_path = pth_file.read_text().strip()
                    if pth_path and Path(pth_path).exists() and str(pth_path) not in sys.path:
                        sys.path.insert(0, str(pth_path))
    except Exception:
        pass  # Fallback failed, continue with src_path

    # Now try importing again
    from .cli import main

__all__ = ["main"]
