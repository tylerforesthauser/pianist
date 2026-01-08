# Agent Instructions for Pianist Project

This document provides instructions for AI agents working on the Pianist project. It focuses on development guidelines, file organization, and workflow rules.

**For project mission, goals, and principles:** See [`MISSION.md`](MISSION.md)  
**For current status, progress, and priorities:** See [`ROADMAP.md`](ROADMAP.md) (single source of truth)

## Quick Reference: Most Critical Rules

**Before completing ANY task, ensure:**
1. ✅ Run tests: `source .venv/bin/activate && pytest -m "not integration"`
2. ✅ Update existing docs, don't create new files
3. ✅ Update ROADMAP.md "Current Status" if status changed
4. ✅ Remove temporary files from `docs/temp/`
5. ✅ Activate venv before Python commands: `source .venv/bin/activate`

**Common mistakes to avoid:**
- ❌ Creating new documentation files (update existing ones instead)
- ❌ Not running tests before completing tasks
- ❌ Creating separate status documents (update ROADMAP.md instead)
- ❌ Running integration tests automatically (they require API keys)
- ❌ Committing changes automatically (only commit when explicitly asked)
- ❌ Committing incomplete work (verify all changes are complete and tested first)

## Critical Rules: Command Execution and Documentation

**⚠️ READ THIS FIRST: These rules are frequently ignored. Follow them strictly.**

### Command Execution Rules

**When to RUN commands:**
- ✅ Run tests before completing a task: `source .venv/bin/activate && pytest -m "not integration"`
- ✅ Run linting/formatting when making code changes
- ✅ Run `make sync-prompts` after modifying prompt templates
- ✅ Run `pianist --version` to verify installation after setup changes
- ✅ Run commands to verify your changes work as expected

