# AGENTS.md

Instructions for AI agents working on the Pianist project.

**For project mission, goals, and principles:** See [`MISSION.md`](MISSION.md)  
**For current status, progress, and priorities:** See [`ROADMAP.md`](ROADMAP.md) (single source of truth)

## Setup commands

- Activate venv: `source .venv/bin/activate`
- Install package: `python3 -m pip install -e ".[dev]"`
- Fix entry point: `python3 scripts/fix_entry_point.py` (required after installation)
- Verify: `./pianist --version`
- Optional deps: `python3 -m pip install -e ".[dev,gemini,dotenv]"`

## Build and test commands

- Run tests: `pytest -m "not integration"`
- Run tests in parallel: `pytest -m "not integration" -n auto`
- Run failed tests only: `pytest -m "not integration" --lf`
- Code quality: `make quality` (lint, format-check, type-check)
- Auto-fix issues: `make lint-fix && make format`
- Sync prompts: `make sync-prompts` (after modifying prompt templates)

**Rules:** Always run `make quality` and tests after code changes. Fix failures before proceeding.

## Code style

- PEP 8 guidelines
- Type hints for function signatures
- Pydantic models for data validation
- Single-purpose functions
- Clear docstrings for public functions

**Performance:** Use O(n) or O(n log n) over O(n²). Avoid redundant computations. Pass pre-computed results as optional parameters.

## Critical rules

**Always:** Activate venv before Python commands. Run `make quality` and tests after changes. Never commit unless explicitly requested.

**When to RUN:** Tests, quality checks, verification commands, sync prompts.

**When to SUGGEST:** Integration tests (require API keys), destructive operations, git commits.

**Documentation:** DO NOT create new docs unless requested. Update existing files only. Update ROADMAP.md "Current Status" if status changed. Use `docs/temp/` for WIP, remove when done.

## Project structure

- `src/pianist/` - Main source code
- `tests/` - Test files (`test_*.py`)
- `docs/` - Documentation
- `input/`, `output/` - User files (gitignored)
- `references/` - Reference database staging

**Key files:** `ROADMAP.md` (single source of truth for status), `MISSION.md`, `PLANNING.md`

## Before completing task

- [ ] All code finished (no TODOs, placeholders)
- [ ] Quality checks pass (`make quality`)
- [ ] Tests pass (`pytest -m "not integration"`)
- [ ] No broken imports or syntax errors
- [ ] No temp files, debug code, or commented code
- [ ] Documentation updated (existing files only)
- [ ] ROADMAP.md updated if status changed
- [ ] `make sync-prompts` run if prompts changed

## Commit instructions

**DO NOT commit unless explicitly requested.**

When requested:
- Verify completeness (use checklist above)
- One commit per feature/logical change
- Format: `<type>: <subject>` (types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`, `chore`)
- Example: `feat: add MIDI quality validation`

## Common tasks

**Adding CLI command:** Create `src/pianist/cli/commands/<command>.py`, register in `src/pianist/cli/main.py`, write tests, document in `docs/commands/<command>.md`.

**Adding module:** Create `src/pianist/<module>.py`, write tests `tests/test_<module>.py`, add to `__init__.py` if public API.
