"""CLI package for pianist.

This package contains the command-line interface implementation,
organized into submodules for better maintainability.

The refactoring is complete for: render, import, modify, fix, diff
Legacy commands (annotate, expand, analyze, generate, reference) are still
in cli_legacy.py for now but can be refactored incrementally.
"""
from __future__ import annotations

from .main import main

# Re-export utility functions for backward compatibility
from .util import (
    DEFAULT_OUTPUT_DIR as _DEFAULT_OUTPUT_DIR,
    add_common_flags,
    derive_base_name_from_path as _derive_base_name_from_path,
    derive_raw_path as _derive_raw_path,
    get_output_base_dir as _get_output_base_dir,
    prompt_from_template as _prompt_from_template,
    read_text as _read_text,
    resolve_output_path as _resolve_output_path,
    version_path_if_exists as _version_path_if_exists,
    write_text as _write_text,
)

# Re-export AI provider functions for test mocking compatibility
from ..ai_providers import (
    GeminiError,
    OllamaError,
    generate_text,
    generate_text_unified,
)

# Re-export MUSIC21_AVAILABLE for test compatibility
from ..musical_analysis import MUSIC21_AVAILABLE

__all__ = [
    "main",
    # Internal utilities (underscore-prefixed for backward compat)
    "_DEFAULT_OUTPUT_DIR",
    "_derive_base_name_from_path",
    "_derive_raw_path",
    "_get_output_base_dir",
    "_prompt_from_template",
    "_read_text",
    "_resolve_output_path",
    "_version_path_if_exists",
    "_write_text",
    "add_common_flags",
    # AI provider functions
    "GeminiError",
    "OllamaError",
    "generate_text",
    "generate_text_unified",
    # Music analysis
    "MUSIC21_AVAILABLE",
]