**When to SUGGEST commands (don't run automatically):**
- ⚠️ Long-running commands (integration tests, full test suites)
- ⚠️ Destructive operations (deletes, overwrites without confirmation)
- ⚠️ Commands that require user input or API keys not available to the agent
- ⚠️ **Git commits** - NEVER commit automatically, only when explicitly requested

**Always:**
- Activate virtual environment before running Python commands: `source .venv/bin/activate`
- Run tests after making code changes
- Verify commands succeed before proceeding
- **Never commit changes** unless the user explicitly asks you to

### Documentation Management Rules

**CRITICAL: DO NOT create new documentation files unless explicitly requested.**

**Rules:**
1. ✅ **Update existing files** - Check if documentation already exists before creating new files
2. ✅ **Consolidate related docs** - Use sections within existing documents, not separate files
3. ✅ **Update ROADMAP.md** - Always update "Current Status" section, never create separate status docs
4. ✅ **Use `docs/temp/`** - For work-in-progress docs that will be consolidated later
5. ✅ **Remove temp files** - Clean up `docs/temp/` when work is complete

**What NOT to do:**
- ❌ Create multiple files for the same topic (e.g., `analysis.md`, `analysis_impl.md`, `analysis_test.md`)
- ❌ Create separate status documents - always update ROADMAP.md
- ❌ Create new planning documents - use existing ones (ROADMAP.md, MISSION.md, PLANNING.md)

**Documentation update checklist (after code changes):**
- [ ] Updated command docs (`docs/commands/`) if CLI changed
- [ ] Updated workflow docs (`docs/workflows/`) if workflows changed
- [ ] Updated ROADMAP.md "Current Status" if status changed
- [ ] Updated README.md if user-facing features changed
- [ ] Ran `make sync-prompts` if prompt templates changed
- [ ] Removed temporary files from `docs/temp/`

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

**IMPORTANT: Always run tests after making code changes.**

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all unit tests (excludes integration tests)
# ✅ RUN THIS after code changes - it's fast and doesn't require API keys
pytest -m "not integration"

# Run only integration tests (requires API key)
# ⚠️ SUGGEST this to the user, but don't run automatically
pytest -m integration

# Run all tests
# ⚠️ Only run if user explicitly requests it
pytest
```

**Test execution rules:**
- ✅ **Always run** unit tests (`pytest -m "not integration"`) after code changes
- ⚠️ **Suggest, don't run** integration tests automatically (they require API keys and may be slow)
- ✅ **Run tests** before completing any coding task
- ✅ **Fix failing tests** before proceeding with other work

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

### Performance and Efficiency Guidelines

**CRITICAL: Avoid inefficient algorithms and redundant computations that can cause significant performance degradation.**

#### Algorithm Complexity Awareness

1. **Avoid O(n²) or worse algorithms when O(n) or O(n log n) alternatives exist**
   - When comparing elements, use hash-based grouping, sorting, or indexing instead of nested loops
   - Example: Pattern matching should use hash tables or tries, not nested loops comparing every element with every other element
   - If you must use O(n²), document why and consider optimization

2. **Use appropriate data structures**
   - Hash tables/dictionaries for O(1) lookups
   - Sets for membership testing
   - Sorted data structures when order matters
   - Avoid repeated linear searches when hash lookups are possible

3. **Consider input size**
   - For small inputs (<100 items), simple algorithms are fine
   - For larger inputs, optimize early - don't wait for performance problems
   - When processing MIDI files or musical data, assume potentially large inputs (thousands of notes)

#### Avoid Redundant Computations

1. **Functions should accept pre-computed results as optional parameters**
   ```python
   # ❌ BAD: Function always recomputes
   def analyze_composition(composition):
       motifs = detect_motifs(composition)  # Always recomputes
       phrases = detect_phrases(composition)  # Always recomputes
   
   # ✅ GOOD: Function accepts pre-computed results
   def analyze_composition(composition, motifs=None, phrases=None):
       if motifs is None:
           motifs = detect_motifs(composition)
       if phrases is None:
           phrases = detect_phrases(composition)
   ```

2. **Pass results between functions instead of recomputing**
   - When one function calls another that needs the same data, pass it as a parameter
   - Cache expensive computations and reuse them
   - Don't call the same expensive function multiple times with the same inputs

3. **Reuse expensive objects**
   - If converting data structures is expensive (e.g., music21 streams), convert once and pass the result
   - Don't recreate the same object multiple times in a call chain

#### Performance Best Practices

1. **Profile before optimizing**
   - Use timing measurements (`time.time()`) or profiling tools to identify actual bottlenecks
   - Don't optimize code that's already fast enough
   - Focus optimization efforts on the slowest parts

2. **Test with realistic data sizes**
   - Test algorithms with files similar to production use cases
   - Large MIDI files (1000+ notes, 10+ minutes) should complete in seconds, not minutes
   - If processing takes >10 seconds for typical inputs, investigate optimization

3. **Consider memory vs. speed tradeoffs**
   - Hash-based algorithms may use more memory but are much faster
   - For large datasets, prefer algorithms that scale well (O(n) or O(n log n)))

4. **Code review checklist for performance**
   - [ ] Are there nested loops that could be replaced with hash-based lookups?
   - [ ] Are functions recomputing the same values multiple times?
   - [ ] Are expensive conversions (e.g., MIDI → music21) happening multiple times?
   - [ ] Could results be passed between functions instead of recomputed?
   - [ ] Is the algorithm complexity appropriate for expected input sizes?

#### When to Optimize

- **Optimize immediately if:**
  - Algorithm is O(n²) or worse and O(n) alternative exists
  - Same computation is performed multiple times in a call chain
  - Processing takes >10 seconds for typical inputs

- **Don't optimize if:**
  - Code is already fast enough (<1 second for typical inputs)
  - Optimization would significantly harm readability
  - Premature optimization without profiling data

#### Examples from Past Issues

**Example 1: O(n²) Pattern Matching (Fixed)**
- **Problem**: Motif detection used nested loops comparing every pattern with every other pattern
- **Solution**: Hash-based grouping reduced complexity from O(n²) to O(n)
- **Result**: 98.93s → 0.09s (1099x speedup)

**Example 2: Redundant Function Calls (Fixed)**
- **Problem**: `identify_key_ideas()` and `generate_expansion_strategies()` recomputed all analysis
- **Solution**: Functions now accept pre-computed results as optional parameters
- **Result**: Eliminated ~200s of redundant computation

**Example 3: Redundant Quality Check (Fixed)**
- **Problem**: Quality check recomputed full analysis instead of reusing existing results
- **Solution**: Quality check now accepts pre-computed analysis as parameter
- **Result**: Eliminated 305s redundant analysis

### Development Mode

**The project is currently in active development with no external users or production deployments.**

- **No backwards compatibility requirements:** Breaking changes are acceptable when they improve code quality, maintainability, or align with the project roadmap
- **Focus on efficiency:** Prioritize clean, maintainable code over preserving existing interfaces
- **Refactor freely:** Don't hesitate to restructure code, rename functions, or change APIs if it makes the codebase better
- **Roadmap-driven:** Changes should align with the project roadmap and current development priorities

This approach allows for rapid iteration and keeps the codebase lean without the overhead of maintaining deprecated APIs or migration paths.

## Development Workflow

**Quick Start:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install/update package in editable mode
pip install -e . --force-reinstall --no-deps

# Fix entry point script (required after installation)
# Note: This is needed because pyproject.toml + setuptools.build_meta doesn't
# execute setup.py's custom commands, so the entry point script needs manual fixing
python scripts/fix_entry_point.py

# Verify installation
pianist --version
```

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

### Troubleshooting Module Import Errors

If you encounter `ModuleNotFoundError: No module named 'pianist'` when running commands:

1. **Ensure the virtual environment is activated:**
   ```bash
   source .venv/bin/activate
   ```

2. **Install/update the package in editable mode:**
   ```bash
   pip install -e . --force-reinstall --no-deps
   ```

3. **Fix the entry point script (required after installation):**
   ```bash
   python scripts/fix_entry_point.py
   ```
   
   This ensures the `pianist` command properly processes `.pth` files for editable installs.
   
   **Why this is needed:** When using `pyproject.toml` with `setuptools.build_meta`, 
   setuptools reads metadata from `pyproject.toml` and doesn't execute `setup.py`'s 
   custom command classes. This means the automatic fix in `setup.py` never runs. 
   The manual fix script ensures the entry point script processes `.pth` files correctly 
   (especially important in Python 3.14+).

4. **Verify the installation:**
   ```bash
   pianist --version
   ```
   
   The `pianist` command should work. For direct Python imports, use:
   ```bash
   python -c "import site; site.main(); import pianist; print('✓ OK')"
   ```
   
   Or add the path manually:
   ```bash
   python -c "import sys; sys.path.insert(0, 'src'); import pianist; print('✓ OK')"
   ```

5. **If issues persist, check the `.pth` file:**
   ```bash
   cat .venv/lib/python*/site-packages/__editable__.pianist-*.pth
   ```
   
   It should contain the path to the `src` directory.

**Note:** 
- The `pianist` command should work after running `fix_entry_point.py`
- Direct Python imports (`python -c "import pianist"`) may not work because `.pth` files are only processed during Python startup, not in every session
- Use the `pianist` command for CLI operations, or manually process `.pth` files for direct imports
- After making code changes, you typically don't need to reinstall (that's the benefit of editable installs)

