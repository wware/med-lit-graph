#!/bin/bash -xe

PYTHONFILES=$(git ls-files | grep -E '\.py$')

uv run ruff check $PYTHONFILES
uv run black $PYTHONFILES
uv run pylint -E $PYTHONFILES
uv run flake8 --max-line-length=200 $PYTHONFILES
# uv run mypy $PYTHONFILES
uv run pytest tests/
