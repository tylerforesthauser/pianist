"""Pytest configuration for pianist tests.

This ensures the src directory is in the Python path so tests can import the pianist package.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to the Python path
# This is needed because Python 3.14+ may not process .pth files correctly in some cases
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

