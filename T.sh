#!/bin/bash -xe
uv run docker compose -f docker-compose.yml up -d postgres
uv run pytest tests/test_postgresql_integration.py
uv run docker compose -f docker-compose.yml down
