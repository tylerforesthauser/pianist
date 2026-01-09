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

**CRITICAL: Code quality is mandatory.**
- **Always run `make quality` after code changes** - This checks linting, formatting, and type checking
- **Fix all issues before proceeding** - Use `make lint-fix && make format` to auto-fix most issues
- **All checks must pass** - No exceptions. See `docs/technical/CODE_QUALITY.md` for details
- **Pre-commit hooks enforce quality** - Install with `make install-pre-commit` to catch issues before commit

## Code style and quality

**Enforced by Ruff, MyPy, and pre-commit hooks. See `docs/technical/CODE_QUALITY.md` for full details.**

**Style requirements:**
- PEP 8 guidelines (enforced by Ruff)
- Type hints for function signatures (checked by MyPy)
- Pydantic models for data validation
- Single-purpose functions
- Clear docstrings for public functions

**Code quality standards:**
- **Zero linting errors** - All Ruff checks must pass (`make lint`)
- **Consistent formatting** - Code must be formatted (`make format-check`)
- **Type safety** - Type hints validated by MyPy (`make type-check`)
- **No unused code** - Unused imports, variables, arguments are flagged
- **Simplified logic** - Nested ifs combined, conditions simplified

**Performance:** Use O(n) or O(n log n) over O(n²). Avoid redundant computations. Pass pre-computed results as optional parameters.

**Common fixes:**
- Unused arguments: Prefix with `_` (e.g., `_unused_arg`)
- Nested ifs: Combine conditions with `and`
- Unused imports: Remove or use `# noqa: F401` if intentional
- Type issues: Add proper type hints or use `# type: ignore` sparingly

## Critical rules

**⚠️ READ THIS FIRST: These rules are frequently ignored. Follow them strictly.**

**Always:** Activate venv (`source .venv/bin/activate`) before Python commands. Run `make quality` and tests after code changes. Never commit unless explicitly requested.

**When to RUN:** Tests, quality checks (`make quality`), verification commands, sync prompts.

**When to SUGGEST:** Integration tests (require API keys), destructive operations, commands requiring user input/API keys, git commits.

### Code quality enforcement

**MANDATORY before any code changes are considered complete:**
1. Run `make quality` - Must pass with zero errors
2. Run `make lint-fix && make format` if issues found
3. Run tests: `pytest -m "not integration"`
4. Verify: All checks pass, no warnings, no errors

**Pre-commit hooks:** Installed hooks automatically check code quality. If hooks fail, fix issues before committing (or use `--no-verify` only if explicitly needed and documented).

**Documentation:** DO NOT create new docs unless requested. Update existing files only. Update ROADMAP.md "Current Status" if status changed. Use `docs/temp/` for WIP, remove when done.

## Project structure

- `src/pianist/` - Main source code
- `tests/` - Test files (`test_*.py`)
- `docs/` - Documentation
- `input/`, `output/` - User files (gitignored)
- `references/` - Reference database staging

**Key files:** `ROADMAP.md` (single source of truth for status), `MISSION.md`, `PLANNING.md`

## Before completing task

**CRITICAL CHECKLIST - All items must be verified:**

- [ ] All code finished (no TODOs, placeholders, incomplete implementations)
- [ ] **Quality checks pass (`make quality`)** - Lint, format-check, type-check all pass
- [ ] **All linting errors fixed** - Run `make lint-fix && make format` if needed
- [ ] Tests pass (`pytest -m "not integration"`)
- [ ] No broken imports or syntax errors
- [ ] No temp files, debug code, or commented-out code
- [ ] Documentation updated (existing files only)
- [ ] ROADMAP.md updated if status changed
- [ ] `make sync-prompts` run if prompt templates modified

**If quality checks fail:** Fix issues immediately. Do not proceed with incomplete or non-compliant code.

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