### Making Changes

**Follow these steps in order, running commands as specified:**

1. **Create a feature branch** (if using git)

2. **Ensure package is installed** (if you encounter import errors):
   ```bash
   source .venv/bin/activate
   pip install -e . --force-reinstall --no-deps
   python scripts/fix_entry_point.py
   pianist --version  # Verify installation
   ```

3. **Implement changes** following code quality guidelines
   - Follow PEP 8 style guidelines
   - Use type hints for function signatures
   - Keep functions focused and single-purpose

4. **Write/update tests** to maintain coverage
   - Add tests for new functionality
   - Update existing tests if behavior changes

5. **Run tests** (REQUIRED - don't skip this):
   ```bash
   source .venv/bin/activate
   pytest -m "not integration"
   ```
   - Fix any failing tests before proceeding

6. **Update documentation** to reflect changes
   - Update existing docs, don't create new files
   - Update ROADMAP.md if status changed
   - Run `make sync-prompts` if prompt templates changed

7. **Verify everything works**:
   ```bash
   pianist --version  # Should work without errors
   ```

### Before Committing

**ALWAYS run these commands before completing a task:**

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run unit tests (excludes integration tests that require API keys)
pytest -m "not integration"

# 3. Check for linting issues (if linter is configured)
# Run any project-specific linting commands here

# 4. Verify the package still works
pianist --version
```

**Completeness verification (required before ANY commit):**
- [ ] All code changes are finished (no TODOs, placeholders, or incomplete implementations)
- [ ] All tests pass (`pytest -m "not integration"`)
- [ ] All related tests are written and passing
- [ ] No broken imports or syntax errors
- [ ] Changes have been verified to work
- [ ] No temporary files, debug code, or commented-out code included

**Documentation checklist:**
- [ ] All tests pass (`pytest -m "not integration"`)
- [ ] Documentation is up-to-date (see "Keeping Documentation Up-to-Date" section)
- [ ] ROADMAP.md "Current Status" section updated (if status changed)
- [ ] Temporary documents removed from `docs/temp/`
- [ ] Code follows style guidelines
- [ ] No new planning documents created (use existing ones)
- [ ] Ran `make sync-prompts` if prompt templates were modified

### Git Commit Rules

**CRITICAL: DO NOT commit changes unless explicitly requested by the user.**

#### When to Commit

- ❌ **NEVER commit automatically** - Only commit when the user explicitly asks you to
- ✅ **ONLY commit when requested** - Wait for explicit instructions like "commit these changes" or "commit your work"
- ✅ **ONLY commit complete work** - Verify all changes are finished, tested, and working before committing
- ✅ **Ask for confirmation** if the commit would affect many files or is potentially destructive
- ❌ **DO NOT commit incomplete work** - If changes are not complete, inform the user and do not commit

#### Commit Organization

**When committing, break changes into logical, atomic commits:**

1. **Group related changes together:**
   - One commit per feature or logical change
   - Separate commits for code changes, tests, and documentation
   - Keep commits focused and single-purpose

2. **Example of good commit grouping:**
   ```bash
   # Commit 1: Core feature implementation
   git add src/pianist/new_feature.py
   git commit -m "feat: add new feature for X"
   
   # Commit 2: Tests for the feature
   git add tests/test_new_feature.py
   git commit -m "test: add tests for new feature"
   
   # Commit 3: Documentation updates
   git add docs/commands/new_feature.md ROADMAP.md
   git commit -m "docs: update documentation for new feature"
   ```

3. **Avoid monolithic commits:**
   - ❌ DON'T: One commit with all changes mixed together
   - ✅ DO: Separate commits for different logical changes

#### Commit Message Format

**Use consistent, descriptive commit messages following this format:**

```
<type>: <subject>

<optional body>
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

**Examples:**
```bash
# Feature addition
git commit -m "feat: add MIDI quality validation to analyze command"

# Bug fix
git commit -m "fix: correct pattern matching algorithm for large files"

# Documentation
git commit -m "docs: update ROADMAP.md with current status"

# Test addition
git commit -m "test: add integration tests for expand command"

# Multiple related changes (use body for details)
git commit -m "refactor: optimize analysis performance

- Replace O(n²) pattern matching with hash-based approach
- Add caching for expensive music21 conversions
- Update tests to verify performance improvements"
```

**Commit message guidelines:**
- Use imperative mood ("add" not "added" or "adds")
- Keep subject line under 72 characters
- Capitalize first letter of subject
- No period at end of subject line
- Use body for detailed explanations when needed
- Reference related issues/PRs if applicable

#### Commit Workflow

**When the user requests commits:**

1. **Verify changes are complete** - DO NOT commit incomplete work:
   - ✅ All code changes are finished (no TODOs, placeholders, or incomplete implementations)
   - ✅ All tests pass (`pytest -m "not integration"`)
   - ✅ All related tests are written and passing
   - ✅ Documentation is updated (if needed)
   - ✅ Code follows style guidelines
   - ✅ No broken imports or syntax errors
   - ✅ Changes have been verified to work (e.g., `pianist --version` succeeds)

2. **Review all changes:**
   ```bash
   git status
   git diff
   ```

3. **Exclude incomplete work:**
   - ❌ **DO NOT commit** files with TODOs, FIXMEs, or incomplete implementations
   - ❌ **DO NOT commit** files with failing tests
   - ❌ **DO NOT commit** files with syntax errors or broken imports
   - ❌ **DO NOT commit** temporary files, debug code, or commented-out code
   - ✅ **ONLY commit** complete, tested, and verified changes

4. **Group changes logically** - Identify which files belong together

5. **Create atomic commits** - One commit per logical group:
   ```bash
   # Stage related files
   git add <files-for-commit-1>
   git commit -m "<type>: <descriptive message>"
   
   # Repeat for each logical group
   git add <files-for-commit-2>
   git commit -m "<type>: <descriptive message>"
   ```

6. **Verify commits:**
   ```bash
   git log --oneline -5  # Review recent commits
   ```

7. **Inform the user** about what was committed:
   - List the commits created
   - Summarize what each commit contains
   - Note if any files were left uncommitted (and why)
   - If incomplete work exists, clearly state what was NOT committed and why

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

