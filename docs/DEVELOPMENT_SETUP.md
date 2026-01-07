# Development Setup

This document describes the development environment setup for the Pianist project.

## Virtual Environment

**This project uses a Python virtual environment (`.venv`) for dependency management.**

### Setup

1. **Create virtual environment** (if it doesn't exist):
   ```bash
   python3 -m venv .venv
   ```

2. **Activate virtual environment**:
   ```bash
   # On macOS/Linux:
   source .venv/bin/activate
   
   # On Windows:
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   # Install in development mode with all optional dependencies
   pip install -e ".[dev,gemini,dotenv]"
   ```

### Important Notes

- **Always activate the virtual environment** before running scripts or commands
- The project uses `.venv` as the virtual environment directory (not `venv`)
- All Python scripts should be run with the virtual environment activated
- Dependencies like `music21` are installed in the virtual environment

### Verifying Setup

Check that the virtual environment is active and dependencies are installed:

```bash
# Should show .venv in the path
which python

# Should show music21 is available
python -c "import music21; print('music21 available')"

# Should show pianist is installed
python -c "import pianist; print('pianist available')"
```

### Running Scripts

All scripts in the `scripts/` directory should be run with the virtual environment activated:

```bash
# Activate venv first
source .venv/bin/activate

# Then run scripts
python3 scripts/check_midi_quality.py --dir input/
python3 scripts/batch_import_references.py --dir references/
```

### Troubleshooting

**Issue:** "music21 not available" or "ModuleNotFoundError: No module named 'music21'"

**Solution:** 
1. Make sure virtual environment is activated: `source .venv/bin/activate`
2. Install dependencies: `pip install -e ".[dev]"`
3. Verify: `python -c "import music21; print('OK')"`

**Issue:** Scripts can't find pianist modules

**Solution:**
1. Make sure virtual environment is activated
2. Install in development mode: `pip install -e ".[dev]"`
3. Scripts automatically add `src/` to path, but venv must be active

## See Also

- [README.md](../README.md) - Main project documentation
- [docs/guides/REFERENCE_DATABASE_CURATION.md](guides/REFERENCE_DATABASE_CURATION.md) - Reference database setup

