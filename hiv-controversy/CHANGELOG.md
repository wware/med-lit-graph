# Changelog

All notable changes and development progress for the HIV Controversy Knowledge Graph Pipeline.

---

## [0.1.0] - 2024-12-17

### Stage 1: Entity Extraction - ✅ WORKING

#### Added
- Docker containerization with Python 3.11
- BioBERT NER model integration (`ugaray96/biobert_ncbi_disease_ner`)
- SQLite-based entity canonicalization system
- Entity-to-alias mappings for entity resolution
- Co-occurrence edge extraction
- CSV output for debugging (nodes.csv, edges.csv)
- PMC XML parsing (JATS format)

#### Fixed
- Docker image bloat (8.5GB → 1.5GB) by using CPU-only PyTorch
- Model re-downloading at runtime by baking into image
- Volume mount masking pre-downloaded model
- Noisy entity extraction with confidence threshold (0.85) and stopword filtering
- Entity label filtering (now correctly handles 'Disease' label)

#### Known Issues
- Still some noise in extraction ("enter", "chronic", etc.)
- No entity clustering yet (HIV and HTLV-III are separate)
- Co-occurrence only, no semantic predicates

#### Performance
- 9 XML files processed in ~3 seconds
- Docker build time: ~5-10 minutes
- Image size: ~1.5GB

---

## [Unreleased] - Planned Features

### Stage 2: Provenance Extraction - DESIGNED

#### Planned
- Parse PMC XML metadata (title, authors, journal, date)
- Extract document structure (sections, paragraphs)
- Create provenance.db with paper/section/paragraph tables
- Citation extraction and parsing
- Link entities to specific paragraph locations

#### Schema
```sql
CREATE TABLE papers (pmc_id, pmid, title, journal, pub_date, authors, doi);
CREATE TABLE sections (section_id, paper_id, section_type, section_order);
CREATE TABLE paragraphs (paragraph_id, section_id, text, start_char, end_char);
CREATE TABLE citations (citing_paper, cited_reference, context);
```

### Stage 3: Embeddings - DESIGNED

#### Planned
- Generate embeddings for entities using sentence-transformers
- Generate embeddings for paragraphs
- Store embeddings as binary blobs in SQLite
- Entity clustering using cosine similarity
- Map entity variants (HIV/HTLV-III/LAV) to canonical IDs

#### Models
- Primary: `sentence-transformers/all-mpnet-base-v2` (768-dim)
- Alternative: BioBERT embeddings for domain specificity

#### Schema
```sql
CREATE TABLE entity_embeddings (entity_id, embedding BLOB, model_name);
CREATE TABLE paragraph_embeddings (paragraph_id, embedding BLOB, model_name);
```

### Stage 4: Claims Extraction - DESIGNED

#### Planned
- Extract semantic relationships between entities
- Classify predicates (CAUSES, INFECTS, CORRELATES_WITH, etc.)
- Link claims to specific paragraphs for provenance
- Store extracted sentence with claim
- Confidence scoring for claims

#### Predicates
- CAUSATION: CAUSES, PREVENTS, INHIBITS, PROMOTES
- DETECTION: DETECTED_IN, FOUND_IN, ISOLATED_FROM
- ASSOCIATION: CORRELATES_WITH, ASSOCIATED_WITH
- BIOLOGICAL: INFECTS, BINDS_TO, ACTIVATES, SUPPRESSES
- CLINICAL: TREATS, DIAGNOSED_BY, PROGRESSES_TO

#### Schema
```sql
CREATE TABLE claims (
    claim_id, paper_id, section_id, paragraph_id,
    subject_entity_id, predicate, object_entity_id,
    extracted_text, confidence, evidence_type
);
```

### Stage 5: Evidence Aggregation - DESIGNED

#### Planned
- Link evidence items to claims
- Classify evidence as supporting/refuting
- Extract quantitative metrics (sample size, p-values, etc.)
- Rate evidence strength (high/medium/low)
- Store method-specific details

#### Schema
```sql
CREATE TABLE evidence (
    evidence_id, claim_id, supports BOOLEAN, strength,
    type, paragraph_id, details
);
CREATE TABLE evidence_metrics (
    evidence_id, sample_size, detection_rate, p_value,
    confidence_interval, statistical_test
);
```

### Stage 6: PostgreSQL/AGE Import - DESIGNED

#### Planned
- Bulk import JSON files to PostgreSQL + Apache AGE
- Create graph nodes (Paper, Entity, Claim, Evidence)
- Create graph edges (PUBLISHED, MENTIONS, CLAIMS, SUPPORTS, REFUTES, CITES)
- Vector similarity indexes for embeddings (pgvector)
- Full-text search indexes
- Cypher query interface

#### Import Strategy
- Disable indexes during bulk import
- Use COPY instead of INSERT for speed
- Parallelize across JSON files
- Rebuild indexes after import complete

