# Pipeline Testing Guide: Cloud-Based Ollama

This guide explains how to run the Stage 1 ingestion pipeline (`ingestion/run_stage1.py`) using a remote, GPU-accelerated Ollama instance (e.g., on Lambda Labs or AWS).

## Prerequisites

1.  **Cloud GPU Instance**: You should have a cloud instance running Ollama with GPU support.
    *   See [Lambda Labs Setup Gist](https://gist.github.com/wware/4b9e44412764747082f49286a5f2ab81) for setup instructions.
    *   Ensure Ollama is running on port `11434`.

2.  **Local Environment**:
    *   Python 3.10+
    *   Dependencies installed (`uv sync`)

## Configuration

The pipeline connects to Ollama via the URL specified in the `--ollama-host` argument or passed through environment configurations.

### Option 1: Direct Connection (if port is exposed)

If your cloud instance exposes port 11434 directly (ensure firewall allows this, usage of VPN or IP allowlisting is recommended):

```bash
export OLLAMA_HOST="http://<YOUR_INSTANCE_IP>:11434"
```

### Option 2: SSH Tunnel (Recommended for Security)

If the port is not exposed, verify it via SSH tunnel:

```bash
# Forward local port 11434 to remote port 11434
ssh -L 11434:localhost:11434 user@<YOUR_INSTANCE_IP>
```

Then simply use localhost:

```bash
export OLLAMA_HOST="http://localhost:11434"
```

## Running the Pipeline

You can run the Stage 1 pipeline wrapper directly. It accepts `argparse` arguments for configuration.

### Basic Usage

```bash
# Run from project root
uv run python -m ingestion.run_stage1 \
  --query "metformin diabetes" \
  --limit 5 \
  --model "llama3.1:70b" \
  --ollama-host "$OLLAMA_HOST"
```

### Arguments

| Argument | Default | Description |
|:--- |:--- |:--- |
| `query` | **Required** | PubMed search query string. |
| `limit` | `10` | Number of papers to process. |
| `model` | `llama3.1:70b` | Name of the Ollama model to use. Ensure this model is pulled on the remote instance. |
| `output` | `ingestion/outputs/entities.jsonl` | Path to output JSONL file. |
| `ollama-host` | `http://localhost:11434` | URL of the Ollama server. |

## Verification

1.  **Check Output**: Detailed logs will appear in the console.
2.  **Inspect Results**: Check the output file (default `ingestion/outputs/entities.jsonl`).
    ```bash
    head -n 2 ingestion/outputs/entities.jsonl
    ```
3.  **Troubleshooting**:
    *   **Connection Refused**: Check your SSH tunnel or firewall settings.
    *   **Model Not Found**: SSH into your cloud instance and run `ollama pull <model_name>`.

## Database Dependency (IMPORTANT)

**Stage 1 (`run_stage1.py`) is database-agnostic.**

It extracts entities to a JSONL file (`ingestion/outputs/entities.jsonl`) and **does NOT** write to PostgreSQL. You do not need the database running to execute this stage.

However, if you proceed to **Stage 2** (loading data) or use the legacy script (`ingest_papers.py`), you **WILL** need the database.

### Running PostgreSQL Locally

To spin up just the database for testing loading scripts:

```bash
docker compose up -d postgres
```

This will run Postgres on port `5432` (or the port defined in your `.env` if you have one).

## Using Docker Compose

If you prefer running the pipeline inside Docker (using the root `docker-compose.yml`), pass the host variable:

```bash
# Ensure OLLAMA_HOST is set in your shell
export OLLAMA_HOST="http://<YOUR_INSTANCE_IP>:11434"

# Run the ingest service
# Link to postgres so it's available if you run other scripts
docker compose run -e OLLAMA_HOST=$OLLAMA_HOST ingest \
  python -m ingestion.run_stage1 --query "statins" --limit 5
```
