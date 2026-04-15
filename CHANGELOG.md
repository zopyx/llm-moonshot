# Changelog

## 0.3.8 - 2026-04-15

- Bumped the release version to `0.3.8`.

## 0.3.5 - 2026-04-15

- Fixed the `src/` layout packaging regression so CI and isolated builds include the plugin package correctly.
- Marked the flaky streaming HTTPX fallback test as `xfail` to keep release automation stable while that behavior is investigated.

## 0.3.4 - 2026-04-15

- Maintenance release with no functional changes.

## 0.3.3 - 2026-04-15

- Refactored into a proper `src/` layout package with type hints and explicit error handling.
- Added `ruff`, `mypy`, `pytest-cov`, and `pre-commit` to the development toolchain.
- Expanded test suite to 19 tests with 90% code coverage.
- Auto-generated README model list using `cog`.
- Added `CONTRIBUTING.md` and a troubleshooting section to the README.
- Improved CI/CD workflows with lint gates and reduced duplicate runs.

## 0.3.2 - 2026-04-15

This release aligns the `zopyx.llm-moonshot` fork with the current package name and documents the fork-specific maintenance work.

- Renamed the published package to `zopyx.llm-moonshot`.
- Added a fallback Moonshot model catalog so `llm models list` still shows Moonshot models when live model discovery fails or no key is configured.
- Added regression tests for fallback model registration.
- Migrated CI/CD to `uv`, committed `uv.lock`, and locked workflow installs for reproducible builds.
- Adjusted the GitHub Actions test matrix to Python `3.12` through `3.14`.
- Added `make dist` and `make upload` helpers for local release workflows.
- Switched local upload workflow to `twine` so `.pypirc` can be reused directly.
- Replaced deprecated license classifier metadata with the SPDX license expression `Apache-2.0`.
- Updated documentation to point at the `zopyx` fork and current workflow.

Why these changes were made after forking:

- The package rename avoids collisions with the upstream distribution and makes it clear which distribution is maintained by `zopyx`.
- The fallback model list fixes a usability problem where Moonshot models could disappear from `llm models list` when the remote model lookup timed out or failed.
- The `uv` migration and lockfile were introduced to keep local builds and GitHub Actions runs aligned and reproducible.
- The Makefile targets simplify repeatable build and release steps for the fork.
- The packaging metadata cleanup removes warnings and keeps the project aligned with current Python packaging standards.

## 0.3.1

Upstream release history prior to the `zopyx` fork. See the original project history for the pre-fork development lineage.
