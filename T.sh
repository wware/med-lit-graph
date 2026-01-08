#!/bin/bash -xe
cd ~/med-lit-graph/ingestion
uv run docker compose down -v # Cleans up any old volumes and services
uv run docker compose build ingest # Rebuilds the ingest image to pick up requirements.txt changes
uv run docker compose up -d postgres redis redis-commander # Starts the database and other services

# --- ADD THESE LINES TO YOUR T.sh SCRIPT ---
# Give PostgreSQL a moment to fully start up and be ready for connections
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Initialize the database within the Docker Compose environment
# We use the 'ingest' service's environment to run init_db.py
echo "Initializing the database..."
uv run docker compose run --rm ingest python -m ingestion.init_db
# --- END ADDITION ---

uv run docker compose run ingest \
    python -m ingestion.ingest_papers \
    --query "brca1 breast cancer" \
    --limit 5 \
    --model llama3.1:8b

# uv run pytest tests/test_postgresql_integration.py
uv run docker compose down -v
