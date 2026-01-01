# SQLModel Three-Layer Edge Architecture - Proof of Concept

## What This Demonstrates

This proof-of-concept shows how to implement the **three-layer edge architecture** (Extraction → Claim → Evidence) using SQLModel with a **single-table design**.

### Key Features

1. **Single Table, Multiple Layers**
   - All edge types stored in one `edges` table
   - `layer` field acts as discriminator: `'extraction'`, `'claim'`, `'evidence'`
   - Sparse columns: each row only uses fields relevant to its layer

2. **Database-Level Constraints**
   - `CHECK` constraints ensure layer-specific required fields
   - Example: extraction edges MUST have `extractor_name` and `extraction_confidence`

3. **Type-Safe Edge Creation**
   - Helper functions: `create_extraction_edge()`, `create_claim_edge()`, `create_evidence_edge()`
   - Encapsulate layer assignment and provide clear API

4. **Powerful Queries**
   - **Layer-specific**: `WHERE layer = 'claim'` to query just claims
   - **Cross-layer**: `WHERE subject_id = X AND object_id = Y` to see all relationships
   - **Quality filtering**: `WHERE layer = 'evidence' AND evidence_strength > 0.9`

5. **Contradiction Detection**
   - Group claims by relationship, check for different polarities
   - Shows how the system handles disagreement between papers

## Running the Demo

```bash
pip install sqlmodel
python sqlmodel_inheritance_poc.py
```

### What You'll See

The demo:
1. Creates a SQLite database `medical_kg_inheritance.db`
2. Adds sample medical data (Olaparib treating Breast Cancer)
3. Creates edges at all three layers
4. Runs 6 different query patterns
5. Shows contradiction detection

### Sample Output

```
1. LAYER-SPECIFIC: What do papers CLAIM about Olaparib?
----------------------------------------------------------------------

   Paper: Efficacy of Olaparib in BRCA-Mutated Breast Cancer: Phase III Trial
   Claim: Olaparib treats Breast Cancer
   Polarity: supports
   Confidence: 0.92
   Study type: rct (n=302)

   Paper: Limited Benefit of Olaparib in Unselected Breast Cancer
   Claim: Olaparib treats Breast Cancer
   Polarity: neutral
   Confidence: 0.65
   Study type: observational (n=150)
```

## Why Single-Table Design?

### Advantages

✅ **Simple schema** - One table, no joins between edge types
✅ **Fast cross-layer queries** - All data in one place
✅ **Easy to extend** - Add new layers without schema migrations
✅ **SQLModel compatibility** - No complex inheritance setup needed

### Trade-offs

⚠️ **Sparse columns** - Each row has NULLs for other layers' fields
   - Not a problem: Storage is cheap, modern DBs handle NULLs efficiently

⚠️ **No Python type enforcement** - All edges are `Edge` class at runtime
   - Mitigated by: Database constraints + helper functions

## Database Schema

```sql
CREATE TABLE edges (
    id BLOB PRIMARY KEY,
    layer VARCHAR NOT NULL,

    -- Common fields
    subject_id VARCHAR NOT NULL,
    subject_name VARCHAR NOT NULL,
    subject_type VARCHAR NOT NULL,
    object_id VARCHAR NOT NULL,
    object_name VARCHAR NOT NULL,
    object_type VARCHAR NOT NULL,
    created_at DATETIME NOT NULL,

    -- Extraction layer fields (nullable)
    extractor_name VARCHAR,
    extractor_provider VARCHAR,
    extraction_confidence FLOAT,
    extraction_paper_id VARCHAR,

    -- Claim layer fields (nullable)
    predicate VARCHAR,
    asserted_by VARCHAR,
    polarity VARCHAR,
    claim_confidence FLOAT,

    -- Evidence layer fields (nullable)
    evidence_type VARCHAR,
    evidence_strength FLOAT,
    evidence_paper_id VARCHAR,
    evidence_section VARCHAR,
    evidence_text_span VARCHAR,
    study_type VARCHAR,
    sample_size INTEGER,

    -- Constraints ensure layer-specific requirements
    CHECK ((layer != 'extraction') OR (extractor_name IS NOT NULL)),
    CHECK ((layer != 'claim') OR (predicate IS NOT NULL)),
    CHECK ((layer != 'evidence') OR (evidence_type IS NOT NULL))
);

CREATE INDEX idx_edges_layer ON edges(layer);
CREATE INDEX idx_edges_subject ON edges(subject_id);
CREATE INDEX idx_edges_object ON edges(object_id);
```

## Next Steps

For production use, you could:

1. **Add Pydantic validation classes** for each layer type
2. **Use PostgreSQL** instead of SQLite for better performance
3. **Add vector embeddings** column for semantic search
4. **Create views** for each layer type if you want SQL-level type safety
5. **Add proper ORM relationships** between edges and papers

## Lessons Learned

From the gist conversation and this implementation:

1. **Cross-layer queries ARE important** - Debugging, provenance tracking, and "show me everything" queries require them
2. **Single-table is pragmatic** - Simpler than joined-table inheritance, works great with SQLModel
3. **Database constraints matter** - They enforce invariants that Python can't
4. **The three layers are conceptually distinct** - Not just "different types", but different epistemic roles

## Credits

This design emerged from:
- ChatGPT's insights on epistemic layers
- GitHub Copilot's code review
- Iterative refinement based on actual SQLModel capabilities
