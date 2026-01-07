# Agent Instructions for Pianist Project

This document provides instructions for AI agents working on the Pianist project. It focuses on development guidelines, file organization, and workflow rules.

**For project mission, goals, and principles:** See [`MISSION.md`](MISSION.md)  
**For current status, progress, and priorities:** See [`ROADMAP.md`](ROADMAP.md) (single source of truth)

## Project Structure

### Directory Organization

**Source Code:**
- `src/pianist/` - Main Python source code
- `tests/` - Test files
- `tests/fixtures/` - Test data and fixtures
- `tests/analysis/` - Test analysis artifacts (from test scripts)

**Documentation:**
- `docs/commands/` - Individual command documentation
- `docs/workflows/` - End-to-end workflow guides
- `docs/guides/` - How-to guides
- `docs/technical/` - Technical deep dives
- `docs/reference/` - Reference materials
- `docs/temp/` - **Temporary/working documents** (gitignored, clean up when done)

**Planning & Status:**
- `MISSION.md` - Project mission and goals
- `ROADMAP.md` - **Single source of truth for project status and planning** (always update this, not separate status docs)
- `PLANNING.md` - Meta-document explaining planning structure

**User Files:**
- `input/` - User input files (MIDI, JSON compositions) - **gitignored**
- `output/` - Generated output files (organized by `<base-name>/<command>/`) - **gitignored**
  - `output/analysis/` - User-generated analysis output (prompts, analysis JSON)
- `references/` - **Reference database staging area** - Source files (MIDI, JSON, metadata CSV) before importing into the reference database
  - The actual reference database is SQLite stored in `~/.pianist/references.db`
  - Use `scripts/batch_import_references.py` to import files from `references/` into the database
- `examples/` - Example files for users

**Development:**
- `scripts/` - Utility scripts for development/maintenance
- `schemas/` - Schema definition files

**Configuration:**
- Root level: `pyproject.toml`, `setup.py`, `Makefile`, etc.

### File Naming and Organization Rules

1. **Output Files:** Always use the `output/` directory structure:
   - Pattern: `output/<base-name>/<command>/<filename>`
   - Base name derived from input file (without extension)
   - Command subdirectory prevents filename conflicts
   - Special subdirectories:
     - `output/analysis/` - For analysis outputs (prompts, analysis JSON)

2. **Test Files:** 
   - Test code: `tests/test_*.py`
   - Test fixtures: `tests/fixtures/`
   - Test output: `tests/analysis/` (for test scripts)

3. **Documentation:**
   - Command docs: `docs/commands/<command>.md`
   - Workflow docs: `docs/workflows/<workflow>.md`
   - Guides: `docs/guides/<topic>.md`
   - Technical: `docs/technical/<topic>.md`
   - Reference: `docs/reference/<topic>.md`

4. **Temporary Documents:**
   - Use `docs/temp/` for work-in-progress planning documents
   - Remove temporary documents when no longer needed
   - Do not create new markdown documents for every plan - consolidate into existing planning documents

5. **Scripts:**
   - Development/maintenance scripts: `scripts/<script_name>.py`
   - Make scripts executable and document their purpose

## Documentation Guidelines

### Planning Documents

**Keep planning documents minimal and consolidated:**

1. **`ROADMAP.md`** - **Single source of truth for project status and planning**
   - Always update the "Current Status" section when making status assessments
   - DO NOT create separate status documents
   - Consolidate all status updates here

2. **`MISSION.md`** - Project mission, goals, and principles
   - Update when goals change or after major milestones
   - Use for reassessing current state

3. **`PLANNING.md`** - Meta-document explaining planning structure
   - Explains how planning documents are organized
   - Points to other planning documents

**Rules:**
- **DO NOT create new markdown documents for every plan** - Use existing planning documents
- **DO NOT create separate status documents** - Update ROADMAP.md instead
- Use `docs/temp/` for temporary planning documents that will be consolidated or removed
- Remove temporary documents from `docs/temp/` when no longer needed

### Keeping Documentation Up-to-Date

**When implementing new features or refactoring code:**

1. **Update command documentation** (`docs/commands/`) when commands change
2. **Update workflow documentation** (`docs/workflows/`) when workflows change
3. **Update technical documentation** (`docs/technical/`) when implementation details change
4. **Update README.md** when user-facing features change
5. **Update ROADMAP.md** when status changes (always update "Current Status" section)
6. **Update AI_PROMPTING_GUIDE.md** when prompt templates change (use `make sync-prompts`)
7. **Update AGENTS.md** when development guidelines, file organization, or workflow rules change

