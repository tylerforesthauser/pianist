from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT / "AI_PROMPTING_GUIDE.md"
PROMPTS_DIR = ROOT / "src" / "pianist" / "prompts"


def _read_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8").rstrip() + "\n"


def _replace_between_markers(text: str, marker: str, replacement_body: str) -> str:
    begin = f"<!-- BEGIN {marker} -->"
    end = f"<!-- END {marker} -->"

    begin_idx = text.find(begin)
    end_idx = text.find(end)
    if begin_idx == -1 or end_idx == -1 or end_idx < begin_idx:
        raise ValueError(f"Missing or invalid markers for {marker!r} in {GUIDE_PATH}")

    before = text[: begin_idx + len(begin)]
    after = text[end_idx:]

    replacement = "\n```" + "\n" + replacement_body.rstrip() + "\n```\n"
    return before + "\n" + replacement + after


def _extract_between_markers(text: str, marker: str) -> str:
    begin = f"<!-- BEGIN {marker} -->"
    end = f"<!-- END {marker} -->"

    begin_idx = text.find(begin)
    end_idx = text.find(end)
    if begin_idx == -1 or end_idx == -1 or end_idx < begin_idx:
        raise ValueError(f"Missing or invalid markers for {marker!r} in {GUIDE_PATH}")

    inner = text[begin_idx + len(begin) : end_idx]

    # Expect a single fenced code block inside the markers.
    first = inner.find("```")
    if first == -1:
        return ""
    second = inner.find("```", first + 3)
    if second == -1:
        return ""
    body = inner[first + 3 : second]
    return body.strip() + "\n"


def sync(write: bool) -> int:
    guide = GUIDE_PATH.read_text(encoding="utf-8")

    short_prompt = _read_prompt("system_prompt_short.txt")
    full_prompt = _read_prompt("system_prompt_full.txt")

    if not write:
        guide_short = _extract_between_markers(guide, "SYSTEM_PROMPT_SHORT")
        guide_full = _extract_between_markers(guide, "SYSTEM_PROMPT_FULL")

        ok = True
        if guide_short != short_prompt:
            print("Mismatch: SYSTEM_PROMPT_SHORT (guide vs prompts file)")
            ok = False
        if guide_full != full_prompt:
            print("Mismatch: SYSTEM_PROMPT_FULL (guide vs prompts file)")
            ok = False
        return 0 if ok else 1

    guide = _replace_between_markers(guide, "SYSTEM_PROMPT_FULL", full_prompt)
    guide = _replace_between_markers(guide, "SYSTEM_PROMPT_SHORT", short_prompt)
    GUIDE_PATH.write_text(guide, encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync packaged prompts into AI_PROMPTING_GUIDE.md.")
    ap.add_argument(
        "--check",
        action="store_true",
        help="Check whether AI_PROMPTING_GUIDE.md matches prompt files (exit 1 on drift).",
    )
    args = ap.parse_args()

    return sync(write=not args.check)


if __name__ == "__main__":
    raise SystemExit(main())


