.PHONY: install lint format test docs demo check clean

install:
	python -m pip install -e '.[dev]'

lint:
	python -m ruff check .
	python -m ruff format --check .

format:
	python -m ruff check --fix .
	python -m ruff format .

test:
	python -m pytest

docs:
	python -m sphinx -W --keep-going -b html docs docs/_build/html

demo:
	python scripts/demo.py

check: lint test docs demo

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov docs/_build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
