#!/bin/bash -xe

export PYTHONFILES=$(git ls-files | grep -E '\.py$')
export PYTHONPATH=$(pwd)

uv run ruff check --fix $PYTHONFILES
uv run black $PYTHONFILES
uv run pylint -E $PYTHONFILES
uv run flake8 --max-line-length=200 $PYTHONFILES
# uv run mypy $PYTHONFILES
uv run pytest tests/
