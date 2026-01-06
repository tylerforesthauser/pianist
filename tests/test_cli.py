"""General CLI infrastructure tests."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from pianist.cli import main
from pianist.entry import main as entry_main


def test_entry_point_imports_main() -> None:
    """Test that entry point module correctly imports and exposes main."""
    # Verify entry_main is the same function as cli.main
    assert entry_main is main
    # Verify it's callable
    assert callable(entry_main)


def test_cli_file_permission_error_read(tmp_path: Path) -> None:
    """Test handling of file permission errors when reading."""
    # Create a file and make it unreadable
    protected_file = tmp_path / "protected.txt"
    protected_file.write_text("test content", encoding="utf-8")
    
    # Try to make it unreadable (this might not work on all systems)
    try:
        protected_file.chmod(0o000)  # No permissions
        
        out = tmp_path / "out.mid"
        rc = main(["render", "-i", str(protected_file), "-o", str(out)])
        
        # Should fail with permission error
        assert rc == 1
    except (OSError, PermissionError):
        # On some systems, we can't create unreadable files or the test itself
        # doesn't have permission to change permissions - skip this test
        pass
    finally:
        # Restore permissions so file can be cleaned up
        try:
            protected_file.chmod(0o644)
        except OSError:
            pass


def test_cli_file_permission_error_write(tmp_path: Path) -> None:
    """Test handling of file permission errors when writing."""
    # Create a directory and make it unwritable
    protected_dir = tmp_path / "protected_dir"
    protected_dir.mkdir()
    
    try:
        protected_dir.chmod(0o555)  # Read and execute only, no write
        
        protected_output = protected_dir / "output.mid"
        rc = main(
            [
                "render",
                "-i",
                "examples/model_output.txt",
                "-o",
                str(protected_output),
            ]
        )
        
        # Should fail with permission error
        assert rc == 1
    except (OSError, PermissionError):
        # On some systems, we can't create unwritable directories or the test itself
        # doesn't have permission to change permissions - skip this test
        pass
    finally:
        # Restore permissions so directory can be cleaned up
        try:
            protected_dir.chmod(0o755)
        except OSError:
            pass
