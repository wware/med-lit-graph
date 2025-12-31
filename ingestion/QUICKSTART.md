# Ingestion Pipeline Quickstart

This guide walks you through the process of populating the Medical Knowledge Graph with real data from PubMed Central (PMC).

## Prerequisites

- Docker & Docker Compose
- 50GB+ Disk Space (for Ollama models and Vector DB)
- 16GB+ RAM (Recommended for CPU) OR GPU instance (Recommended for speed)

## Performance Options

### GPU-Accelerated (Recommended) - 50-100x Faster
See [cloud/README.md](../cloud/README.md) for Lambda Labs or AWS EC2 setup.
- **Speed**: 5-10 papers/minute
- **Cost**: ~$0.75/hr (Lambda Labs A10)
- **Best for**: Processing 100s-1000s of papers

### CPU-Only (Slower)
- **Speed**: 1 paper per 20+ minutes
- **Cost**: Free (local)
- **Best for**: Testing, small batches (<10 papers)

## 1. Finding Papers to Ingest

Before running the pipeline, it's helpful to identify good search terms.

1.  Go to [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/).
2.  Try search terms like:
    - `"metformin type 2 diabetes"`
    - `"BRCA1 breast cancer treatment"`
    - `"Alzheimer's amyloid hypothesis"`
3.  Filter for "Open Access" to ensure full text availability.
4.  Note a few relevant PMC IDs (e.g., `PMC1234567`) or just keep your search query handy.

## 2. Starting the Stack

### Option A: GPU-Accelerated (Recommended)

```bash
# Set up GPU server (one-time) - see cloud/README.md
# Then set remote Ollama server
export OLLAMA_HOST=http://<GPU_SERVER_IP>:11434

# Start PostgreSQL locally
cd ingestion
docker compose up -d postgres

# Clear old entity database (if restarting)
rm -rf ./data/entity_db
```

### Option B: CPU-Only

```bash
cd ingestion
docker compose up -d
```

> **Note:** Data is persisted locally in `ingestion/data/postgres`. This allows other stacks to access the same database by mounting this directory.

## 3. Preparing the LLM

### GPU Server
Models are pulled on the GPU server (see cloud/README.md).

### Local CPU
```bash
# Pull the model
docker compose exec ollama ollama pull llama3.1:8b
```

> **Note on Model Size**: If you have a high-memory system (**40GB+ RAM**), you can use `llama3.1:70b` for higher extraction quality.
> ```bash
> docker compose exec ollama ollama pull llama3.1:70b
> ```

## 4. Running the Ingestion Pipeline

The pipeline searches PubMed based on your query, downloads full-text XML, extracts entities/relationships using the LLM, resolves entities, and saves everything to PostgreSQL.

```bash
docker compose run --rm ingest python ingest_papers.py \
  --query "metformin type 2 diabetes" \
  --limit 10 \
  --model "llama3.1:8b"
```

**What happens next:**
1.  **Search**: Queries PubMed API for 10 relevant papers.
2.  **Download**: Fetches full-text JATS XML for each paper.
3.  **Extract**: Uses LLM to identify entities (Drugs, Diseases, etc.) and relationships (TREATS, CAUSES).
4.  **Deduplicate**: Matches entities using exact names + strict similarity (0.01 threshold).
5.  **Embed**: Generates vector embeddings for entities using BiomedBERT.
6.  **Persist**: Saves structured data to `medgraph` Postgres database.

## 5. Verification

You can verify the data was ingested by querying the database directly:

```bash
docker compose exec postgres psql -U postgres -d medgraph -c "
SELECT
    p.id as paper,
    count(distinct e.id) as entities,
    count(distinct r.id) as relationships
FROM papers p
LEFT JOIN evidence ev ON p.id = ev.paper_id
LEFT JOIN relationships r ON ev.relationship_id = r.id
LEFT JOIN entities e on e.id = r.subject_id OR e.id = r.object_id
GROUP BY p.id;
"
```

## 6. Current Status

✅ **25+ papers** successfully ingested with:
- Unique entity canonical IDs
- Deduplicated entities (no false positives)
- Relationships with full evidence trails
- Flexible LLM output parsing

## 7. Accessing Data from Other Stacks

Since the database files are stored in `ingestion/data/postgres`, you can point any other Docker stack to this directory to access the graph data.

Example volume configuration for another stack:
```yaml
services:
  retrieval_db:
    image: pgvector/pgvector:pg16
    volumes:
      - ./path/to/ingestion/data/postgres:/var/lib/postgresql/data
```

## Troubleshooting

### Slow Performance
Use GPU acceleration - see [cloud/README.md](../cloud/README.md)

### Entity Matching Issues
Clear entity DB: `rm -rf ./data/entity_db`

### LLM Output Errors
The pipeline handles multiple formats automatically. Malformed relationships are skipped with warnings.
