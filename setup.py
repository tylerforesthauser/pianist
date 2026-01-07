"""Setup configuration for pianist package.

This file customizes the entry point script generation to ensure .pth files
are processed before importing the package, fixing issues with editable installs.
"""
from __future__ import annotations

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from pathlib import Path


def fix_entry_point_script(script_path: Path) -> None:
    """Fix the entry point script to process .pth files before importing."""
    if not script_path.exists():
        return
    
    content = script_path.read_text()
    
    # Check if already fixed
    if "site.main()" in content and "# Process .pth files" in content:
        return
    
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


class PostInstallMixin:
    """Mixin to fix entry point scripts after installation."""
    
    def run(self) -> None:
        """Run the install/develop command and fix entry point scripts."""
        super().run()
        
        # Find and fix the entry point script
        # Try multiple possible locations
        import sysconfig
        scripts_dir = Path(sysconfig.get_path("scripts"))
        entry_script = scripts_dir / "pianist"
        
        # Also check common venv locations
        if not entry_script.exists():
            # Try to find it in the current venv
            import sys
            venv_bin = Path(sys.prefix) / "bin" / "pianist"
            if venv_bin.exists():
                entry_script = venv_bin
        
        fix_entry_point_script(entry_script)


class DevelopCommand(PostInstallMixin, develop):
    """Custom develop command that fixes entry point scripts."""
    pass


class InstallCommand(PostInstallMixin, install):
    """Custom install command that fixes entry point scripts."""
    pass


# When using pyproject.toml, setuptools reads metadata from there
# We only need to customize the install commands
# Note: When using setuptools.build_meta, setup.py is NOT executed automatically
# The custom commands only work when setup.py is invoked directly or via legacy backend
if __name__ == "__main__":
    setup(
        cmdclass={
            "develop": DevelopCommand,
            "install": InstallCommand,
        }
    )
else:
    # When imported by setuptools.build_meta, we need to register the commands differently
    # Use setuptools.setup_requires or a hook to ensure our commands are used
    # For now, we rely on the fix_entry_point.py script to be run manually
    pass
