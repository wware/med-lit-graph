# Design Decisions

This document explains the key architectural and design decisions made for the Medical Knowledge Graph project, including trade-offs and rationale.

## Table of Contents

1. [Provenance as a First-Class Citizen](#provenance-as-a-first-class-citizen)
2. [Immutable Source of Truth (JSON Files)](#immutable-source-of-truth-json-files)
3. [JSON Query Language vs Native Graph QLs](#json-query-language-vs-native-graph-qls)
4. [Evidence Quality Weighting](#evidence-quality-weighting)
5. [Hybrid Graph RAG Architecture](#hybrid-graph-rag-architecture)
6. [Per-Paper JSON vs Centralized Database](#per-paper-json-vs-centralized-database)
7. [PostgreSQL vs Graph Databases](#postgresql-vs-graph-databases)
8. [OpenSearch vs PostgreSQL for Vector Search](#opensearch-vs-postgresql-for-vector-search)
9. [MCP Integration](#mcp-integration)
10. [Pydantic for Schema Validation](#pydantic-for-schema-validation)

---

## 1. Provenance as a First-Class Citizen

### Decision
**ALL medical relationships MUST include evidence. Evidence is not optional.**

### Rationale

**Problem we're solving:**
- Doctors don't trust AI/ML systems that can't explain their sources
- Existing medical knowledge bases lack citation traceability
- Researchers can't verify or audit data quality
- Users can't distinguish high-quality evidence (RCTs) from low-quality (case reports)

**Our approach:**
```python
class MedicalRelationship(BaseRelationship):
    evidence: list[Evidence] = Field(
        min_length=1,  # MANDATORY - Cannot be empty
        description="Evidence supporting this relationship"
    )
```

Every piece of evidence must specify:
- `paper_id`: Which PMC paper
- `section_type`: Where in the paper (results, methods, discussion)
- `paragraph_idx`: Exact paragraph number
- `extraction_method`: How it was extracted (for reproducibility)
- `confidence`: Confidence in this specific piece of evidence
- `study_type`: RCT, meta-analysis, observational, etc.

### Trade-offs

**Pros:**
- ✅ Full traceability - doctors can verify every claim
- ✅ Quality filtering - filter by evidence type (RCTs only)
- ✅ Confidence scoring based on actual evidence
- ✅ Reproducibility - know exactly how data was extracted
- ✅ Audit trail for regulatory compliance

**Cons:**
- ⚠️ Storage overhead (~20-30% more data)
- ⚠️ Extraction complexity (must track provenance during NER)
- ⚠️ Cannot quickly add relationships without evidence

**Why pros outweigh cons:**
For medical applications, trustworthiness >> storage costs. A doctor won't use a system that says "this drug treats that disease (trust me)" without citations.

### Alternative Approaches Considered

**1. Optional provenance (what most systems do)**
```python
evidence: Optional[list[Evidence]] = None
```
**Rejected because**: Allows lazy implementation. Would gradually degrade to unprovable claims.

**2. Lightweight provenance (just paper IDs)**
```python
source_papers: list[str]
```
**Rejected because**: Not enough for verification. Need to know WHERE in the paper.

**3. Hybrid approach (what we DO support)**
```python
# Mandatory minimum
evidence: list[Evidence]  # Must have at least one

# Can be lightweight
Evidence(
    paper_id="PMC123",
    section_type="results",
    paragraph_idx=5,
    extraction_method="llm",
    confidence=0.85
)

# Or rich
Evidence(
    paper_id="PMC123",
    section_type="results",
    paragraph_idx=5,
    sentence_idx=2,
    text_span="Exact quote from paper",
    extraction_method="llm",
    confidence=0.85,
    study_type="rct",
    sample_size=302
)
```

This balances mandatory provenance with flexible richness.

---

## 2. Immutable Source of Truth (JSON Files)

### Decision
**Per-paper JSON files are the immutable source of truth. Graph database is regenerated from JSON.**

### Rationale

**Problem we're solving:**
- Graph databases can become corrupted
- Can't roll back to previous states easily
- Hard to track what changed and why
- Algorithm improvements require re-ingesting everything
- No audit trail of data provenance

**Our approach:**
```
papers/
  PMC123456-v1.json
  PMC123456-v2.json (corrected)
  PMC789012-v1.json
  PMC789012-retracted.json
```

Each JSON file is:
- Immutable (never modified, only new versions)
- Complete (entire knowledge graph for that paper)
- Versioned (track corrections and updates)
- Self-contained (can rebuild graph from scratch)

### Trade-offs

**Pros:**
- ✅ Complete reproducibility
- ✅ Easy rollback (delete file, regenerate graph)
- ✅ Version history (track algorithm improvements)
- ✅ Audit trail (know when/how data extracted)
- ✅ Backup is simple (versioned object storage)
- ✅ Parallel processing (each JSON independent)

**Cons:**
- ⚠️ Storage cost (~1-5MB per paper)
- ⚠️ Graph regeneration takes time
- ⚠️ Duplication (data in both JSON and graph DB)

**Storage considerations:**
- Per-paper JSON files scale linearly with corpus size
- Object storage with versioning provides cost-effective archival
- Trade-off: storage cost vs. reproducibility and data integrity

### Alternative Approaches Considered

**1. Graph database is source of truth**
**Rejected because:**
- Database corruption = data loss
- No version history
- Hard to track changes
- Can't re-run extraction algorithms

**2. Store deltas/diffs instead of full files**
**Rejected because:**
- Complex to reconstruct
- Higher risk of corruption
- No independent validation

**3. Hybrid: JSON + database both authoritative**
**Rejected because:**
- Which is source of truth when they conflict?
- Complexity of keeping in sync

### Implementation Details

**Regeneration strategy:**
```python
def regenerate_graph(since: datetime):
    """Rebuild graph from JSON files modified after 'since'"""
    papers = storage.list_objects(prefix="papers/", modified_after=since)

    for paper_json in papers:
        if paper_json['status'] == 'retracted':
            graph_db.delete_paper(paper_json['paper_id'])
        else:
            graph_db.upsert_paper(paper_json)
```

**Versioning strategy:**
- `PMC123456-v1.json`: Initial ingestion
- `PMC123456-v2.json`: Correction or better extraction
- `PMC123456-retracted.json`: Paper retracted (keep for history)

**When to regenerate:**
- Paper retracted: Immediate
- Algorithm improved: Batch (nightly/weekly)
- Data corruption detected: Automatic from backup

---

## 3. JSON Query Language vs Native Graph QLs

### Decision
**Use a vendor-neutral JSON query language that translates to SQL (PostgreSQL), not direct SQL or complex Graph QLs.**

### Rationale

**Problem we're solving:**
- GraphQL and Graph QLs (Cypher/Gremlin) can be complex for standard relational tasks
- Switching databases = rewrite all queries
- LLMs are excellent at JSON but can sometimes hallucinate complex SQL joins
- A JSON abstraction allows us to optimize the underlying SQL generation
- Users can't easily learn yet another query language

**Our approach:**
```json
{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "edge_pattern": {"relation_type": "treats"},
  "filters": [{"field": "target.name", "operator": "eq", "value": "diabetes"}]
}
```

This translates to an optimized PostgreSQL SQL query involving joins between `entities`, `relationships`, and `evidence` tables.

### Trade-offs

**Pros:**
- ✅ Database-agnostic (could switch back to Graph DB if needed)
- ✅ LLM-friendly (JSON is natural for AI to generate)
- ✅ SQL Optimization (translator handles complex JOIN logic)
- ✅ Human-readable (no learning curve)
- ✅ Type-safe (Pydantic validation)
- ✅ Consistent interface across deployments

**Cons:**
- ⚠️ Translation layer overhead (~10-20ms per query)
- ⚠️ Cannot use database-specific optimizations
- ⚠️ Additional code to maintain (translator)
- ⚠️ Slightly less expressive than native QLs

**Why pros outweigh cons:**
- 10-20ms translation is negligible vs ~100-500ms query execution
- Vendor lock-in risk >> performance hit
- LLM integration is critical for AI-powered queries

### Alternative Approaches Considered

**1. Direct SQL Queries**
**Rejected because:**
- Vendor lock-in
- Hard for LLMs
- Not composable

**2. GraphQL**
**Rejected because:**
- Designed for CRUD, not graph traversal
- Doesn't map well to multi-hop queries
- Still needs backend translation

**3. SPARQL (RDF)**
**Rejected as primary, kept as export:**
- Too complex for users
- RDF reasoning is overkill
- But we DO support RDF export for semantic web

### Performance Considerations

**Query translation time:**
- Simple query: ~2-5ms
- Complex path query (Recursive CTE): ~10-15ms
- **Negligible compared to query execution**

**Caching strategy:**
```python
@lru_cache(maxsize=1000)
def translate_to_sql(query: GraphQuery) -> str:
    return SQLQueryExecutor().translate(query)
```

Common queries cached in-memory.

---

## 4. Evidence Quality Weighting

### Decision
**Confidence scores are automatically calculated from evidence quality, not manually assigned.**

### Rationale

**Problem we're solving:**
- Not all studies are equal (RCT >> case report)
- Manual confidence assignment is subjective and inconsistent
- Users can't tell why confidence is high or low
- No way to filter by evidence type

**Our approach:**
```python
study_weights = {
    'rct': 1.0,              # Randomized controlled trial (gold standard)
    'meta_analysis': 0.95,   # Systematic review
    'cohort': 0.8,           # Longitudinal observational
    'case_control': 0.7,     # Retrospective
    'observational': 0.6,    # General observation
    'case_report': 0.4,      # Single patient
    'review': 0.5            # Literature review (not systematic)
}

# Weighted average
confidence = sum(ev.confidence * weight(ev.study_type) for ev in evidence) / sum(weights)
```

### Trade-offs

**Pros:**
- ✅ Objective and consistent
- ✅ Transparent (users see evidence breakdown)
- ✅ Filterable (show only RCT-supported claims)
- ✅ Updatable (adjust weights based on feedback)
- ✅ Evidence-based medicine principles

**Cons:**
- ⚠️ Study type classification must be accurate
- ⚠️ Weights are somewhat subjective
- ⚠️ Doesn't account for study quality within types

**Why pros outweigh cons:**
- Consistent weighting >> manual assignment
- Users can inspect evidence and judge for themselves
- Can be refined based on domain expert feedback

### Alternative Approaches Considered

**1. Manual confidence assignment**
**Rejected because:**
- Subjective and inconsistent
- Can't explain to users

**2. Machine learning confidence**
**Considered for future:**
- Train on expert-labeled examples
- Account for more factors (sample size, journal IF, citation count)
- Currently out of scope

**3. Simple average**
**Rejected because:**
- Treats all evidence equally
- RCT = case report is wrong

### Validation

**Example calculation:**
```python
evidence = [
    Evidence(paper_id="PMC1", confidence=0.9, study_type="rct"),          # weight 1.0
    Evidence(paper_id="PMC2", confidence=0.8, study_type="cohort"),       # weight 0.8
    Evidence(paper_id="PMC3", confidence=0.7, study_type="case_report")   # weight 0.4
]

# Weighted: (0.9*1.0 + 0.8*0.8 + 0.7*0.4) / (1.0 + 0.8 + 0.4) = 0.82
# Simple average: (0.9 + 0.8 + 0.7) / 3 = 0.80

# Weighted is higher because RCT weighted more
```

---

## 5. Hybrid Graph RAG Architecture

### Decision
**Combine vector search + graph traversal, not just one or the other.**

### Rationale

**Problem we're solving:**
- Pure vector search misses multi-hop relationships
- Pure graph traversal misses semantic similarity
- Users need both semantic relevance AND relational structure

**Our approach:**
```
Query: "What drugs treat BRCA-mutated breast cancer?"

Step 1: Vector Search
- Semantic search for "BRCA breast cancer treatment"
- Returns relevant paper chunks

Step 2: Graph Traversal
- BRCA1 --[increases_risk]--> breast cancer
- breast cancer <--[treated_by]-- drugs
- Filter: drugs with evidence specific to BRCA

Step 3: Hybrid Ranking
- Combine vector similarity score + graph centrality
- Rank: (0.7 * vector_score) + (0.3 * graph_score)
```

### Trade-offs

**Pros:**
- ✅ Best of both worlds
- ✅ Finds multi-hop connections (graph)
- ✅ Semantic search (vector)
- ✅ More comprehensive results

**Cons:**
- ⚠️ Two databases to maintain
- ⚠️ Complex query planning
- ⚠️ Higher infrastructure cost

**Infrastructure considerations:**
- Dual database approach requires more resources than single-database solutions
- Trade-off: comprehensive results vs. infrastructure complexity
- Both vector and graph capabilities are essential for medical knowledge queries

### Alternative Approaches Considered

**1. Vector-only (like many RAG systems)**
**Rejected because:**
- Misses drug mechanisms (multi-hop)
- Can't answer "what connects X to Y?"

**2. Graph-only (like traditional knowledge graphs)**
**Rejected because:**
- Misses semantic similarity
- Hard to search free text

**3. Hybrid with single database**
**Considered but:**
- Separation of concerns provides flexibility
- Each database optimized for its purpose
- Easier to scale independently

---

## 6. Per-Paper JSON vs Centralized Database

### Decision
**Store complete knowledge graph per paper in JSON, not centralized relational DB.**

### Rationale

See [Decision #2](#2-immutable-source-of-truth-json-files) for full details.

**Key point**: Reproducibility and auditability are more important than storage efficiency for medical applications.

---

## 7. PostgreSQL vs Graph Databases (Neptune/Neo4j)

### Decision
**Use PostgreSQL with a relational schema optimized for graph-like queries.**

### Rationale

**Why PostgreSQL:**
- ✅ Mature, reliable, and widely available
- ✅ Strong consistency and ACID compliance
- ✅ Excellent performance for 1-2 hop relationships with proper indexing
- ✅ Recursive CTEs support multi-hop path queries
- ✅ Lower operational complexity than managed graph services like Neptune

**Why not Neptune/Neo4j (initially considered):**
- ⚠️ Higher cost for managed instances (Neptune)
- ⚠️ Niche query languages (Gremlin/Cypher) that are harder to integrate with standard toolchains
- ⚠️ "Graph-first" performance only really shines at 4+ hops, which is rare in our current use cases

### Trade-offs

- Pros: Low cost, high reliability, standard SQL skills, powerful CTEs.
- Cons: Slightly more complex SQL for deeply nested relationships compared to Cypher.

**Decision**: PostgreSQL is the primary store for entities, relationships, and evidence.

---

## 8. OpenSearch vs PostgreSQL for Vector Search

### Decision
**Use OpenSearch (with k-NN plugin) for vector search, not pgvector.**

### Rationale

**Why OpenSearch:**
- ✅ Purpose-built for search
- ✅ HNSW algorithm (state of the art)
- ✅ Hybrid search (vector + BM25 keyword)
- ✅ Scales horizontally
- ✅ Elasticsearch-compatible

**Why not pgvector:**
- ⚠️ PostgreSQL not designed for vector search
- ⚠️ Slower at scale
- ⚠️ No hybrid search built-in
- ⚠️ Would need additional keyword search

### Trade-offs

**OpenSearch:**
- Pros: Fast, scalable, hybrid search
- Cons: Separate database, higher cost

**pgvector:**
- Pros: Single database, lower cost
- Cons: Slower, less scalable

**Decision**: OpenSearch for production. pgvector for tiny deployments.

> [!NOTE]
> For local development and entity deduplication in the ingestion pipeline, **ChromaDB** is used as a lightweight, persistent vector store.

---

## 9. MCP Integration

### Decision
**Provide MCP server for LLM integration, not just REST API.**

### Rationale

**Problem we're solving:**
- LLMs need structured ways to query external data
- REST APIs require custom integration for each LLM
- MCP is emerging standard (backed by Anthropic, OpenAI, Google)

**Our MCP server:**
```typescript
{
  "tools": [
    {
      "name": "search_treatments",
      "description": "Find drugs that treat a disease",
      "inputSchema": {...}
    },
    {
      "name": "find_disease_genes",
      "description": "Find genes associated with a disease",
      "inputSchema": {...}
    }
  ]
}
```

LLMs can now query medical knowledge natively.

### Trade-offs

**Pros:**
- ✅ LLM-native integration
- ✅ Works with Claude, ChatGPT, Gemini
- ✅ Follows emerging standard
- ✅ Simple for LLM developers

**Cons:**
- ⚠️ MCP is still young (v1.0 just released)
- ⚠️ Must maintain MCP server alongside API

**Why pros outweigh cons:**
- Medical Q&A is primary use case
- LLMs are the interface doctors will use
- MCP adoption is growing rapidly

---

## 10. Pydantic for Schema Validation

### Decision
**Use Pydantic v2 for all data models and validation.**

### Rationale

**Why Pydantic:**
- ✅ Runtime validation
- ✅ JSON serialization built-in
- ✅ Type hints for IDE support
- ✅ Automatic docs generation
- ✅ Wide Python ecosystem support

**Example:**
```python
class Treats(MedicalRelationship):
    response_rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('evidence')
    @classmethod
    def validate_evidence_not_empty(cls, v):
        if not v:
            raise ValueError("Evidence required")
        return v
```

Impossible to create invalid data.

### Alternative Approaches Considered

**1. Dataclasses**
**Rejected because:**
- No validation
- No serialization

**2. attrs**
**Rejected because:**
- Less ecosystem support
- Pydantic is standard

**3. No validation**
**Rejected because:**
- Medical data must be validated
- Errors could be dangerous

---

## Summary of Key Decisions

| Decision | Rationale | Trade-off Accepted |
|----------|-----------|-------------------|
| **Mandatory provenance** | Trust and verification | Storage overhead |
| **JSON source of truth** | Reproducibility | Duplication |
| **JSON query language** | Vendor neutrality | Translation overhead |
| **Evidence weighting** | Objectivity | Classification accuracy |
| **Hybrid RAG** | Comprehensive results | Infrastructure cost |
| **PostgreSQL** | Mature & Reliable | SQL Complexity for deep hops |
| **OpenSearch** | Purpose-built search | Separate database |
| **MCP integration** | LLM-native | Young standard |
| **Pydantic validation** | Data quality | Runtime cost |

---

## Decision Process

For each major architectural decision, we follow this process:

1. **Identify the problem** we're solving
2. **List alternative approaches** with pros/cons
3. **Analyze trade-offs** (performance, cost, complexity)
4. **Consider long-term implications** (5-10 year horizon)
5. **Choose the approach** that best serves our users
6. **Document the decision** for future reference

**Principle**: Choose simplicity and correctness over performance. Medical applications require trustworthiness above all else.
