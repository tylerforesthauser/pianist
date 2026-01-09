.PHONY: sync-prompts check-prompts lint format type-check quality test-coverage install-pre-commit

sync-prompts:
	python3 scripts/sync_prompts_to_guide.py

check-prompts:
	python3 scripts/sync_prompts_to_guide.py --check

# Code quality targets
lint:
	ruff check src tests scripts

lint-fix:
	ruff check --fix src tests scripts

format:
	ruff format src tests scripts

format-check:
	ruff format --check src tests scripts

type-check:
	mypy src

quality: lint format-check type-check
	@echo "✓ All quality checks passed"

# Test targets (always run in parallel for faster execution)
test:
	pytest -m "not integration" -n auto

test-failed:
	pytest -m "not integration" -n auto --lf

test-coverage:
	pytest -m "not integration" -n auto --cov=src/pianist --cov-report=term-missing --cov-report=html

# Pre-commit hooks
install-pre-commit:
	pre-commit install

pre-commit-all:
	pre-commit run --all-files


