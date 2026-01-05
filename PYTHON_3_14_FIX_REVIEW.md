# Python 3.14+ Fix Review

## Current Implementation Analysis

### What the Fix Does
The current `fix_entry_point.py` script modifies the generated entry point script (typically at `venv/bin/pianist`) to call `site.main()` before importing the module. This ensures that `.pth` files (used for editable installs) are processed correctly.

### Issues with Current Approach

1. **Fragility**: Modifying generated files is brittle
   - If setuptools changes the format of generated entry point scripts, the fix may break
   - The script has multiple fallback patterns, indicating uncertainty about script format
   - Generated files can be overwritten by package reinstalls

2. **Manual Step Required**: Users must remember to run the fix after installation
   - Easy to forget
   - Not integrated into the installation process
   - Creates friction for new users

3. **Not a Proper Solution**: This is a workaround, not addressing the root cause
   - The issue likely lies in how setuptools generates entry points in Python 3.14
   - Modifying generated files is a band-aid solution

4. **Potential Side Effects**: 
   - `site.main()` may have unintended side effects if called multiple times
   - Could interfere with other site customization

## Recommended Solutions

### Option 1: Entry Point Wrapper (RECOMMENDED)

Create a wrapper module that handles the `site.main()` call internally:

**Create `src/pianist/_entry.py`:**
```python
"""Entry point wrapper for Python 3.14+ compatibility."""
from __future__ import annotations

import site
import sys

# Ensure .pth files are processed for editable installs (Python 3.14+ fix)
# This must be called before importing the main module
if sys.version_info >= (3, 14):
    site.main()

from pianist.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

**Update `pyproject.toml`:**
```toml
[project.scripts]
pianist = "pianist._entry:main"
```

**Pros:**
- ✅ No post-installation step required
- ✅ Works automatically for all users
- ✅ Version-specific (only applies to Python 3.14+)
- ✅ Doesn't modify generated files
- ✅ More maintainable and reliable

**Cons:**
- ⚠️ Adds an extra module file
- ⚠️ Requires version check (though this is good practice)

### Option 2: Conditional Import in CLI Module

Modify `cli.py` to handle this at the module level:

```python
# At the top of cli.py, before other imports
import sys
if sys.version_info >= (3, 14):
    import site
    site.main()
```

**Pros:**
- ✅ Simple, no extra files
- ✅ Automatic

**Cons:**
- ⚠️ Mixes concerns (CLI logic with installation fix)
- ⚠️ May process site files even when not needed (e.g., when imported as a module)

### Option 3: Keep Current Approach but Improve

If you want to keep the post-install fix approach:

1. **Make it automatic**: Add a `setup.py` or use `setuptools` hooks to run the fix automatically
2. **Add version check**: Only apply the fix for Python 3.14+
3. **Better error handling**: More robust pattern matching

**Pros:**
- ✅ Keeps entry point clean
- ✅ Can be removed once upstream fixes the issue

**Cons:**
- ⚠️ Still fragile
- ⚠️ Still requires manual or hook-based execution

## Recommendation

**Use Option 1 (Entry Point Wrapper)** because:
1. It's the most robust solution
2. No user intervention required
3. Version-specific, so it won't affect older Python versions
4. Follows Python packaging best practices
5. Can be easily removed once Python 3.14+ or setuptools fixes the underlying issue

## Additional Notes

- The root cause appears to be that Python 3.14 changed how entry point scripts are executed, and `.pth` file processing may not happen before imports
- This is likely a temporary issue that will be fixed upstream (either in Python or setuptools)
- Consider checking Python bug tracker and setuptools issues for official fixes
- The `site.main()` approach is correct for processing `.pth` files, but the timing/placement matters

## Testing Recommendations

1. Test with Python 3.14+ in editable mode
2. Test with Python 3.11-3.13 to ensure no regressions
3. Test with regular (non-editable) installs
4. Test with different virtual environment tools (venv, virtualenv, etc.)
