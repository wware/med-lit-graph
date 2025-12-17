# Database Schema Design

## Overview

This document describes the database schemas for all pipeline stages.

Current implementation: **Stage 1 only (entities.db)**
Planned: Stages 2-6

---

## Stage 1: Entity Extraction

**Database**: `entities.db` (SQLite)
**Purpose**: Canonical entity storage with alias mappings

### Tables

```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE,
    type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    name TEXT UNIQUE,
    source TEXT,  -- PMC ID where this alias was found
    confidence REAL,  -- NER confidence score
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Example Data

```sql
-- Canonical entity
INSERT INTO entities (id, canonical_name, type) VALUES (15, 'HIV', 'Disease');

-- Multiple aliases map to same canonical entity
INSERT INTO aliases (entity_id, name, source, confidence) 
VALUES 
    (15, 'HIV', 'PMC2545367', 0.98),
    (15, 'HTLV-III', 'PMC322947', 0.95),
    (15, 'LAV', 'PMC268988', 0.92);
```

### Indexes

```sql
CREATE INDEX idx_aliases_entity_id ON aliases(entity_id);
CREATE INDEX idx_aliases_name ON aliases(name);
```

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

### Node Types

```cypher
// Paper nodes
CREATE (:Paper {
    pmc_id: 'PMC322947',
    title: '...',
    pub_date: date('1986-02-01'),
    authors: ['Gallo RC', 'Harper ME'],
    journal: 'Proc Natl Acad Sci U S A'
})

// Entity nodes (from entities.db)
CREATE (:Entity {
    id: 15,
    canonical_name: 'HIV',
    type: 'Disease',
    aliases: ['HIV', 'HTLV-III', 'LAV']
})

// Claim nodes
CREATE (:Claim {
    claim_id: 'PMC322947_claim_1',
    predicate: 'INFECTS',
    extracted_text: '...',
    confidence: 0.92
})

// Evidence nodes
CREATE (:Evidence {
    evidence_id: 'PMC322947_ev_1',
    type: 'in_situ_hybridization',
    strength: 'high'
})
```

### Edge Types

```cypher
// Paper published claim
(p:Paper)-[:PUBLISHED]->(c:Claim)

// Claim involves entities
(c:Claim)-[:SUBJECT]->(e1:Entity)
(c:Claim)-[:OBJECT]->(e2:Entity)

// Evidence supports/refutes claim
(ev:Evidence)-[:SUPPORTS {weight: 0.9}]->(c:Claim)
(ev:Evidence)-[:REFUTES {weight: 0.1}]->(c:Claim)

// Paper cites other paper
(p1:Paper)-[:CITES {context: '...'}]->(p2:Paper)

// Claim contradicts other claim (derived)
(c1:Claim)-[:CONTRADICTS]->(c2:Claim)
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

## Query Examples

### Find all claims about HIV causing AIDS

```sql
-- SQLite (Stage 4)
SELECT 
    c.claim_id,
    c.extracted_text,
    p.title,
    p.pub_date,
    e1.canonical_name as subject,
    e2.canonical_name as object
FROM claims c
JOIN papers p ON c.paper_id = p.pmc_id
JOIN entities e1 ON c.subject_entity_id = e1.id
JOIN entities e2 ON c.object_entity_id = e2.id
WHERE c.predicate = 'CAUSES'
  AND e1.canonical_name = 'HIV'
  AND e2.canonical_name = 'AIDS'
ORDER BY p.pub_date;
```

```cypher
-- Cypher (Stage 6 - Apache AGE)
MATCH (p:Paper)-[:PUBLISHED]->(c:Claim)-[:SUBJECT]->(hiv:Entity {canonical_name: 'HIV'})
MATCH (c)-[:OBJECT]->(aids:Entity {canonical_name: 'AIDS'})
WHERE c.predicate = 'CAUSES'
RETURN p.title, p.pub_date, c.extracted_text, c.confidence
ORDER BY p.pub_date;
```

### Find contradictory claims

```cypher
MATCH (c1:Claim)-[:SUBJECT]->(e1:Entity),
      (c2:Claim)-[:SUBJECT]->(e1),
      (c1)-[:OBJECT]->(e2:Entity),
      (c2)-[:OBJECT]->(e2)
WHERE c1.claim_id < c2.claim_id  -- Avoid duplicates
  AND c1.predicate != c2.predicate
  AND (
    (c1.predicate = 'CAUSES' AND c2.predicate = 'UNRELATED_TO')
    OR
    (c1.predicate = 'TREATS' AND c2.predicate = 'INEFFECTIVE')
  )
RETURN c1, c2;
```

### Find evidence supporting a claim

```sql
-- SQLite
SELECT 
    e.evidence_id,
    e.type,
    e.strength,
    em.sample_size,
    em.detection_rate,
    p.text as evidence_text
FROM evidence e
JOIN evidence_metrics em ON e.evidence_id = em.evidence_id
JOIN paragraphs p ON e.paragraph_id = p.paragraph_id
WHERE e.claim_id = 'PMC322947_claim_1'
  AND e.supports = TRUE;
```

---

## Migration Strategy

### Phase 1: Extract to SQLite (Stages 1-5)
- Fast, local processing
- Easy to debug and inspect
- Can rebuild anytime from JSON

### Phase 2: Bulk import to PostgreSQL/AGE (Stage 6)
- Disable indexes
- Use COPY instead of INSERT
- Process papers in parallel
- Rebuild indexes after import

### Phase 3: Incremental updates
- New papers → extract to JSON → import to graph
- Maintain SQLite as staging area
- PostgreSQL as queryable production DB
