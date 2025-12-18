# Database Schema Design

## Overview

This document describes the database schemas for all pipeline stages.

Current implementation: **Stage 1 only (entities.db)**
Planned: Stages 2-6

**Key Design Principles:**
- **Pydantic models** as source of truth (type safety, validation)
- **SQLite** for canonical entity storage and staging
- **PostgreSQL/AGE** for graph queries and visualization
- **Full provenance tracking** for reproducibility

---

## Stage 1: Entity Extraction

**Database**: `entities.db` (SQLite)
**Purpose**: Canonical entity storage with alias mappings
**Implementation**: `pmc_ner_pipeline.py` + `db_serialization.py`

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Layer                            │
│  (Pydantic Models - Source of Truth)                        │
│                                                             │
│  - base.py: EntityType, EntityReference, Edges              │
│  - entity.py: Disease, Gene, Drug, etc.                     │
│  - relationship.py: Treats, Causes, etc.                    │
└──────────────┬─────────────────────────┬────────────────────┘
               │                         │
               │ serialize               │ serialize
               │                         │
    ┌──────────▼──────────┐   ┌─────────▼────────────┐
    │   SQLite Store      │   │  PostgreSQL/AGE      │
    │ (Canonical Entities)│   │  (Graph Store)       │
    │                     │   │                      │
    │ - entities table    │   │ - Cypher queries     │
    │ - aliases table     │   │ - Vertices/Edges     │
    │ - JSON storage      │   │ - Graph traversal    │
    └─────────────────────┘   └──────────────────────┘
```

### Tables

```sql
-- Stores full Pydantic models as JSON
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE,           -- "DISEASE:hiv" (from Pydantic model)
    canonical_name TEXT,             -- "HIV"
    type TEXT,                       -- "disease" (lowercase EntityType)
    entity_json TEXT,                -- Full JSON of Disease/Gene/Drug model
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Aliases for entity resolution
CREATE TABLE aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_db_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    name TEXT UNIQUE,
    source TEXT,  -- PMC ID where this alias was found
    confidence REAL,  -- NER confidence score
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Pydantic Models

