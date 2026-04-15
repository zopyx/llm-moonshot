# Contributing to zopyx.llm-moonshot

Thank you for your interest in improving this project!

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and
packaging.

```bash
git clone https://github.com/zopyx/llm-moonshot.git
cd llm-moonshot
uv sync --extra dev
```

## Running tests

```bash
make test        # Run the full test suite with coverage
uv run pytest    # Run tests directly
```

## Code quality

We use **Ruff** for linting and formatting, and **mypy** for static type checking.

```bash
make lint        # Check formatting and types
make fmt         # Auto-fix formatting and lint issues
make check       # Run lint + tests + cog
```

## Pre-commit hooks

After installing dependencies, enable the pre-commit hooks:

```bash
make install     # Also installs pre-commit hooks
```

## Updating the README model list

The list of supported models in `README.md` is auto-generated with
[cog](https://cog.readthedocs.io/). After changing `DEFAULT_MOONSHOT_MODEL_IDS`,
run:

```bash
make cog
```

## Cutting a release

1. Update `CHANGELOG.md` and bump the version in `pyproject.toml`.
2. Run `make check` to ensure everything is green.
3. Commit, tag, and push.
4. Create a GitHub Release — the publish workflow will upload to PyPI
   automatically.

```bash
git add .
git commit -m "release: 0.x.y"
git tag 0.x.y
git push && git push --tags
```
