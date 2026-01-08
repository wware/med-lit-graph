#!/bin/bash -xe
cd ~/med-lit-graph/ingestion
uv run docker compose down -v
uv run docker compose build ingest
uv run docker compose up -d postgres redis redis-commander
uv run docker compose run ingest \
    python -m ingestion.ingest_papers \
    --query "brca1 breast cancer" \
    --limit 5 \
    --model llama3.1:8b
# uv run pytest tests/test_postgresql_integration.py
uv run docker compose down -v
