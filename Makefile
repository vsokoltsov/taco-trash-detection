.PHONY: test lint typecheck check fix

test:
	uv run pytest trash_annotation/tests/ -v

lint:
	uv run ruff check

typecheck:
	uv run ty check trash_annotation

check: lint typecheck test

fix:
	uv run ruff check --fix
	uv run ruff format
