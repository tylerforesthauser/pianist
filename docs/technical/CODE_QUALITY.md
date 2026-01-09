# Code Quality Tools

This document describes the code quality tools and practices used in the Pianist project.

## Tools Overview

### Ruff
**Purpose:** Fast Python linter and formatter (replaces flake8, black, isort, etc.)

**Features:**
- Linting: Catches errors, unused imports, style issues
- Formatting: Auto-formats code to consistent style
- Speed: 10-100x faster than traditional tools
- Configuration: See `[tool.ruff]` in `pyproject.toml`

**Usage:**
```bash
make lint          # Check for issues
make lint-fix      # Auto-fix issues
make format        # Format code
make format-check  # Check formatting
```

### MyPy
**Purpose:** Static type checker for Python

**Features:**
- Type checking: Validates type hints
- Catches type-related bugs before runtime
- Configuration: See `[tool.mypy]` in `pyproject.toml`

**Usage:**
```bash
make type-check    # Run type checker
```

### Pre-commit Hooks
**Purpose:** Automatically run quality checks before commits

**Features:**
- Prevents committing code with issues
- Runs ruff, mypy, and file checks
- Configuration: `.pre-commit-config.yaml`

**Setup:**
```bash
make install-pre-commit    # Install hooks
make pre-commit-all        # Test all files
```

### Pytest Coverage
**Purpose:** Measure test coverage

**Features:**
- Shows which code is covered by tests
- Generates HTML reports
- Configuration: See `[tool.coverage.*]` in `pyproject.toml`

**Usage:**
```bash
make test-coverage    # Generate coverage report (HTML in htmlcov/)
```

## Quick Reference

### Before Committing
```bash
make quality          # Run all checks (lint, format-check, type-check)
make lint-fix         # Auto-fix linting issues
make format           # Format code
pytest -m "not integration"  # Run tests
```

### Complete Quality Check
```bash
make quality          # Lint, format-check, type-check
make test-coverage    # Coverage report
```

## Configuration Files

- `pyproject.toml` - Tool configurations (ruff, mypy, coverage, pytest)
- `.pre-commit-config.yaml` - Pre-commit hook definitions
- `Makefile` - Convenience commands

## What Gets Checked

### Ruff Checks
- **E/W**: PEP 8 style errors and warnings
- **F**: Pyflakes (unused imports, undefined names)
- **I**: Import sorting (isort)
- **N**: Naming conventions (PEP 8)
- **UP**: Code upgrades (pyupgrade)
- **B**: Bugbear (common bugs)
- **C4**: Comprehensions
- **SIM**: Simplifications
- **TCH**: Type checking imports
- **ARG**: Unused arguments
- **PL**: Pylint rules
- **RUF**: Ruff-specific rules

### MyPy Checks
- Type consistency
- Missing type annotations (when enabled)
- Incorrect type usage
- Unreachable code

### Pre-commit Checks
- Ruff linting and formatting
- MyPy type checking
- Trailing whitespace
- End of file newlines
- YAML/JSON/TOML validity
- Large file detection
- Merge conflict markers
- Debug statements

## Integration with Development Workflow

See `AGENTS.md` for the complete development workflow. Quality checks are integrated into the "Before completing task" checklist.

**CRITICAL:** All code changes must pass quality checks before being considered complete. This is enforced by:
- Pre-commit hooks (if installed)
- Mandatory `make quality` check in development workflow
- CI/CD integration (when configured)

## Current Status

**As of latest update:** All 294 initial linting issues have been resolved. The codebase maintains:
- ✅ Zero linting errors
- ✅ Consistent formatting
- ✅ Type checking enabled
- ✅ Pre-commit hooks configured

**Maintained standards:**
- All unused arguments prefixed with `_`
- All nested if statements combined where appropriate
- All unused imports removed
- All code simplifications applied (SIM rules)
- Type safety enforced where possible

## Troubleshooting

### Ruff Issues
- Most issues can be auto-fixed: `make lint-fix`
- Formatting issues: `make format`
- To ignore a specific rule, add it to `ignore` in `[tool.ruff]`

### MyPy Issues
- Third-party libraries without type stubs are ignored (see `[[tool.mypy.overrides]]`)
- To disable strict checking for a module, add it to overrides

### Pre-commit Issues
- Run manually: `pre-commit run --all-files`
- Skip hooks (not recommended): `git commit --no-verify`
