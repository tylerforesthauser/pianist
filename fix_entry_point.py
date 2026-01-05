#!/usr/bin/env python3
"""Fix the entry point script to ensure .pth files are processed for editable installs.

This fixes an issue where Python 3.14 doesn't process .pth files correctly
when running entry point scripts, causing ModuleNotFoundError.

Run this after installing the package in editable mode:
    python3 fix_entry_point.py
"""
from __future__ import annotations

import sys
from pathlib import Path


def fix_entry_point():
    """Fix the entry point script to ensure .pth files are processed."""
    if sys.prefix == sys.base_prefix:
        print("Not in a virtual environment. Skipping fix.")
        return False

    venv_bin = Path(sys.prefix) / "bin" / "pianist"
    if not venv_bin.exists():
        print(f"Entry point script not found: {venv_bin}")
        return False

    content = venv_bin.read_text()
    
    # Check if already fixed
    if "site.main()" in content:
        print("Entry point script already fixed.")
        return True
    
    # Fix the entry point script - handle both patterns
    fixed = False
    if "from pianist.cli import main" in content:
        # Replace the import section with site.main() call and then import
        new_content = content.replace(
            "import sys\nfrom pianist.cli import main",
            "import sys\nimport site\n\n# Ensure .pth files are processed for editable installs\nsite.main()\n\nfrom pianist.cli import main"
        )
        venv_bin.write_text(new_content)
        print(f"Fixed entry point script: {venv_bin}")
        fixed = True
    elif "from pianist._entry import main" in content:
        # Handle old pattern that might still be cached
        new_content = content.replace(
            "import sys\nfrom pianist._entry import main",
            "import sys\nimport site\n\n# Ensure .pth files are processed for editable installs\nsite.main()\n\nfrom pianist.cli import main"
        )
        venv_bin.write_text(new_content)
        print(f"Fixed entry point script (updated import): {venv_bin}")
        fixed = True
    
    if not fixed:
        # Try a more general fix - add site.main() after the first import sys
        if "import sys" in content and "site.main()" not in content:
            new_content = content.replace(
                "import sys",
                "import sys\nimport site\n\n# Ensure .pth files are processed for editable installs\nsite.main()"
            )
            venv_bin.write_text(new_content)
            print(f"Fixed entry point script (general fix): {venv_bin}")
            fixed = True
    
    if not fixed:
        print("Could not find expected import pattern in entry point script.")
        print(f"Script content:\n{content}")
        return False
    
    return True


if __name__ == "__main__":
    success = fix_entry_point()
    sys.exit(0 if success else 1)

