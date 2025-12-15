# Quickstart: Local Paper Ingestion with Ollama

This guide provides instructions for setting up and running the local paper ingestion pipeline using Ollama and specialized embedding models.

## 1. Setup

First, ensure you have the necessary dependencies and models installed.

```bash
# Navigate to the project directory
cd ~/med-lit-graph

# Install Python dependencies
pip install -r ingestion/requirements.txt

# Pull the large language model for extraction (choose one)
ollama pull llama3.1:70b      # Best accuracy, needs ~40GB RAM
# or
ollama pull qwen2.5:32b       # Good balance, ~20GB RAM

# Pull the default embedding model for entity matching
ollama pull nomic-embed-text
```

## 2. Running the Ingestion Pipeline

Once the setup is complete, you can run the ingestion script with a query. The script will search PubMed, download the relevant papers, and use the local Ollama model to extract entities and relationships.

### Standard Ingestion

This command uses the default `nomic-embed-text` for entity matching.

```bash
python ingestion/ingest_papers.py \
  --query "metformin diabetes AMPK" \
  --limit 100 \
  --model llama3.1:70b
```

### Ingestion with Biomedical Embeddings

For improved accuracy in medical entity matching, you can use specialized models like `BiomedBERT` or `PubMedBERT`. These models are trained on biomedical literature and provide better results for recognizing and deduplicating clinical and biological terms.

The first run will download the selected model (approx. 400MB), which will be cached for future use.

```bash
# Run with the default BioBERT model
python ingestion/ingest_papers.py \
  --query "metformin diabetes AMPK" \
  --limit 100

# Or specify another HuggingFace model
python ingestion/ingest_papers.py \
  --query "PARP inhibitors breast cancer" \
  --embedding-model "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext" \
  --limit 50
```

### How It Works

1.  **Searches PubMed** for papers matching the query.
2.  **Downloads JATS XML** from the PubMed Central (PMC) repository.
3.  **Extracts Entities & Relationships** using the specified Ollama model.
4.  **Deduplicates Entities** using vector similarity search with the chosen embedding model.
5.  **Saves JSON Output** to `data/papers/`, with one file per paper.
6.  **Builds an Entity Database** in `data/entity_db/` to maintain canonical entity identifiers.
