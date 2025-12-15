# Mini server for front end validation

**Created:** 12/6/2025 18:08:01

````plaintext
Bash Tool: Find the med-lit-graph repository
````

A lightweight FastAPI server with synthetic data is perfect for validating your frontend without waiting for the full pipeline. Let me create a skeleton:

````plaintext
Create File: Create a simple FastAPI server skeleton for testing the med-lit-graph frontend
````

````plaintext
Create File: Create requirements.txt for the dev server
````

````plaintext
Bash Tool: Fix ownership of created files
````

Perfect! I've created a skeleton FastAPI server. Here's what you got:

## 📁 Files Created

**`server.py`** - The main server with:
- ✅ FastAPI app with CORS enabled
- ✅ Pydantic models for Entity, Relationship, Paper
- ✅ API endpoints ready to implement:
  - `GET /entities` - List entities (filterable)
  - `GET /relationships` - List relationships
  - `GET /papers` - List papers
  - `POST /graph/traverse` - Main graph query endpoint
  - `GET /search` - Search across entities and papers
  - `GET /stats` - Graph statistics
- ✅ Auto-generated docs at `/docs` (Swagger UI)
- ✅ Hot reload enabled for development

**`requirements.txt`** - Dependencies

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py

# Server starts on http://localhost:8000
# API docs at http://localhost:8000/docs
```

## 🎯 Next Steps for Synthetic Data

You'll want to populate the `load_synthetic_data()` function. Here are some ideas:

**Option 1: Small curated dataset**
- ~10-20 entities (Aspirin, Cancer, TP53, etc.)
- ~20-30 relationships
- ~5-10 fake papers
- Good for: Testing specific UI features

**Option 2: Generated realistic data**
- Use real entity names from UMLS/SNOMED
- Generate plausible relationships
- Create realistic-looking abstracts
- Good for: Load testing, demos

**Option 3: Subset of real data**
- Download a few real papers from PubMed
- Extract entities/relationships manually
- Most realistic but more work

Want me to generate some synthetic data for one of these options?





---
Powered by [Claude Exporter](https://www.claudexporter.com)
