# Python conventions and practices

- Full docstrings everywhere all the time. Type hints everywhere that make sense.
- Use Pydantic models, not dataclasses.
- Where possible, favor uv for setting up virtual environments. If uv is not already
  set up, offer to migrate from whatever is there to uv.
- Testing should be done with pytest. Use fixtures where appropriate.
- Linting should be done first with "ruff check", then "pylint -E", then format with black.
- Line width should be 200 characters.
