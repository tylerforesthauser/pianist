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

### Documentation Consolidation Rules

**CRITICAL: Consolidate related documentation into single documents. DO NOT create multiple files for the same topic.**

#### Planning Documents

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

#### Technical Documentation

**When documenting technical work (optimizations, refactorings, implementations):**

1. **Consolidate related documentation** - Create ONE comprehensive document per topic, not multiple files
   - Example: Instead of creating `analysis.md`, `analysis_implementation.md`, `analysis_validation.md`, create `analysis.md` with all sections
   - Use sections within a single document to organize content

2. **Use `docs/temp/` for work-in-progress** - If you need multiple drafts or working documents:
   - Create them in `docs/temp/` during development
   - Consolidate into final document in appropriate location (`docs/technical/`, `docs/guides/`, etc.)
   - Delete temporary files when done

3. **Update existing documents when possible** - Before creating new documentation:
   - Check if an existing document covers the topic
   - Update existing document instead of creating new one
   - Only create new documents for genuinely new topics

**Examples of what NOT to do:**
- ❌ Creating `topic_analysis.md`, `topic_implementation.md`, `topic_validation.md`, `topic_summary.md` for one feature
- ❌ Creating separate status documents instead of updating ROADMAP.md
- ❌ Creating multiple planning documents for the same work

**Examples of what TO do:**
- ✅ Create `topic.md` with sections: Analysis, Implementation, Validation, Summary
- ✅ Update ROADMAP.md for status changes
- ✅ Use `docs/temp/` for drafts, then consolidate into final document

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

1. **Create a feature branch** (if using git)
2. **Ensure package is installed** (if you encounter import errors):
   ```bash
   source .venv/bin/activate
   pip install -e . --force-reinstall --no-deps
   ```
3. **Implement changes** following code quality guidelines
4. **Write/update tests** to maintain coverage
5. **Update documentation** to reflect changes
6. **Run tests** to ensure everything passes

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