**Entity Types** (from `entity.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class Disease(BaseModel):
    """Disease entity with UMLS/ICD-10 codes."""
    entity_id: str  # e.g., "DISEASE:hiv" or "C0019693" (UMLS)
    name: str
    umls_id: Optional[str] = None
    icd10_codes: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    abbreviations: List[str] = Field(default_factory=list)
    source: str = "extracted"  # or "umls", "manual"

class Gene(BaseModel):
    """Gene entity with NCBI/HGNC codes."""
    entity_id: str  # e.g., "GENE:tp53"
    name: str
    ncbi_id: Optional[str] = None
    hgnc_id: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)

class Drug(BaseModel):
    """Drug entity with RxNorm codes."""
    entity_id: str  # e.g., "DRUG:metformin"
    name: str
    rxnorm_id: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
```

### Serialization Helpers

**From `db_serialization.py`**:

```python
# Store Pydantic model in SQLite
def serialize_entity_to_sqlite(entity: Disease | Gene | Drug) -> dict:
    """Converts Pydantic model to dict for SQLite INSERT."""
    return {
        "entity_id": entity.entity_id,
        "canonical_name": entity.name,
        "type": entity.__class__.__name__.lower(),
        "entity_json": entity.model_dump_json(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

# Load Pydantic model from SQLite
def deserialize_entity_from_sqlite(row: dict, entity_type: EntityType) -> Disease | Gene | Drug:
    """Reconstructs Pydantic model from SQLite row."""
    entity_json = json.loads(row["entity_json"])
    if entity_type == EntityType.DISEASE:
        return Disease(**entity_json)
    elif entity_type == EntityType.GENE:
        return Gene(**entity_json)
    # ... etc
```

### Example Data

```python
# Create validated entity
disease = Disease(
    entity_id="DISEASE:hiv",
    name="HIV",
    umls_id="C0019693",
    synonyms=["Human Immunodeficiency Virus", "AIDS virus"],
    abbreviations=["HIV-1", "HTLV-III", "LAV"],
    source="extracted"
)

# Store in SQLite
row = serialize_entity_to_sqlite(disease)
conn.execute("""
    INSERT INTO entities (entity_id, canonical_name, type, entity_json, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", (row["entity_id"], row["canonical_name"], row["type"], row["entity_json"],
      row["created_at"], row["updated_at"]))

# Create aliases
for alias in disease.abbreviations:
    conn.execute("""
        INSERT INTO aliases (entity_db_id, name, source, confidence)
        VALUES (?, ?, ?, ?)
    """, (entity_db_id, alias, "PMC322947", 0.95))
```

### Indexes

```sql
CREATE INDEX idx_entities_entity_id ON entities(entity_id);
CREATE INDEX idx_entities_canonical_name ON entities(canonical_name);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_aliases_entity_db_id ON aliases(entity_db_id);
CREATE INDEX idx_aliases_name ON aliases(name);

-- JSON query support
CREATE INDEX idx_entities_umls ON entities(json_extract(entity_json, '$.umls_id'));
```

### Three-Layer Edge Architecture

The schema supports three distinct edge types (from ChatGPT recommendations):

#### 1. ExtractionEdge (What the model said)
```python
ExtractionEdge(
    subject=EntityReference(id="DRUG:metformin", name="Metformin", type=EntityType.DRUG),
    object=EntityReference(id="DISEASE:diabetes", name="Type 2 Diabetes", type=EntityType.DISEASE),
    extractor=ModelInfo(name="biobert", version="1.0", ...),
    confidence=0.92
)
```
- Raw output from NER/extraction models
- Disposable (can regenerate with better models)
- Includes model version for reproducibility

#### 2. ClaimEdge (What the paper claims)
```python
ClaimEdge(
    subject=drug_ref,
    object=disease_ref,
    predicate=ClaimPredicate.TREATS,
    asserted_by="PMC123456",
    polarity=Polarity.SUPPORTS
)
```
- Paper-level assertions
- Citable and versioned
- Can contradict each other

#### 3. EvidenceEdge (Empirical evidence)
```python
EvidenceEdge(
    subject=drug_ref,
    object=disease_ref,
    evidence_type=EvidenceType.CLINICAL_TRIAL,
    strength=0.95,
    sample_size=500
)
```
- Fine-grained evidence from experiments
- Multi-modal (text, stats, figures)
- Reusable across claims

### Provenance Tracking

Every extraction includes complete provenance metadata:

```python
ExtractionProvenance(
    extraction_pipeline=ExtractionPipelineInfo(
        name="pmc_ner_pipeline",
        version="1.0.0",
        git_commit="abc123...",
        git_branch="main"
    ),
    models={"ner": ModelInfo(name="biobert_ncbi_disease_ner", version="1.0")},
    prompt=PromptInfo(version="v1", template="ner_biobert_ncbi_disease"),
    execution=ExecutionInfo(
        timestamp="2025-12-18T12:00:00Z",
        hostname="server-01",
        duration_seconds=45.3
    ),
    entity_resolution=EntityResolutionInfo(
        canonical_entities_matched=150,
        new_entities_created=50
    )
)
```

**Saved to**: `/app/output/extraction_provenance.json`

### Output Files

After running `pmc_ner_pipeline.py`:

1. **`entities.db`** (SQLite)
   - Canonical entities with full Pydantic models as JSON
   - Aliases for entity resolution

2. **`extraction_edges.jsonl`** (JSONL)
   - One ExtractionEdge object per line
   - Ready for AGE import
   - Full provenance in each edge

3. **`extraction_provenance.json`** (JSON)
   - Complete extraction metadata
   - Pipeline version, git commit, models used

4. **`nodes.csv`, `edges.csv`** (Legacy CSV)
   - Simple format for inspection/debugging
   - Kept for backward compatibility

---

## Stage 2: Provenance

**Database**: `provenance.db` (SQLite)
**Purpose**: Paper metadata and document structure

### Tables

```sql
CREATE TABLE papers (
    pmc_id TEXT PRIMARY KEY,
    pmid TEXT,
    title TEXT,
    journal TEXT,
    pub_date DATE,
    authors TEXT,  -- JSON array: [{"name": "...", "affiliation": "..."}]
    doi TEXT,
    keywords TEXT,  -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,  -- e.g., "PMC322947_abstract"
    paper_id TEXT REFERENCES papers(pmc_id) ON DELETE CASCADE,
    section_type TEXT,  -- abstract, intro, methods, results, discussion, conclusion
    section_order INTEGER,
    title TEXT
);

CREATE TABLE paragraphs (
    paragraph_id TEXT PRIMARY KEY,  -- e.g., "PMC322947_abstract_p1"
    section_id TEXT REFERENCES sections(section_id) ON DELETE CASCADE,
    paragraph_order INTEGER,
    text TEXT,
    start_char INTEGER,  -- Position in full document
    end_char INTEGER
);

CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper TEXT REFERENCES papers(pmc_id),
    cited_reference TEXT,  -- PMID, DOI, or freetext
    context TEXT,  -- Sentence containing citation
    paragraph_id TEXT REFERENCES paragraphs(paragraph_id)
);
```

### Example Data

```sql
INSERT INTO papers VALUES (
    'PMC322947',
    '3003749',
    'Detection of lymphocytes expressing HTLV-III...',
    'Proc Natl Acad Sci U S A',
    '1986-02-01',
    '[{"name": "Harper ME"}, {"name": "Gallo RC"}]',
    '10.1073/pnas.83.3.772',
    '["HIV", "lymphocytes", "in situ hybridization"]',
    '2024-12-17 20:00:00'
);
```

---

## Stage 3: Embeddings

**Extension to existing databases**
**Purpose**: Semantic similarity for entity resolution and search

### Entity Embeddings

```sql
-- Add to entities.db
CREATE TABLE entity_embeddings (
    entity_id INTEGER PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    embedding BLOB,  -- 768-dim float32 array serialized
    model_name TEXT,  -- e.g., "sentence-transformers/all-mpnet-base-v2"
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_embeddings ON entity_embeddings(entity_id);
```

### Paragraph Embeddings

```sql
-- Add to provenance.db
CREATE TABLE paragraph_embeddings (
    paragraph_id TEXT PRIMARY KEY REFERENCES paragraphs(paragraph_id) ON DELETE CASCADE,
    embedding BLOB,
    model_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Storage Format

```python
import numpy as np

# Store
embedding = np.array([0.12, 0.34, ...], dtype=np.float32)
embedding_bytes = embedding.tobytes()
conn.execute("INSERT INTO entity_embeddings VALUES (?, ?, ?, datetime('now'))",
             (entity_id, embedding_bytes, "all-mpnet-base-v2"))

# Load
row = conn.execute("SELECT embedding FROM entity_embeddings WHERE entity_id=?", 
                   (entity_id,)).fetchone()
embedding = np.frombuffer(row[0], dtype=np.float32)
```

---

## Stage 4: Claims

**Database**: `claims.db` (SQLite)
**Purpose**: Semantic relationships with provenance

### Tables

```sql
CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,  -- e.g., "PMC322947_claim_1"
    paper_id TEXT,
    section_id TEXT,
    paragraph_id TEXT,
    subject_entity_id INTEGER,  -- References entities.id
    predicate TEXT,  -- CAUSES, CORRELATES_WITH, INFECTS, DETECTED_IN, etc.
    object_entity_id INTEGER,
    extracted_text TEXT,  -- The actual sentence
    confidence REAL,
    evidence_type TEXT,  -- epidemiological, molecular, clinical, statistical
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (paper_id) REFERENCES papers(pmc_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id),
    FOREIGN KEY (paragraph_id) REFERENCES paragraphs(paragraph_id)
);

