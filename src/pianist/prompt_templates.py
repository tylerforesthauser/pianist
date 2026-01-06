from __future__ import annotations

"""
Prompt templates used by the CLI helpers that generate ready-to-paste LLM prompts.

Source of truth: the packaged prompt files in `src/pianist/prompts/`.
`AI_PROMPTING_GUIDE.md` should be synced from those files via `scripts/sync_prompts_to_guide.py`.
"""

from importlib import resources


def _read_prompt_asset(filename: str) -> str:
    """
    Read a packaged prompt asset from `pianist.prompts`.
    """
    return resources.files("pianist.prompts").joinpath(filename).read_text(encoding="utf-8")


# Keep this intentionally compact: CLI prompt generation often includes large seed JSON
# or analysis blocks, so we prefer a short, high-signal system prompt.
SYSTEM_PROMPT_SHORT = _read_prompt_asset("system_prompt_short.txt").strip()
SYSTEM_PROMPT_FULL = _read_prompt_asset("system_prompt_full.txt").strip()


