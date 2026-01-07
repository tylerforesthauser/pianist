# CLI Refactoring

The CLI has been refactored from a single `cli.py` file into a modular package structure:

```
src/pianist/cli/
├── __init__.py          # Package exports and backward compatibility
├── main.py              # Main entry point with argument parsing
├── util.py              # Shared utilities
└── commands/            # Individual command handlers
    ├── render.py
    ├── import_.py
    ├── modify.py
    ├── fix.py
    └── diff.py
```

## Backward Compatibility

All public APIs are maintained:
- `python -m pianist` continues to work
- `from pianist.cli import main` works
- Utility functions are re-exported with underscore prefixes (e.g., `_read_text`, `_write_text`)

## Legacy Commands

The following commands still use the original implementation from `cli_legacy.py`:
- `annotate`
- `expand`
- `analyze`
- `generate`
- `reference`

These can be refactored incrementally in future PRs.

## Testing Notes

### Test Mocking

Due to the module structure, tests that mock AI functions need to update their mock targets:

**Before (when all code was in one file):**
```python
monkeypatch.setattr("pianist.cli.generate_text", fake_function)
```

**After (with refactored structure):**
```python
# Mock at the source module where it's actually imported from
monkeypatch.setattr("pianist.ai_providers.generate_text", fake_function)
```

This is a standard Python behavior - mocking needs to happen where the function is looked up, not where it's re-exported.

### Test Status

- ✅ All non-AI tests passing (render, import, basic modify, fix, diff)
- ⚠️ AI-provider tests need mock location updates (see above)
- ✅ Smoke tests for refactored structure passing
- ✅ Entry points working correctly

## Benefits

1. **Maintainability**: Each command is in its own file (~100-250 lines vs 2460 lines)
2. **Testability**: Commands can be unit tested in isolation
3. **Extensibility**: Easy to add new commands
4. **Code Organization**: Clear separation of concerns
5. **Backward Compatible**: No breaking changes to public APIs
