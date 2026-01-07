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


SYSTEM_PROMPT = _read_prompt_asset("system_prompt.txt").strip()


