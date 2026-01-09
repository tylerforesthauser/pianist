"""Allow running pianist as a module: python -m pianist"""

from __future__ import annotations

import site
import sys
from pathlib import Path

# Ensure .pth files are processed
site.main()

# Manually process .pth files if needed (for -m flag compatibility)
try:
    import sysconfig

    site_packages = Path(sysconfig.get_path("purelib"))
    if site_packages.exists():
        pth_files = list(site_packages.glob("__editable__.*.pth"))
        for pth_file in pth_files:
            if "pianist" in pth_file.name:
                pth_path = pth_file.read_text().strip()
                if pth_path and Path(pth_path).exists() and str(pth_path) not in sys.path:
                    sys.path.insert(0, str(pth_path))
except Exception:
    pass

# Fallback: add src to path if needed
try:
    from .cli import main
except (ImportError, ModuleNotFoundError):
    # Find src directory
    this_file = Path(__file__).resolve()
    src_path = this_file.parent.parent
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
