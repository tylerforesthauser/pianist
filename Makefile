.PHONY: sync-prompts check-prompts

sync-prompts:
	python3 scripts/sync_prompts_to_guide.py

check-prompts:
	python3 scripts/sync_prompts_to_guide.py --check


