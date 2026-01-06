# Prompt Sync (Source of Truth)

Pianist’s **model-facing system prompts** are stored as prompt assets under:
- `src/pianist/prompts/system_prompt_full.txt`
- `src/pianist/prompts/system_prompt_short.txt`

`AI_PROMPTING_GUIDE.md` embeds these prompts between markers and is kept in sync automatically.

## Developer workflow

- Update prompt text in `src/pianist/prompts/*.txt`
- Sync into the guide:

```bash
make sync-prompts
```

- Verify no drift (used in CI):

```bash
make check-prompts
```

## CI

GitHub Actions runs `python3 scripts/sync_prompts_to_guide.py --check` on PRs to prevent drift.


