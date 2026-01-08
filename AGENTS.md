# AGENTS.md

Instructions for AI agents working on the Pianist project.

**For project mission, goals, and principles:** See [`MISSION.md`](MISSION.md)  
**For current status, progress, and priorities:** See [`ROADMAP.md`](ROADMAP.md) (single source of truth)

## Setup commands

- Activate virtual environment: `source .venv/bin/activate`
- Install package: `python3 -m pip install -e ".[dev]"`
- Fix entry point (required after installation): `python3 scripts/fix_entry_point.py`
  - **Why needed:** `pyproject.toml` with `setuptools.build_meta` doesn't execute `setup.py` custom commands, so entry point script needs manual fixing for editable installs (especially Python 3.14+)
- Verify installation: `./pianist --version` (or `python3 -m pianist --version`)
- Install optional dependencies: `python3 -m pip install -e ".[dev,gemini,dotenv]"`

**If encountering import errors, try:**
- `python3 -m pip install -e . --force-reinstall --no-deps` (then run `fix_entry_point.py`)

## Build and test commands

- Run unit tests: `source .venv/bin/activate && pytest -m "not integration"`
- Sync prompts: `make sync-prompts` (after modifying prompt templates)
- Verify package: `./pianist --version` (or `python3 -m pianist --version`)

