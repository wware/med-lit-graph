# HIV Controversy Knowledge Graph Pipeline

A complete pipeline for extracting, processing, and querying biomedical literature related to the HIV/AIDS controversy from PubMed Central (PMC).

## Overview

This project builds a provenance-first knowledge graph from PMC literature, storing extracted entities, claims, and evidence in a PostgreSQL database with the Apache AGE graph extension. The pipeline consists of 6 stages that process XML files through NER, provenance extraction, claims extraction, embeddings generation, evidence synthesis, and finally loading into a graph database.

## Quick Start

```bash
# Run all 6 pipeline stages
docker-compose run --rm pipeline 1-6

# Start the query web interface
docker-compose up -d

# Access the web interface at:
# http://localhost:8000
```

## Features

- 🧬 **6-stage processing pipeline** from XML to graph database
- 🤖 **Entity extraction** using BioBERT NER
- 📊 **Claims extraction** with pattern-based relationship detection  
- 📈 **Evidence synthesis** with strength ratings
- 🔍 **Semantic embeddings** for similarity search
- 🗄️ **Graph database** with Cypher query support (Apache AGE)
- 🌐 **Interactive web interface** for exploring the knowledge graph
- 🔌 **REST API** for programmatic access
- 🐳 **Docker-based** for easy deployment

## Documentation

- **[PIPELINE_USAGE.md](PIPELINE_USAGE.md)** - Detailed pipeline usage guide
- **[QUERY_TOOLS.md](QUERY_TOOLS.md)** - Query tools documentation and examples
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide (Fly.io vs AWS)

## Technologies

- Python 3.11, BioBERT, Sentence Transformers
- SQLite (intermediate), PostgreSQL + Apache AGE (final)
- FastAPI, Docker, Pydantic

## License

MIT License
