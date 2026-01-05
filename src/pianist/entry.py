"""Entry point wrapper for editable install compatibility.

This module ensures .pth files are processed correctly for editable installs
by calling site.main() before importing the main module. This addresses an
issue where entry point scripts may not process .pth files correctly in
some Python versions (notably Python 3.14+).
"""
from __future__ import annotations

import site

# Ensure .pth files are processed for editable installs
# This must be called before importing the main module
# site.main() is idempotent and safe to call unconditionally
site.main()

from pianist.cli import main