### JSON Output Format - DESIGNED

#### Planned
- One JSON file per paper in `output/papers/`
- Self-contained with all extraction results
- Git-trackable for version control
- Includes metadata, sections, entities, claims, evidence, citations
- Embeddings stored as arrays in JSON

#### Benefits
- Human-readable and inspectable
- Easy to debug individual papers
- Portable to any database
- Enables incremental processing
- Supports partial reruns

---

## Design Decisions

### 2024-12-17: Three-Layer Architecture

Based on GitHub issue #20 discussion, separated the pipeline into distinct layers:

1. **Extraction Layer** - Raw NER output, co-occurrence only
2. **Claims Layer** - Semantic predicates with provenance
3. **Evidence Layer** - Supporting/refuting evidence items

**Rationale**: Clean separation enables independent testing and validation of each layer. Extraction artifacts (co-occurrence) don't pollute semantic graph.

### 2024-12-17: Hybrid SQLite + PostgreSQL

**Decision**: Use SQLite for extraction/staging, PostgreSQL+AGE for production graph

**Rationale**:
- SQLite: Fast, local, easy to debug, no server setup
- PostgreSQL: Complex graph queries, vector search, production-ready
- Separation: Entity resolution vs. graph traversal are different problems

### 2024-12-17: JSON Intermediate Format

**Decision**: Extract to JSON files, then bulk import to database

**Rationale**:
- Version control: Git diff shows extraction changes
- Debugging: Inspect individual papers easily
- Portability: Import to any database (Neo4j, AGE, etc.)
- Incremental: Reprocess just one paper if needed
- Testable: Validate against JSON schema

### 2024-12-17: HIV ≠ AIDS at Entity Layer

**Decision**: Keep HIV and AIDS as separate entities

**Rationale**: The controversy is about the RELATIONSHIP, not the entities themselves. Different papers make different claims about HIV→AIDS. Entity layer separates entities; claims layer captures the disputed relationships.

### 2024-12-17: Embeddings for Entity Resolution

**Decision**: Use semantic similarity to cluster entity variants

**Rationale**: Simple string matching misses variants like "HIV"/"HTLV-III"/"LAV". Embeddings enable semantic clustering to map these to the same canonical entity.

### 2024-12-17: CPU-Only PyTorch

**Decision**: Use `--extra-index-url` for CPU-only PyTorch

**Rationale**: Full CUDA PyTorch is 5GB+. We don't need GPU for this pipeline (batch processing, not real-time). CPU-only reduces image from 8.5GB to 1.5GB.

---

## Breaking Changes

### None yet

This is version 0.1.0 - first release. All APIs subject to change.

---

## Migration Guide

### Not applicable yet

This is the first release. Future versions will include migration guides here.

---

## Known Bugs

### Entity Extraction (Stage 1)

1. **Noisy extraction** - Still catches fragments like "enter", "chronic"
   - **Status**: Partially fixed with stopword list and confidence threshold
   - **TODO**: Expand stopword list, possibly add POS tagging

2. **No entity clustering** - "HIV" and "HTLV-III" treated as separate
   - **Status**: By design - will be fixed in Stage 3 (embeddings)
   - **Workaround**: Manual mapping in SQLite if needed

3. **Short acronyms** - Sometimes catches "LA", "Ac", "op" as diseases
   - **Status**: Partially fixed with 3-char minimum
   - **TODO**: Add acronym dictionary or context checking

---

## Performance Metrics

### Stage 1 (Entity Extraction)

| Metric | Value |
|--------|-------|
| Docker build time | 5-10 minutes |
| Docker image size | 1.5 GB |
| Model download (first build) | 431 MB |
| Processing time (9 XML files) | ~3 seconds |
| Entities extracted | 12 |
| Co-occurrence edges | 24 |
| False positive rate | ~30% (needs improvement) |

### Planned (Full Pipeline)

| Papers | Estimated Time |
|--------|----------------|
| 100 | ~5 minutes |
| 1,000 | ~1 hour |
| 10,000 | ~10 hours |

*Times will improve with parallelization and caching*

---

## Dependencies

### Current

```
Python 3.11
torch>=2.1.0 (CPU-only)
transformers>=4.36.0
pandas>=2.0.3
scikit-learn>=1.3.0
lxml>=4.9.3
psycopg2-binary>=2.9.9
```

### Planned

```
sentence-transformers>=2.2.0 (Stage 3)
pgvector (Stage 6)
apache-age (Stage 6)
```

---

## Contributors

- Will Ware (@wware)

---

## License

TBD

---

## References

- **GitHub Issue #20**: Three-layer KG architecture discussion
- **BioBERT Paper**: https://arxiv.org/abs/1901.08746
- **PMC Open Access**: https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/
- **Apache AGE**: https://age.apache.org/
