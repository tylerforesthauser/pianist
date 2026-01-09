# Handling Style Suggestions

This guide explains how to handle linting style suggestions in the Pianist project.

## Quick Answer

**Most style suggestions can be auto-fixed!** You have three options:

1. **Auto-fix everything** (recommended for most cases)
2. **Configure preferences** (ignore rules you don't like)
3. **Manual review** (for important code)

## Auto-Fixable Rules

Most of the style suggestions you're seeing can be automatically fixed by Ruff:

- ✅ **SIM108** - Ternary operators (auto-fixable)
- ✅ **PIE810** - `startswith` optimization (auto-fixable)
- ✅ **SIM102** - Nested if statements (auto-fixable)
- ✅ **SIM103** - Return condition directly (auto-fixable)
- ✅ **SIM118** - Use `key in dict` (auto-fixable)
- ✅ **B905** - Add `strict=` to `zip()` (auto-fixable)
- ✅ **B904** - Exception chaining (auto-fixable)

## Option 1: Auto-Fix Everything (Recommended)

Simply run:

```bash
make lint-fix
```

This will automatically fix all auto-fixable style suggestions. Ruff is conservative and only makes safe changes.

**When to use:** Most of the time. Ruff's auto-fixes are safe and improve code quality.

## Option 2: Configure Your Preferences

If you disagree with certain style rules, you can disable them in `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
    # ... existing ignores ...
    "SIM108",  # Prefer explicit if/else over ternary operators
    "B905",    # Don't require strict= in zip()
]
```

**When to use:** When you have strong preferences that differ from Ruff's defaults.

### Common Preferences

- **SIM108 (Ternary operators)**: Some teams prefer explicit `if/else` for readability
- **B905 (zip strict)**: Only needed if you want strict length checking (Python 3.10+)
- **B904 (Exception chaining)**: Generally good practice, but can be verbose

## Option 3: Selective Auto-Fix

You can auto-fix only specific rules:

```bash
ruff check --fix --fixable SIM108,SIM102 src tests scripts
```

Or exclude certain rules from auto-fix:

```bash
ruff check --fix --unfixable SIM108 src tests scripts
```

## Option 4: Manual Review (For Important Code)

For critical code paths, you might want to review changes:

```bash
# See what would be fixed (without applying)
ruff check --diff src/pianist/quality.py

# Then apply if you're happy
ruff check --fix src/pianist/quality.py
```

## Recommended Workflow

1. **Run auto-fix regularly:**
   ```bash
   make lint-fix && make format
   ```

2. **Review the diff** if you're unsure about changes:
   ```bash
   git diff
   ```

3. **Configure preferences** for rules you consistently disagree with

4. **Use pre-commit hooks** to catch issues before commit:
   ```bash
   make install-pre-commit  # Already done!
   ```

## Current Configuration

We currently ignore:
- `E501` - Line length (handled by formatter)
- `B008` - Function calls in defaults
- `PLR0913`, `PLR0912`, `PLR0915` - Complexity metrics (allow for complex functions)
- `E402` - Imports not at top (scripts modify `sys.path` first)

## Decision Guide

**Auto-fix if:**
- ✅ The suggestion makes code cleaner
- ✅ You trust Ruff's judgment
- ✅ It's a simple style improvement

**Ignore the rule if:**
- ❌ You consistently disagree with it
- ❌ It makes code less readable in your opinion
- ❌ It conflicts with your team's style guide

**Manual review if:**
- ⚠️ The code is critical/complex
- ⚠️ You want to understand the change
- ⚠️ The auto-fix might change behavior (rare)

## Examples

### SIM108: Ternary Operator

**Before:**
```python
if default:
    full_prompt = f"{prompt} [{default}]: "
else:
    full_prompt = f"{prompt}: "
```

**After (auto-fixed):**
```python
full_prompt = f"{prompt} [{default}]: " if default else f"{prompt}: "
```

**Decision:** Auto-fix is fine. Ternary is more concise and Pythonic.

### B905: Zip Strict

**Before:**
```python
matches = sum(1 for a, b in zip(prog1, prog2) if a == b)
```

**After (auto-fixed):**
```python
matches = sum(1 for a, b in zip(prog1, prog2, strict=True) if a == b)
```

**Decision:** Auto-fix is good. `strict=True` prevents silent bugs from mismatched lengths.

### B904: Exception Chaining

**Before:**
```python
except ImportError:
    raise RuntimeError("requests library required")
```

**After (auto-fixed):**
```python
except ImportError as err:
    raise RuntimeError("requests library required") from err
```

**Decision:** Auto-fix is good. Preserves exception context for debugging.

## Summary

**For this project, I recommend:**

1. ✅ **Auto-fix everything** with `make lint-fix`
2. ✅ **Review the diff** to ensure changes look good
3. ✅ **Configure ignores** only for rules you strongly disagree with
4. ✅ **Let pre-commit hooks** catch issues automatically

The style suggestions are generally good improvements. Ruff's auto-fixes are safe and will make your code more Pythonic and maintainable.
