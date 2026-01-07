"""CLI package with compatibility shim for old import paths."""
from __future__ import annotations

# Compatibility shim: re-export main from the new location
from .main import main

__all__ = ["main"]
