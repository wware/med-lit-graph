# HIV Controversy Knowledge Graph Pipeline

## Project Overview

Building a multi-layer knowledge graph extraction pipeline for HIV/AIDS medical literature to analyze the historical controversy around HIV as the causative agent of AIDS.

**Current Status**: Stage 1 (Entity Extraction) working. Stages 2-6 designed but not implemented.

---

## Architecture

### Three-Layer Knowledge Graph Design

Based on GitHub issue #20 discussion about separating extraction artifacts from semantic claims:

```
Layer 1: EXTRACTION (entities + co-occurrence)
         ↓
Layer 2: CLAIMS (semantic relationships with provenance)
         ↓
Layer 3: EVIDENCE (supporting/refuting evidence items)
```

### Pipeline Stages

```bash
# Stage 1: Extract entities (NER) - ✅ WORKING
docker-compose run pipeline extract-entities

# Stage 2: Extract provenance (paper metadata + structure) - DESIGNED
docker-compose run pipeline extract-provenance

# Stage 3: Generate embeddings (entities + paragraphs) - DESIGNED
docker-compose run pipeline generate-embeddings

# Stage 4: Extract claims (relationships) - DESIGNED
docker-compose run pipeline extract-claims

# Stage 5: Aggregate evidence - DESIGNED
docker-compose run pipeline aggregate-evidence

# Stage 6: Import to PostgreSQL/AGE - DESIGNED
docker-compose run pipeline import-graph
```

---

## Technology Stack

- **Extraction**: BioBERT (ugaray96/biobert_ncbi_disease_ner)
- **Entity Storage**: SQLite (entities.db) for fast canonical entity resolution
- **Embeddings**: sentence-transformers (planned)
- **Graph Storage**: PostgreSQL + Apache AGE (planned)
- **Containerization**: Docker + Docker Compose
- **Output Format**: JSON (one file per paper)

---

## File Structure

```
hiv-controversy/
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Orchestration
├── requirements.txt             # Python dependencies
├── pmc_ner_pipeline.py         # Stage 1: Entity extraction (WORKING)
├── pmc_xmls/                   # Input: PMC XML files
│   ├── PMC322947.xml
│   ├── PMC2545367.xml
│   └── ...
└── output/                     # Extraction results
    ├── entities.db             # SQLite: canonical entities + aliases
    ├── nodes.csv               # Debug: extracted nodes
    ├── edges.csv               # Debug: co-occurrence edges
    └── papers/                 # JSON per paper (PLANNED)
        ├── PMC322947.json
        ├── PMC2545367.json
        └── ...
```

---

## Stage 1: Entity Extraction (WORKING)

### What It Does

1. Parses PMC XML files (JATS format)
2. Extracts entities using BioBERT NER model
3. Stores canonical entities in SQLite with alias mapping
4. Outputs co-occurrence edges (simple graph)

### Key Design Decisions

