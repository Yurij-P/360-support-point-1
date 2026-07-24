.PHONY: install test lint typecheck run

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	python -m ruff check .

typecheck:
	python -m mypy platform

run:
	python -m uvicorn platform.api.main:app --reload
