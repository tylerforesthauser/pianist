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
# site.main() is idempotent and safe to call unconditionally
site.main()

from pianist.cli import main