CREATE TABLE claim_embeddings (
    claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id) ON DELETE CASCADE,
    embedding BLOB,
    model_name TEXT,
    created_at DATETIME
);
```

### Predicate Taxonomy

```
CAUSATION:
  - CAUSES
  - PREVENTS
  - INHIBITS
  - PROMOTES

DETECTION:
  - DETECTED_IN
  - FOUND_IN
  - ISOLATED_FROM

ASSOCIATION:
  - CORRELATES_WITH
  - ASSOCIATED_WITH
  - LINKED_TO

BIOLOGICAL:
  - INFECTS
  - BINDS_TO
  - ACTIVATES
  - SUPPRESSES

CLINICAL:
  - TREATS
  - DIAGNOSED_BY
  - PROGRESSES_TO
  - INDICATES
```

### Example Data

```sql
INSERT INTO claims VALUES (
    'PMC322947_claim_1',
    'PMC322947',
    'PMC322947_results',
    'PMC322947_results_p2',
    42,  -- HTLV-III entity_id
    'INFECTS',
    56,  -- lymphocytes entity_id
    'HTLV-III-infected cells expressing viral RNA were detected in 6 of 7 lymph nodes',
    0.92,
    'molecular',
    '2024-12-17 20:00:00'
);
```

---

## Stage 5: Evidence

**Database**: `evidence.db` (SQLite)
**Purpose**: Supporting/refuting evidence for claims

### Tables

```sql
CREATE TABLE evidence (
    evidence_id TEXT PRIMARY KEY,
    claim_id TEXT REFERENCES claims(claim_id) ON DELETE CASCADE,
    supports BOOLEAN,  -- TRUE=supports, FALSE=refutes
    strength TEXT CHECK(strength IN ('high', 'medium', 'low')),
    type TEXT,  -- method type: in_situ_hybridization, PCR, ELISA, cohort_study, etc.
    paragraph_id TEXT REFERENCES paragraphs(paragraph_id),
    details TEXT,  -- JSON with method-specific information
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evidence_metrics (
    evidence_id TEXT PRIMARY KEY REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    sample_size INTEGER,
    detection_rate REAL,
    p_value REAL,
    confidence_interval TEXT,
    statistical_test TEXT,
    other_metrics TEXT  -- JSON for method-specific metrics
);
```

### Example Data

```sql
-- Evidence supporting PMC322947_claim_1
INSERT INTO evidence VALUES (
    'PMC322947_ev_1',
    'PMC322947_claim_1',
    TRUE,
    'high',
    'in_situ_hybridization',
    'PMC322947_methods_p5',
    '{"probe": "35S-labeled RNA", "detection_method": "autoradiography"}',
    '2024-12-17 20:00:00'
);

INSERT INTO evidence_metrics VALUES (
    'PMC322947_ev_1',
    7,  -- 7 lymph nodes examined
    0.857,  -- 6/7 positive = 85.7%
    NULL,
    NULL,
    NULL,
    '{"positive_samples": 6, "total_samples": 7}'
);
```

---

## Stage 6: PostgreSQL + Apache AGE

**Purpose**: Graph database for complex queries and visualization
**Integration**: Imports from SQLite databases and JSONL files

### Cypher Generation Helpers

**From `db_serialization.py`**:

```python
# Create entity vertex from Pydantic model
def cypher_create_vertex(entity: Disease | Gene | Drug) -> str:
    """Generates Cypher CREATE statement for entity vertex."""
    entity_type = entity.__class__.__name__.lower()
    properties = entity.model_dump_json()
    return f"""
    CREATE (n:{entity_type} {{
        entity_id: '{entity.entity_id}',
        properties: '{properties}'
    }})
    """

# Create extraction edge
def cypher_create_edge(edge: ExtractionEdge) -> str:
    """Generates Cypher for ExtractionEdge."""
    return f"""
    MATCH (s {{entity_id: '{edge.subject.id}'}})
    MATCH (o {{entity_id: '{edge.object.id}'}})
    CREATE (s)-[r:EXTRACTION_EDGE {{
        confidence: {edge.confidence},
        extractor: '{edge.extractor.name}',
        extractor_version: '{edge.extractor.version}'
    }}]->(o)
    """

# Create medical relationship
def cypher_create_relationship(rel: Treats | Causes) -> str:
    """Generates Cypher for medical relationship edge."""
    rel_type = rel.__class__.__name__.upper()
    properties = rel.model_dump_json()
    return f"""
    MATCH (s {{entity_id: '{rel.subject_id}'}})
    MATCH (o {{entity_id: '{rel.object_id}'}})
    CREATE (s)-[r:{rel_type} {{properties: '{properties}'}}]->(o)
    """
```

### Node Types

```cypher
// Paper nodes
CREATE (:paper {
    pmc_id: 'PMC322947',
    title: '...',
    pub_date: date('1986-02-01'),
    authors: ['Gallo RC', 'Harper ME'],
    journal: 'Proc Natl Acad Sci U S A'
})

// Entity nodes (from entities.db via Pydantic models)
CREATE (:disease {
    entity_id: 'DISEASE:hiv',
    properties: '{"entity_id": "DISEASE:hiv", "name": "HIV", "umls_id": "C0019693", ...}'
})

CREATE (:drug {
    entity_id: 'DRUG:metformin',
    properties: '{"entity_id": "DRUG:metformin", "name": "Metformin", "rxnorm_id": "6809", ...}'
})

// Claim nodes
CREATE (:claim {
    claim_id: 'PMC322947_claim_1',
    predicate: 'INFECTS',
    extracted_text: '...',
    confidence: 0.92
})

// Evidence nodes
CREATE (:evidence {
    evidence_id: 'PMC322947_ev_1',
    type: 'in_situ_hybridization',
    strength: 'high'
})
```

### Edge Types

```cypher
// ExtractionEdge - what the NER model found
(e1:entity)-[:EXTRACTION_EDGE {
    confidence: 0.92,
    extractor: 'biobert',
    extractor_version: '1.0'
}]->(e2:entity)

// ClaimEdge - what the paper asserts
(e1:entity)-[:CLAIM_EDGE {
    predicate: 'TREATS',
    asserted_by: 'PMC123456',
    polarity: 'supports'
}]->(e2:entity)

// EvidenceEdge - empirical support
(e1:entity)-[:EVIDENCE_EDGE {
    evidence_type: 'clinical_trial',
    strength: 0.95,
    sample_size: 500
}]->(e2:entity)

// Medical relationships (derived from ClaimEdges)
(drug:drug)-[:TREATS {
    response_rate: 0.75,
    source_papers: ['PMC123']
}]->(disease:disease)

(virus:disease)-[:CAUSES {
    mechanism: 'infection',
    source_papers: ['PMC456']
}]->(syndrome:disease)

// Paper published claim
(p:paper)-[:PUBLISHED]->(c:claim)

// Claim involves entities
(c:claim)-[:SUBJECT]->(e1:entity)
(c:claim)-[:OBJECT]->(e2:entity)

// Evidence supports/refutes claim
(ev:evidence)-[:SUPPORTS {weight: 0.9}]->(c:claim)
(ev:evidence)-[:REFUTES {weight: 0.1}]->(c:claim)

// Paper cites other paper
(p1:paper)-[:CITES {context: '...'}]->(p2:paper)

// Claim contradicts other claim (derived)
(c1:claim)-[:CONTRADICTS]->(c2:claim)
```

### Bulk Import from JSONL

```python
from db_serialization import batch_insert_edges_to_age

# Import extraction edges from pmc_ner_pipeline.py output
with open('/app/output/extraction_edges.jsonl') as f:
    edges = [ExtractionEdge(**json.loads(line)) for line in f]
    batch_insert_edges_to_age(cursor, edges, batch_size=1000)
```

### Indexes

```sql
-- Vector similarity search on embeddings
CREATE INDEX entity_embedding_idx ON entities 
USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX paragraph_embedding_idx ON paragraphs 
USING ivfflat (embedding vector_cosine_ops);

-- Text search
CREATE INDEX paper_title_idx ON papers USING gin(to_tsvector('english', title));

-- Graph traversal
CREATE INDEX claim_paper_idx ON claims(paper_id);
CREATE INDEX evidence_claim_idx ON evidence(claim_id);
```

---

## Migration Strategy

### Phase 1: Extract to SQLite (Stages 1-5)
- Fast, local processing
- Easy to debug and inspect
- Can rebuild anytime from JSON
- **Pydantic models** stored as JSON in SQLite
- Full validation and type safety

### Phase 2: Bulk import to PostgreSQL/AGE (Stage 6)
- Disable indexes
- Use COPY or batch INSERT
- Process papers in parallel
- Rebuild indexes after import
- Use `db_serialization.py` helpers for Cypher generation

### Phase 3: Incremental updates
- New papers → extract to JSON → import to graph
- Maintain SQLite as staging area
- PostgreSQL as queryable production DB

---

## Integration Notes

### Benefits of Combined Approach

1. **Type Safety**: Pydantic validates at creation time
2. **No Data Loss**: Full models stored in SQLite JSON
3. **Database Independence**: Same models work with SQLite and AGE
4. **Provenance**: Complete audit trail for reproducibility
5. **Three Layers**: Proper separation of extraction/claims/evidence
6. **Query Flexibility**: Can query by extracted fields OR deserialize full model

### Query Examples

**SQLite: Find all diseases mentioning "diabetes"**
```python
cursor = conn.execute(
    "SELECT * FROM entities WHERE canonical_name LIKE ?",
    ("%diabetes%",)
)
for row in cursor:
    disease = deserialize_entity_from_sqlite(row, EntityType.DISEASE)
    print(disease.name, disease.umls_id, disease.synonyms)
```

**SQLite: Query JSON fields directly**
```sql
SELECT
    entity_id,
    canonical_name,
    json_extract(entity_json, '$.umls_id') as umls_id,
    json_extract(entity_json, '$.synonyms') as synonyms
FROM entities
WHERE type = 'disease'
  AND json_extract(entity_json, '$.umls_id') IS NOT NULL;
```

**AGE: Find all drugs treating diabetes**
```cypher
MATCH (d:drug)-[r:TREATS]->(di:disease {entity_id: 'DISEASE:diabetes'})
RETURN d, r, di
```

**AGE: Find extraction edges with high confidence**
```cypher
MATCH (s)-[r:EXTRACTION_EDGE]->(o)
WHERE r.confidence > 0.9
RETURN s, r, o
```

**AGE: Find contradictory claims about HIV**
```cypher
MATCH (c1:claim)-[:SUBJECT]->(hiv:disease {entity_id: 'DISEASE:hiv'}),
      (c2:claim)-[:SUBJECT]->(hiv)
WHERE c1.claim_id < c2.claim_id
  AND c1.predicate != c2.predicate
  AND (
    (c1.predicate = 'CAUSES' AND c2.predicate = 'UNRELATED_TO')
    OR
    (c1.polarity = 'supports' AND c2.polarity = 'refutes')
  )
RETURN c1, c2;
```

### Backward Compatibility

**For New Code:**
- Use Pydantic models directly
- Use `db_serialization.py` helpers for database operations
- Create ExtractionEdge/ClaimEdge/EvidenceEdge as appropriate

**For Existing Code:**
- SQLite schema is backward compatible (columns added, not removed)
- Legacy CSV files still generated
- Can gradually migrate to new format

### Common Pitfalls

**Q: Can I still use my existing SQLite queries?**
A: Yes! The schema is backward compatible. New columns added, old columns preserved.

**Q: Do I have to use Cypher?**
A: No! The serialization helpers generate Cypher, but you can use the dicts directly.

**Q: What if I need a new entity type?**
A: Add it to `entity.py` following the Disease/Gene/Drug pattern. Update `db_serialization.py` mapping.

**Q: Can I query the JSON in SQLite?**
A: Yes! SQLite has JSON functions: `SELECT json_extract(entity_json, '$.umls_id') FROM entities`

**Q: How do I bulk load into AGE?**
A: Use `batch_insert_edges_to_age()` from `db_serialization.py` for efficient batching.

### Next Steps

1. **Define Provenance class** in base.py (placeholder exists)
2. **Add more entity types** as needed (Protein, CellType, Tissue)
3. **Create ClaimEdge pipeline** (Stage 4) for semantic relationships
4. **Add embedding generation** (Stage 3) for entity resolution
5. **Build AGE import pipeline** to load extraction_edges.jsonl