**Test rules:** Always run unit tests after code changes. Suggest (don't run) integration tests - requires API keys. Fix failing tests before proceeding.

## Critical rules

**⚠️ READ THIS FIRST: These rules are frequently ignored. Follow them strictly.**

**Always:** Activate venv (`source .venv/bin/activate`) before Python commands. Run tests after code changes. Never commit unless explicitly requested.

**When to RUN:** Tests, verification commands, sync prompts.

**When to SUGGEST (don't run):** Integration tests, destructive operations, commands requiring user input/API keys, git commits.

### Documentation rules

**CRITICAL: DO NOT create new documentation files unless explicitly requested.**

**Rules:** Update existing files, consolidate related docs, update ROADMAP.md "Current Status" (never create separate status docs), use `docs/temp/` for WIP, remove temp files when done.

**After code changes:** Update command/workflow docs if changed, update ROADMAP.md if status changed, update README.md if user-facing features changed, run `make sync-prompts` if prompt templates changed, remove temp files.

## Project structure

**Key directories:**
- `src/pianist/` - Main source code
- `tests/` - Test files (`test_*.py`), fixtures (`fixtures/`), test output (`analysis/`)
- `docs/` - Documentation (`commands/`, `workflows/`, `guides/`, `technical/`, `reference/`, `temp/` for WIP)
- `input/`, `output/` - User files (gitignored)
- `references/` - Reference database staging (import with `scripts/batch_import_references.py`)

**Key files:**
- `ROADMAP.md` - Single source of truth for status (always update this, not separate docs)
- `MISSION.md`, `PLANNING.md` - Project planning

**File naming:** Output files: `output/<base-name>/<command>/<filename>`. Docs: `docs/<category>/<name>.md`. Tests: `tests/test_<module>.py`.

## Testing instructions

**Write tests:** Unit tests (`tests/test_<module>.py`), CLI tests (`tests/test_cli_<command>.py`), integration tests (mark with `@pytest.mark.integration`), fixtures in `tests/fixtures/`. Aim for >80% coverage.

**Test failures:** Verify implementation correctness first. If wrong, fix implementation. If correct, update test expectations. Don't blindly change tests to make them pass.

## Code style

- PEP 8 style guidelines
- Type hints for function signatures
- Pydantic models for data validation
- Single-purpose functions
- Clear docstrings for public functions

**Module organization:**
- `src/pianist/` - Main source code
- `src/pianist/cli/commands/` - CLI commands
- `src/pianist/<module>.py` - Core modules
- `src/pianist/renderers/` - Renderers
- `src/pianist/prompts/` - Prompts

**Dependencies:** Add to `pyproject.toml`, use optional extras (`[gemini]`, `[dev]`), document in README.md

### Performance guidelines

**CRITICAL: Avoid inefficient algorithms and redundant computations.**

**Algorithm complexity:** Use O(n) or O(n log n) over O(n²). Use hash tables/dictionaries for lookups, sets for membership. For MIDI files, assume large inputs (thousands of notes).

**Avoid redundant computations:** Functions should accept pre-computed results as optional parameters. Pass results between functions instead of recomputing. Reuse expensive objects (e.g., music21 streams).

**When to optimize:** O(n²) when O(n) alternative exists, redundant computations, >10s for typical inputs. Don't optimize if already fast (<1s) or would harm readability.

**Examples:** Hash-based grouping: 98.93s → 0.09s. Pre-computed parameters: eliminated ~500s.

### Development mode

**Active development:** No backwards compatibility requirements. Breaking changes acceptable if they improve code quality. Refactor freely. Roadmap-driven changes.

## Development workflow

**Making changes:**
1. Implement changes following code quality guidelines
2. Write/update tests for new functionality
3. Run tests: `source .venv/bin/activate && pytest -m "not integration"`
4. Fix any failing tests before proceeding
5. Update documentation (existing files only, update ROADMAP.md if status changed)
6. Run `make sync-prompts` if prompt templates changed
7. Verify: `./pianist --version` (or `python3 -m pianist --version`)

**Before completing task:**
- [ ] All code finished (no TODOs, placeholders, incomplete implementations)
- [ ] All tests pass (`pytest -m "not integration"`)
- [ ] No broken imports or syntax errors
- [ ] Changes verified to work
- [ ] No temporary files, debug code, or commented-out code
- [ ] Documentation updated (existing files only)
- [ ] ROADMAP.md "Current Status" updated if status changed
- [ ] Temporary files removed from `docs/temp/`
- [ ] `make sync-prompts` run if prompt templates modified

## Commit and PR instructions

**CRITICAL: DO NOT commit changes unless explicitly requested by the user.**

#### When to Commit

- ❌ **NEVER commit automatically** - Only commit when the user explicitly asks you to
- ✅ **ONLY commit when requested** - Wait for explicit instructions like "commit these changes" or "commit your work"
- ✅ **ONLY commit complete work** - Verify all changes are finished, tested, and working before committing
- ✅ **Ask for confirmation** if the commit would affect many files or is potentially destructive
- ❌ **DO NOT commit incomplete work** - If changes are not complete, inform the user and do not commit

#### Commit organization

**Break changes into logical, atomic commits:** One commit per feature/logical change. Separate commits for code, tests, and documentation. Avoid monolithic commits.

#### Commit message format

**Format:** `<type>: <subject>` with optional body.

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`, `chore`

**Guidelines:** Imperative mood, <72 chars, capitalize first letter, no period. Examples: `feat: add MIDI quality validation`, `fix: correct pattern matching algorithm`.

#### Commit workflow

**When user requests commits:**
1. Verify completeness (use "Before completing task" checklist)
2. Review changes: `git status` and `git diff`
3. Exclude incomplete work (no TODOs, failing tests, syntax errors, temp files, debug code)
4. Group logically: One commit per feature/logical change
5. Create atomic commits: `git add <files>` then `git commit -m "<type>: <message>"`
6. Verify: `git log --oneline -5`
7. Inform user: List commits, summarize contents, note any uncommitted files and why

## Common tasks

**Adding CLI command:** Create `src/pianist/cli/commands/<command>.py`, register in `src/pianist/cli/main.py`, write tests `tests/test_cli_<command>.py`, document in `docs/commands/<command>.md`, update README.md and ROADMAP.md.

**Adding module:** Create `src/pianist/<module>.py`, write tests `tests/test_<module>.py`, add to `src/pianist/__init__.py` if public API, document, update ROADMAP.md.

**Updating status:** Always update `ROADMAP.md` "Current Status" section (single source of truth). Never create separate status documents.

## Resources

- **Mission:** `MISSION.md`
- **Roadmap:** `ROADMAP.md` (single source of truth)
- **Planning:** `PLANNING.md`
- **User Guide:** `README.md`
- **AI Prompting:** `AI_PROMPTING_GUIDE.md`

