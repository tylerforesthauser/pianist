#!/usr/bin/env python3
"""
Fix the entry point script to process .pth files correctly.

This script should be run after `pip install -e .` to ensure the entry point
script properly processes .pth files for editable installs.
"""
from __future__ import annotations

import sys
from pathlib import Path


def fix_entry_point_script(script_path: Path) -> bool:
    """Fix the entry point script to process .pth files before importing."""
    if not script_path.exists():
        print(f"Entry point script not found: {script_path}")
        return False
    
    content = script_path.read_text()
    
    # Check if already fixed
    if "site.main()" in content and "# Process .pth files" in content:
        print(f"Entry point script already fixed: {script_path}")
        return True
    
    # Find the import line and add site.main() before it
    import re
    
    # Pattern to match: import sys\nfrom pianist.entry import main
    pattern = r"^(import sys\n)(from pianist\.entry import main)$"
    
    replacement = r"""\1import site
from pathlib import Path

# Process .pth files for editable installs before importing
site.main()

# Manually process .pth files if needed (fallback for Python 3.14+)
venv_root = Path(__file__).parent.parent
site_packages = venv_root / "lib"
python_dirs = [d for d in site_packages.iterdir() if d.is_dir() and d.name.startswith("python")]
if python_dirs:
    pth_file = python_dirs[0] / "site-packages" / "__editable__.pianist-0.1.0.pth"
    if pth_file.exists():
        pth_path = pth_file.read_text().strip()
        if pth_path and Path(pth_path).exists() and str(pth_path) not in sys.path:
            sys.path.insert(0, str(pth_path))

\2"""
    
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content != content:
        script_path.write_text(new_content)
        script_path.chmod(0o755)
        print(f"Fixed entry point script: {script_path}")
        return True
    else:
        print(f"Could not find pattern to replace in: {script_path}")
        return False


def main() -> int:
    """Main entry point."""
    # Find the entry point script
    import sysconfig
    
    scripts_dir = Path(sysconfig.get_path("scripts"))
    entry_script = scripts_dir / "pianist"
    
    # Also check common venv locations
    if not entry_script.exists():
        # Try to find it in the current venv
        venv_bin = Path(sys.prefix) / "bin" / "pianist"
        if venv_bin.exists():
            entry_script = venv_bin
    
    if not entry_script.exists():
        print(f"Error: Could not find entry point script 'pianist'")
        print(f"  Checked: {scripts_dir / 'pianist'}")
        print(f"  Checked: {Path(sys.prefix) / 'bin' / 'pianist'}")
        return 1
    
    if fix_entry_point_script(entry_script):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

