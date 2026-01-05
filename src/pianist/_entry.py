"""Entry point wrapper for Python 3.14+ compatibility.

This module ensures .pth files are processed correctly for editable installs
in Python 3.14+, where entry point scripts may not process .pth files before
importing the main module.
"""
from __future__ import annotations

import site
import sys

# Ensure .pth files are processed for editable installs (Python 3.14+ fix)
# This must be called before importing the main module
if sys.version_info >= (3, 14):
    site.main()

from pianist.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
