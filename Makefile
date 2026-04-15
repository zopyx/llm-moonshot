.PHONY: dist upload

PYPI_REPO ?= pypi

dist:
	uv build

upload: dist
	uvx twine upload --repository "$(PYPI_REPO)" dist/*
