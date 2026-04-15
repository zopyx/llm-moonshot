.PHONY: dist upload test lint fmt check cog clean install

PYPI_REPO ?= pypi

dist:
	uv build

upload: dist
	uvx twine upload --repository "$(PYPI_REPO)" dist/*

test:
	uv run pytest --cov

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run mypy src

fmt:
	uv run ruff check --fix src tests
	uv run ruff format src tests

check: lint test cog-check

cog-check:
	uv run python -m cogapp --check README.md

cog:
	uv run python -m cogapp README.md

install:
	uv sync --extra dev
	uv run pre-commit install

clean:
	rm -rf build/ dist/ *.egg-info/ .coverage .pytest_cache/ src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