**Documentation sync commands:**
- `make sync-prompts` - Sync prompt templates from `src/pianist/prompts/*.txt` to `AI_PROMPTING_GUIDE.md`
- `make check-prompts` - Verify prompt templates are in sync

## Testing Guidelines

### Test Coverage Requirements

**When implementing new features or refactoring code:**

1. **Write tests for new functionality:**
   - Unit tests for individual functions/modules
   - Integration tests for CLI commands (mark with `@pytest.mark.integration`)
   - Test fixtures in `tests/fixtures/` for test data

2. **Maintain acceptable test coverage:**
   - Aim for >80% coverage for new code
   - Ensure critical paths are well-tested
   - Test edge cases and error conditions

3. **Update existing tests when refactoring:**
   - Fix broken tests after refactoring
   - Update test expectations when behavior changes
   - Remove obsolete tests

### Test Organization

- **Unit tests:** `tests/test_<module>.py`
- **CLI tests:** `tests/test_cli_<command>.py`
- **Integration tests:** Mark with `@pytest.mark.integration`
- **Test fixtures:** `tests/fixtures/`

### Running Tests

```bash
# Run all unit tests (excludes integration tests)
pytest -m "not integration"

# Run only integration tests (requires API key)
pytest -m integration

# Run all tests
pytest
```

## Code Quality Guidelines

### Python Code Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Use Pydantic models for data validation
- Keep functions focused and single-purpose
- Write clear docstrings for public functions

### Module Organization

- Main source code: `src/pianist/`
- CLI commands: `src/pianist/cli/commands/`
- Core modules: `src/pianist/<module>.py`
- Renderers: `src/pianist/renderers/`
- Prompts: `src/pianist/prompts/`

### Dependencies

- Add dependencies to `pyproject.toml`
- Use optional dependencies for optional features (e.g., `[gemini]`, `[dev]`)
- Document dependencies in README.md
- Use virtual environment (`.venv`) for development

## Development Workflow

### Virtual Environment

This project uses a Python virtual environment (`.venv`) for dependency management:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install in development mode
python3 -m pip install -e ".[dev]"

# Install optional dependencies
python3 -m pip install -e ".[gemini,dotenv]"
```

**Always activate the virtual environment before running scripts or tests.**

### Making Changes

1. **Create a feature branch** (if using git)
2. **Implement changes** following code quality guidelines
3. **Write/update tests** to maintain coverage
4. **Update documentation** to reflect changes
5. **Run tests** to ensure everything passes

### Before Committing

- [ ] All tests pass (`pytest -m "not integration"`)
- [ ] Documentation is up-to-date (see "Keeping Documentation Up-to-Date" section)
- [ ] ROADMAP.md "Current Status" section updated (if status changed)
- [ ] Temporary documents removed from `docs/temp/`
- [ ] Code follows style guidelines
- [ ] No new planning documents created (use existing ones)

## Key Principles

See [`MISSION.md`](MISSION.md) for project principles and goals.

## Priority Areas

See [`ROADMAP.md`](ROADMAP.md) "Current Status" and "Next Steps" sections for current priorities and critical gaps.

## Common Tasks

### Adding a New CLI Command

1. Create command file: `src/pianist/cli/commands/<command>.py`
2. Register in `src/pianist/cli/main.py`
3. Write tests: `tests/test_cli_<command>.py`
4. Create documentation: `docs/commands/<command>.md`
5. Update README.md with command usage
6. Update ROADMAP.md "Current Status" section if status changes

### Adding a New Module

1. Create module: `src/pianist/<module>.py`
2. Write tests: `tests/test_<module>.py`
3. Add to `src/pianist/__init__.py` if it's part of public API
4. Document in appropriate `docs/` location
5. Update ROADMAP.md "Current Status" section if status changes

### Updating Status

**Always update `ROADMAP.md` "Current Status" section** (single source of truth):
- After completing features
- After making progress on features
- When priorities change
- When new gaps are identified
- **DO NOT create separate status documents**

## Resources

- **Mission:** `MISSION.md`
- **Roadmap:** `ROADMAP.md` (single source of truth for status)
- **Planning:** `PLANNING.md`
- **User Guide:** `README.md`
- **AI Prompting:** `AI_PROMPTING_GUIDE.md`
- **Development Setup:** `docs/DEVELOPMENT_SETUP.md`
- **Documentation Structure:** `docs/DOCUMENTATION_STRUCTURE.md`


