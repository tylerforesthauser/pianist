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

- **Run tests (ALWAYS in parallel):** `pytest -m "not integration" -n auto` or `make test`
- Run failed tests only: `pytest -m "not integration" -n auto --lf`
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

**Always:** Activate venv (`source .venv/bin/activate`) before Python commands. Run `make quality` and tests (in parallel with `-n auto`) after code changes. Never commit unless explicitly requested.

**When to RUN:** Tests, quality checks (`make quality`), verification commands, sync prompts.

**When to SUGGEST:** Integration tests (require API keys), destructive operations, commands requiring user input/API keys, git commits.

### Code quality enforcement

**MANDATORY before any code changes are considered complete:**
1. Run `make quality` - Must pass with zero errors
2. Run `make lint-fix && make format` if issues found
3. Run tests in parallel: `pytest -m "not integration" -n auto` or `make test`
4. Verify: All checks pass, no warnings, no errors

**Test execution:** Always use parallel execution (`-n auto`) - it's 2-3x faster and is the standard for this project.

**Pre-commit hooks:** Installed hooks automatically check code quality. If hooks fail, fix issues before committing (or use `--no-verify` only if explicitly needed and documented).

### Documentation rules

**DO NOT create new docs unless requested. Update existing files only.**

- Update ROADMAP.md "Current Status" if status changed (single source of truth)
- Use `docs/temp/` for temporary/planning documents, remove when done
- DO NOT create new markdown documents for every plan - consolidate into existing planning documents
- DO NOT create separate status documents - Update ROADMAP.md instead
- Run `make sync-prompts` if prompt templates modified
- **NEVER include dates or timelines** - Do not add project dates (e.g., "2024-12", "2025-01", "June 2026"), quarters (e.g., "Q1 2025"), or any project timeline references in documentation. Focus on status and features, not when they were completed or when they will be completed. Exception: Third-party service deprecation dates and shutdown dates (e.g., API model deprecations) are appropriate to include.

## Development mode

**The project is currently in active development with no external users or production deployments.**

- **No backwards compatibility requirements:** Breaking changes are acceptable when they improve code quality, maintainability, or align with the project roadmap
- **Focus on efficiency:** Prioritize clean, maintainable code over preserving existing interfaces
- **Refactor freely:** Don't hesitate to restructure code, rename functions, or change APIs if it makes the codebase better
- **Roadmap-driven:** Changes should align with the project roadmap and current development priorities

## When implementing new features

**REQUIRED steps:**

1. **Write tests** - Unit tests for functions/modules, integration tests for CLI (mark with `@pytest.mark.integration`), aim for >80% coverage
2. **Run tests** - `pytest -m "not integration" -n auto` (always in parallel, REQUIRED)
3. **Fix failing tests** - Do not proceed until all tests pass
4. **Update existing tests** - When refactoring, fix broken tests and update expectations
5. **Update documentation** - Update existing docs only, update ROADMAP.md if status changed, run `make sync-prompts` if prompts changed, remove temp files from `docs/temp/`

## Before completing task

**CRITICAL CHECKLIST - All items must be verified:**

- [ ] All code finished (no TODOs, placeholders, incomplete implementations)
- [ ] **Quality checks pass (`make quality`)** - Lint, format-check, type-check all pass
- [ ] **All linting errors fixed** - Run `make lint-fix && make format` if needed
- [ ] **Tests pass in parallel** (`pytest -m "not integration" -n auto` or `make test`) - REQUIRED
- [ ] **All related tests written and passing** - New features must have tests
- [ ] No broken imports or syntax errors
- [ ] No temp files, debug code, or commented-out code
- [ ] Documentation updated (existing files only)
- [ ] ROADMAP.md updated if status changed
- [ ] `make sync-prompts` run if prompt templates modified
- [ ] Temporary documents removed from `docs/temp/` (if any were created)

**If quality checks fail:** Fix issues immediately. Do not proceed with incomplete or non-compliant code.

## Commit instructions

**CRITICAL: DO NOT commit changes unless explicitly requested by the user.**

**When to commit:**
- ❌ **NEVER commit automatically** - Only commit when the user explicitly asks you to
- ✅ **ONLY commit when requested** - Wait for explicit instructions like "commit these changes" or "commit your work"
- ✅ **ONLY commit complete work** - Verify all changes are finished, tested, and working before committing
- ❌ **DO NOT commit incomplete work** - If changes are not complete, inform the user and do not commit

**Commit workflow (when requested):**
1. **Verify completeness** - Use "Before completing task" checklist above
2. **Review changes:** `git status` and `git diff`
3. **Exclude incomplete work** - DO NOT commit files with TODOs, failing tests, syntax errors, or temp/debug code
4. **Create atomic commits** - One commit per logical group (code, tests, docs separate)
5. **Commit message format:** `<type>: <subject>` (types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`, `chore`)
6. **Verify:** `git log --oneline -5`
7. **Inform user** - List commits created, note any files left uncommitted and why

**Commit message guidelines:**
- Use imperative mood ("add" not "added")
- Keep subject under 72 characters
- Capitalize first letter, no period
- Examples: `feat: add MIDI quality validation`, `fix: correct pattern matching algorithm`, `docs: update ROADMAP.md`

## Project structure

- `src/pianist/` - Main source code
- `tests/` - Test files (`test_*.py`)
- `docs/` - Documentation
  - `docs/temp/` - **Temporary/planning documents** (gitignored, clean up when done)
- `input/`, `output/` - User files (gitignored)
- `references/` - Reference database staging

**Key files:** `ROADMAP.md` (single source of truth for status), `MISSION.md`, `PLANNING.md`

## Common tasks

**Adding CLI command:** Create `src/pianist/cli/commands/<command>.py`, register in `src/pianist/cli/main.py`, write tests, document in `docs/commands/<command>.md`.

**Adding module:** Create `src/pianist/<module>.py`, write tests `tests/test_<module>.py`, add to `__init__.py` if public API.