- **HIV and AIDS are separate entities** - This is intentional! The controversy is about the RELATIONSHIP, not the entities themselves.
- **SQLite for entity canonicalization** - Fast local lookups before expensive graph operations
- **Filtering aggressive** - Confidence threshold 0.85, minimum 3 chars, stopword list
- **Co-occurrence only** - No semantic predicates yet (that's Stage 4)

### Current Results

```bash
Processed 9 XML files.
Nodes: 12, Edges: 24
```

Found entities include:
- AIDS (entity_id=2)
- HIV (entity_id=4)
- Plus some noise (working on filtering)

### Running Stage 1

```bash
cd ~/med-lit-graph/hiv-controversy
docker-compose build
docker-compose run pipeline
```

---

## Stage 2: Provenance Extraction (DESIGNED)

### Purpose

Extract paper-level metadata and document structure to enable traceback from claims to source text.

### Schema: `provenance.db`

```sql
CREATE TABLE papers (
    pmc_id TEXT PRIMARY KEY,
    pmid TEXT,
    title TEXT,
    journal TEXT,
    pub_date DATE,
    authors TEXT,  -- JSON array
    doi TEXT
);

CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,
    paper_id TEXT REFERENCES papers(pmc_id),
    section_type TEXT,  -- abstract, intro, methods, results, discussion
    section_order INTEGER
);

CREATE TABLE paragraphs (
    paragraph_id TEXT PRIMARY KEY,
    section_id TEXT REFERENCES sections(section_id),
    paragraph_order INTEGER,
    text TEXT,
    start_char INTEGER,
    end_char INTEGER
);

CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper TEXT REFERENCES papers(pmc_id),
    cited_reference TEXT,  -- PMID, DOI, or freetext
    context TEXT
);
```

### Why Provenance Matters

For HIV controversy, we need to know:
- **Who** made the claim (Gallo vs. Montagnier)
- **When** it was published (timing of discoveries)
- **Where** in the paper (methods vs. speculation)
- **What** they cited (prior evidence)

---

## Stage 3: Embeddings (DESIGNED)

### Purpose

Generate semantic embeddings for:
1. **Entity resolution** - Map "HIV"/"HTLV-III"/"LAV" to same canonical ID
2. **Semantic search** - Find relevant paragraphs for queries
3. **Claim similarity** - Identify contradictory claims

### Model Choice

**Recommended**: `sentence-transformers/all-mpnet-base-v2` (768-dim)
- General purpose, good quality
- Alternative: BioBERT for domain specificity

### Schema Extensions

```sql
-- Add to entities.db
CREATE TABLE entity_embeddings (
    entity_id INTEGER PRIMARY KEY,
    embedding BLOB,  -- 768-dim float32 array
    model_name TEXT,
    created_at DATETIME
);

-- Add to provenance.db
CREATE TABLE paragraph_embeddings (
    paragraph_id TEXT PRIMARY KEY,
    embedding BLOB,
    model_name TEXT,
    created_at DATETIME
);
```

---

## Stage 4: Claims Extraction (DESIGNED)

### Purpose

Extract semantic relationships between entities with full provenance.

### Schema: `claims.db`

```sql
CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    paper_id TEXT REFERENCES papers(pmc_id),
    section_id TEXT REFERENCES sections(section_id),
    paragraph_id TEXT REFERENCES paragraphs(paragraph_id),
    subject_entity_id INTEGER,
    predicate TEXT,  -- CAUSES, CORRELATES_WITH, DETECTED_IN, etc.
    object_entity_id INTEGER,
    extracted_text TEXT,
    confidence REAL,
    evidence_type TEXT  -- epidemiological, molecular, clinical
);
```

### Example Claims

```json
{
  "claim_id": "PMC322947_claim_1",
  "paper_id": "PMC322947",
  "authors": ["Gallo RC", "Wong-Staal F"],
  "pub_date": "1986-02",
  "subject": "HTLV-III",
  "predicate": "INFECTS",
  "object": "lymphocytes",
  "extracted_text": "HTLV-III-infected cells expressing viral RNA",
  "paragraph_id": "PMC322947_results_p2"
}
```

The controversy: Different papers make different predicate claims about HIV→AIDS relationship.

---

## Stage 5: Evidence Aggregation (DESIGNED)

### Purpose

Link multiple evidence items to claims, supporting or refuting them.

### Schema

```sql
CREATE TABLE evidence (
    evidence_id TEXT PRIMARY KEY,
    claim_id TEXT REFERENCES claims(claim_id),
    supports BOOLEAN,  -- TRUE=supports, FALSE=refutes
    strength TEXT,  -- high, medium, low
    type TEXT,  -- in_situ_hybridization, epidemiological, etc.
    paragraph_id TEXT,
    details TEXT  -- JSON with method-specific info
);
```

---

## JSON Output Format (DESIGNED)

Each paper produces ONE JSON file in `output/papers/{pmc_id}.json`:

```json
{
  "paper_id": "PMC322947",
  "metadata": {
    "pmid": "3003749",
    "title": "Detection of lymphocytes expressing HTLV-III...",
    "authors": [{"name": "Gallo RC", "affiliation": "NIH"}],
    "pub_date": "1986-02-01",
    "journal": "Proc Natl Acad Sci U S A"
  },
  "sections": [...],
  "entities": [
    {
      "entity_id": 42,
      "canonical_id": 15,
      "text": "HTLV-III",
      "type": "Disease",
      "paragraph_id": "PMC322947_abstract_p1",
      "embedding": [0.12, 0.34, ...]
    }
  ],
  "claims": [
    {
      "claim_id": "PMC322947_claim_1",
      "subject_entity": 42,
      "predicate": "INFECTS",
      "object_entity": 56,
      "paragraph_id": "PMC322947_results_p2"
    }
  ],
  "evidence": [...],
  "extraction_metadata": {
    "pipeline_version": "0.1.0",
    "extracted_at": "2024-12-17T19:30:00Z",
    "models": {
      "ner": "ugaray96/biobert_ncbi_disease_ner",
      "embeddings": "sentence-transformers/all-mpnet-base-v2"
    }
  }
}
```

### Benefits

1. **Versioning** - Git diff to see extraction changes
2. **Debugging** - Inspect individual papers
3. **Incremental** - Reprocess just one paper
4. **Portable** - Import anywhere (Neo4j, AGE, etc.)

---

## Stage 6: PostgreSQL/AGE Import (DESIGNED)

### Purpose

Bulk import JSON files into graph database for querying.

### PostgreSQL + Apache AGE

- **Nodes**: Papers, Entities, Claims, Evidence
- **Edges**: PUBLISHED, MENTIONS, CLAIMS, SUPPORTS, REFUTES, CITES
- **Indexes**: Vector similarity index on embeddings (pgvector)

### Import Strategy

```python
# Disable indexes during bulk import
# Use COPY instead of INSERT
# Parallelize across JSON files
# Rebuild indexes after import
```

---

## Design Decisions & Rationale

### 1. SQLite + PostgreSQL (Hybrid)

**SQLite** for entity canonicalization (fast, local)
**PostgreSQL/AGE** for graph queries (complex relationships)

Separates concerns: entity resolution vs. graph traversal

### 2. JSON Intermediate Format

**Before**: Direct DB insertion (hard to debug, version, inspect)
**After**: JSON per paper (git-trackable, inspectable, portable)

### 3. Three-Layer Architecture

**Extraction**: Raw NER output (noisy, co-occurrence only)
**Claims**: Semantic predicates with provenance
**Evidence**: Supporting/refuting items

Clean separation enables testing each layer independently.

### 4. HIV ≠ AIDS at Entity Layer

This is **intentional**! The controversy is about the RELATIONSHIP.
- Entity layer: HIV (virus) and AIDS (syndrome) are separate
- Claim layer: Papers make different claims about HIV→AIDS
- Evidence layer: Support/refute those claims

### 5. Embeddings for Entity Resolution

Use semantic similarity to cluster entity variants:
- "HIV" / "HTLV-III" / "LAV" / "human immunodeficiency virus"
→ All map to same canonical entity

---

## Known Issues

### Stage 1 (Current)

1. **Noisy extraction** - Still catching fragments like "enter", "chronic"
   - Solution: Expand stopword list, tune confidence threshold
   
2. **No entity clustering** - "HIV" and "HTLV-III" are separate
   - Solution: Stage 3 embeddings + clustering

3. **Model download at runtime** - Takes 68 seconds
   - ~~Solution: Pre-download in Dockerfile~~ FIXED via removing volume mount

4. **Docker image bloat** - Was 8.5GB
   - Solution: CPU-only PyTorch (`--extra-index-url`)

---

## Next Steps

### Immediate (Week 1)

1. Refactor `pmc_ner_pipeline.py` → `pmc_pipeline.py` with argparse
2. Implement `extract_provenance()` - parse PMC XML metadata
3. Add JSON output for Stage 1 results

### Short Term (Week 2-3)

4. Implement `generate_embeddings()` - entities + paragraphs
5. Add entity clustering using cosine similarity
6. Implement `extract_claims()` - relationship extraction

### Medium Term (Month 1)

7. Implement `aggregate_evidence()`
8. Set up PostgreSQL + AGE in docker-compose
9. Implement `import_graph()` - bulk JSON import

### Long Term

10. Build query interface for doctors/researchers
11. Add claim verification UI (support/refute evidence)
12. Expand to other medical controversies

---

## Development Commands

```bash
# Build container
docker-compose build

# Run entity extraction
docker-compose run pipeline

# Inspect results
sqlite3 output/entities.db "SELECT * FROM entities;"
sqlite3 output/entities.db "SELECT * FROM aliases WHERE name LIKE '%HIV%';"

# Debug: What did we extract?
head -20 output/nodes.csv

# Rebuild without cache
docker-compose build --no-cache

# Shell into container
docker-compose run --rm pipeline /bin/bash
```

---

## References

- **GitHub Issue #20**: Three-layer KG architecture discussion
- **BioBERT NER**: ugaray96/biobert_ncbi_disease_ner
- **PMC JATS XML**: https://jats.nlm.nih.gov/
- **Apache AGE**: https://age.apache.org/

---

## Contact

Will Ware - wware@alum.mit.edu
Project: https://github.com/wware/med-lit-graph
