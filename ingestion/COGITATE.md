# Building a Medical Knowledge Graph: A Design Journey

**Date**: January 2, 2026
**Project**: Medical Literature Knowledge Graph
**Key Question**: How do we build a knowledge graph that tracks WHO said WHAT, WHEN, and with WHAT EVIDENCE?

---

## Table of Contents

1. [The Problem](#the-problem)
2. [The Three-Layer Architecture](#the-three-layer-architecture)
3. [The Python Schema](#the-python-schema)
4. [The PostgreSQL Mismatch](#the-postgresql-mismatch)
5. [Discovering SQLModel](#discovering-sqlmodel)
6. [The Inheritance Debate](#the-inheritance-debate)
7. [The Breakthrough](#the-breakthrough)
8. [Final Design](#final-design)
9. [Lessons Learned](#lessons-learned)

---

## The Problem

Most medical AI systems treat knowledge as static facts in a database. But medical knowledge is:

- **Contested** - Different papers disagree
- **Evolving** - Understanding changes over time
- **Uncertain** - Evidence has varying quality
- **Contextual** - Claims depend on study design, population, etc.

We needed a schema that captures **how** we know what we know, not just what we claim to know.

### Key Requirements

1. **Provenance tracking** - Every relationship must trace back to source papers
2. **Contradiction handling** - System must represent disagreement
3. **Evidence quality** - Different study types have different reliability
4. **Reproducibility** - Complete audit trail of extraction process
5. **Multi-hop reasoning** - Support complex clinical queries

---

## The Three-Layer Architecture

The breakthrough insight (from a ChatGPT conversation embedded in the code):

> **"Edges are not predicates. Predicates are *meanings*; edges are *events*."**

This led to separating edges into **three epistemic layers**:

### Layer 1: Extraction
**What models extracted from text**

- Noisy (model errors happen)
- Reproducible (same model + prompt → same output)
- Disposable (can be regenerated with better models)

```python
ExtractionEdge:
  extractor: "llama3.1:70b"
  confidence: 0.89
  paper_id: "PMC999888"
```

### Layer 2: Claim
**What papers assert as true**

- Paper-level assertions
- Can be contradictory (papers disagree)
- Versioned (claims evolve)
- Citable (traceable to papers)

```python
ClaimEdge:
  predicate: "TREATS"
  asserted_by: "PMC999888"
  polarity: "supports"
```

### Layer 3: Evidence
**Empirical evidence from studies**

- Fine-grained (specific findings)
- Multi-modal (text, stats, figures)
- Weighted (evidence strength)
- Reusable (evidence can support multiple claims)

```python
EvidenceEdge:
  evidence_type: "rct_evidence"
  strength: 0.95
  text_span: "Olaparib improved PFS (HR=0.58, p<0.001)"
  sample_size: 302
```

### Why This Separation Matters

**Without layers:**
```
Drug X → Disease Y (confidence: 0.7)
```
What does this mean? Is it noisy extraction? A claim? Strong evidence?

**With layers:**
```
Extraction: LLM thinks Drug X treats Disease Y (conf: 0.89)
Claim: Paper PMC123 asserts Drug X treats Disease Y (polarity: supports)
Evidence: RCT with n=302 found HR=0.58, p<0.001 (strength: 0.95)
```

Now we can:
- Track extraction quality separately from evidence quality
- Handle contradictions (different papers, different claims)
- Query by evidence level ("show me only RCT evidence")
- Reproduce extractions (regenerate with better models)

---

## The Python Schema

The initial Python schema was sophisticated:

### Entity Types

```python
class BaseMedicalEntity(BaseModel):
    entity_id: str
    name: str
    synonyms: list[str]
    abbreviations: list[str]
    embedding: list[float]  # For semantic search
    created_at: datetime
    source: Literal["umls", "mesh", "rxnorm", ...]

class Disease(BaseMedicalEntity):
    umls_id: str
    mesh_id: str
    icd10_codes: list[str]

class Drug(BaseMedicalEntity):
    rxnorm_id: str
    drug_class: str
    mechanism: str
```

### Edge Hierarchy

```python
class Edge(BaseModel):
    id: EdgeId
    subject: EntityReference
    object: EntityReference
    provenance: Provenance

class ExtractionEdge(Edge):
    extractor: ModelInfo
    confidence: float

class ClaimEdge(Edge):
    predicate: ClaimPredicate
    asserted_by: PaperId
    polarity: Polarity

class EvidenceEdge(Edge):
    evidence_type: EvidenceType
    strength: float
```

### Complete Provenance

```python
class ExtractionProvenance(BaseModel):
    extraction_pipeline: ExtractionPipelineInfo
    models: Dict[str, ModelInfo]  # LLM, embeddings, etc.
    prompt: PromptInfo
    execution: ExecutionInfo
    entity_resolution: EntityResolutionInfo
```

This captures:
- Git commit hash (exact code version)
- Model versions and parameters
- Prompt version with checksum
- Execution metadata (hostname, timestamp, duration)
- Entity resolution details

### Paper Model

```python
class Paper(BaseModel):
    paper_id: str
    title: str
    abstract: str
    authors: list[str]

    # Study metadata
    study_type: Literal["rct", "observational", ...]
    sample_size: int
    clinical_phase: str
    mesh_terms: list[str]

    # Provenance
    extraction_provenance: ExtractionProvenance
```

---

## The PostgreSQL Mismatch

When we looked at the SQL schema, there were **critical gaps**:

### Missing: Three-Layer Architecture

**SQL had:**
```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY,
    subject_id TEXT,
    predicate TEXT,
    object_id TEXT,
    confidence FLOAT,
    UNIQUE(subject_id, object_id, predicate)  -- ⚠️ Problem!
);
```

**Issues:**
1. No distinction between extraction/claim/evidence layers
2. UNIQUE constraint prevents multiple papers from same relationship
3. Can't represent "5 papers say Drug X treats Disease Y"

### Missing: Entity Fields

**Python had:**
```python
synonyms: list[str]
abbreviations: list[str]
source: Literal["umls", "mesh", ...]
```

**SQL had:**
```sql
properties JSONB  -- Everything goes here ❌
```

### Missing: Extraction Provenance

Python tracked git commit, model versions, prompt checksums.
SQL had nothing.

### Missing: Paper Metadata

Python tracked study_type, sample_size, clinical_phase, MeSH terms.
SQL had just title and abstract.

---

## Discovering SQLModel

SQLModel combines **Pydantic + SQLAlchemy**. Your models are both:
- Pydantic models (validation, serialization)
- SQLAlchemy ORM models (database, queries)

### Key Benefits

#### 1. Single Source of Truth

**Before:**
- Maintain Python models AND SQL schema
- They drift (as we saw)
- Manual sync required

**With SQLModel:**
```python
class Disease(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    synonyms: List[str] = Field(sa_column=Column(ARRAY(String)))
```
Database schema **generated from this**. Can't drift.

#### 2. Type-Safe Queries

**Before:**
```python
cursor.execute("SELECT * FROM entities WHERE entity_type = ?", ("drug",))
```

**With SQLModel:**
```python
drugs = session.exec(
    select(Entity)
    .where(Entity.entity_type == EntityType.DRUG)
    .where(Entity.synonyms.contains(["aspirin"]))
).all()
```
Full autocomplete. Type checking. IDE support.

#### 3. Relationships Work Naturally

```python
class Paper(SQLModel, table=True):
    paper_id: str = Field(primary_key=True)
    evidence_items: List["Evidence"] = Relationship(back_populates="paper")

class Evidence(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    paper_id: str = Field(foreign_key="papers.paper_id")
    paper: Paper = Relationship(back_populates="evidence_items")

# Navigate the graph
evidence = session.get(Evidence, some_id)
print(f"From paper: {evidence.paper.title}")
```

#### 4. Automatic Migrations

```bash
# 1. Change Python model
class Entity(SQLModel, table=True):
    ncbi_gene_id: Optional[str] = None  # Add field

# 2. Generate migration
alembic revision --autogenerate -m "add ncbi_gene_id"

# 3. Apply
alembic upgrade head
```

Alembic detects the diff and generates SQL.

---

## The Inheritance Debate

The first SQLModel attempt failed with inheritance errors. This led to a GitHub Copilot code review that suggested: **"Drop inheritance entirely. Make each edge type independent."**

### The "Drop Inheritance" Argument

**Reasoning:**
- SQLModel inheritance is complex
- Your queries are layer-specific anyway
- Each layer is philosophically distinct

**Proposed:**
```python
# Three independent tables, no base class
class ExtractionEdge(SQLModel, table=True):
    id: UUID
    subject_id: str
    extractor_name: str
    # ...

class ClaimEdge(SQLModel, table=True):
    id: UUID
    subject_id: str
    predicate: str
    # ...

class EvidenceEdge(SQLModel, table=True):
    id: UUID
    subject_id: str
    evidence_type: str
    # ...
```

**What you gain:**
- ✅ SQLModel works perfectly
- ✅ No inheritance complexity
- ✅ Each layer evolves independently

**What you lose:**
- ❌ Duplicate common fields (id, subject_id, object_id, created_at)
- ❌ Can't query across layers easily
- ❌ No polymorphic queries

### The Pushback

I argued that you **DO need cross-layer queries**:

#### Use Case 1: "Show me everything we know about Drug X → Disease Y"

This requires querying all three layers:
```python
# Without inheritance
all_edges = (
    session.exec(select(ExtractionEdge).where(...)).all() +
    session.exec(select(ClaimEdge).where(...)).all() +
    session.exec(select(EvidenceEdge).where(...)).all()
)

# With inheritance
all_edges = session.exec(
    select(Edge)
    .where(Edge.subject_id == drug_id)
    .where(Edge.object_id == disease_id)
).all()
```

#### Use Case 2: Debugging & Provenance

"Why does the system think X relates to Y?"

Need to trace: Extraction → Claim → Evidence

#### Use Case 3: Contradiction Detection

"Do different papers agree?"

Need to compare claims across papers.

#### Use Case 4: Audit Trails

"Show me every assertion about this relationship"

Need all layers for complete picture.

### The Critical Test

> **"Will I ever need to ask 'show me all relationships between entity A and entity B, regardless of layer'?"**

Looking at project goals:
- ✅ Contradiction detection
- ✅ Evidence aggregation
- ✅ Provenance tracking
- ✅ Debugging

**Answer: YES** - Cross-layer queries are essential.

---

## The Breakthrough

The reviewer's response:

> "You're absolutely right. I was too hasty. Cross-layer queries ARE important."

But there was still the problem: **SQLModel inheritance wasn't working**.

### Why SQLModel Inheritance Failed Initially

The original attempt used **joined-table inheritance**, which creates separate tables:

```python
class Edge(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    subject_id: str

class ClaimEdge(Edge, table=True):
    # This creates a SECOND table with foreign key to Edge
    id: UUID = Field(foreign_key="edge.id", primary_key=True)
    predicate: str
```

This is complex to set up correctly in SQLModel.

### The Solution: Single-Table Inheritance

Instead of multiple tables, use **ONE table** with a discriminator:

```python
class Edge(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    layer: str = Field(index=True)  # 'extraction', 'claim', 'evidence'

    # Common fields
    subject_id: str
    object_id: str
    created_at: datetime

    # ALL layer-specific fields (nullable)
    extractor_name: Optional[str] = None      # extraction
    predicate: Optional[str] = None           # claim
    evidence_strength: Optional[float] = None # evidence
```

**Key insight:** This is actually MORE aligned with the conceptual model!

The three layers aren't really subtypes in the OOP sense - they're different **roles** that share a common structure.

---

## Final Design

The proof-of-concept implements single-table design with helper functions:

### Database Schema

```sql
CREATE TABLE edges (
    id UUID PRIMARY KEY,
    layer TEXT NOT NULL,  -- 'extraction', 'claim', 'evidence'

    -- Common fields (all edges)
    subject_id TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    object_name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,

    -- Extraction fields (nullable)
    extractor_name TEXT,
    extractor_provider TEXT,
    extraction_confidence FLOAT,
    extraction_paper_id TEXT,

    -- Claim fields (nullable)
    predicate TEXT,
    asserted_by TEXT,
    polarity TEXT,
    claim_confidence FLOAT,

    -- Evidence fields (nullable)
    evidence_type TEXT,
    evidence_strength FLOAT,
    evidence_paper_id TEXT,
    evidence_section TEXT,
    evidence_text_span TEXT,
    study_type TEXT,
    sample_size INTEGER,

    -- Constraints enforce layer requirements
    CHECK ((layer != 'extraction') OR
           (extractor_name IS NOT NULL AND extraction_confidence IS NOT NULL)),
    CHECK ((layer != 'claim') OR
           (predicate IS NOT NULL AND asserted_by IS NOT NULL)),
    CHECK ((layer != 'evidence') OR
           (evidence_type IS NOT NULL AND evidence_strength IS NOT NULL))
);

CREATE INDEX idx_edges_layer ON edges(layer);
CREATE INDEX idx_edges_subject ON edges(subject_id);
CREATE INDEX idx_edges_object ON edges(object_id);
```

### Python Implementation

```python
class Edge(SQLModel, table=True):
    """All edge types in one table"""
    __tablename__ = "edges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    layer: str = Field(index=True)

    # Common fields
    subject_id: str = Field(index=True)
    object_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Layer-specific fields (all optional)
    extractor_name: Optional[str] = None
    predicate: Optional[str] = None
    evidence_strength: Optional[float] = None
    # ... etc

# Helper functions for type-safe creation
def create_extraction_edge(**kwargs) -> Edge:
    return Edge(layer="extraction", **kwargs)

def create_claim_edge(**kwargs) -> Edge:
    return Edge(layer="claim", **kwargs)

def create_evidence_edge(**kwargs) -> Edge:
    return Edge(layer="evidence", **kwargs)
```

### Query Examples

#### Layer-Specific Query

```python
# "What do papers CLAIM about Olaparib?"
claims = session.exec(
    select(Edge)
    .where(Edge.layer == "claim")
    .where(Edge.subject_id == "RxNorm:1187832")
).all()
```

#### Cross-Layer Query

```python
# "Show me EVERYTHING about Olaparib → Breast Cancer"
all_edges = session.exec(
    select(Edge)
    .where(Edge.subject_id == "RxNorm:1187832")
    .where(Edge.object_id == "UMLS:C0006142")
).all()

for edge in all_edges:
    if edge.layer == "extraction":
        print(f"Extracted by {edge.extractor_name}")
    elif edge.layer == "claim":
        print(f"Paper asserts: {edge.predicate}")
    elif edge.layer == "evidence":
        print(f"Evidence: {edge.evidence_text_span}")
```

#### Evidence Quality Filter

```python
# "Show me RCT evidence with strength > 0.9"
strong_evidence = session.exec(
    select(Edge, Paper)
    .join(Paper, Edge.evidence_paper_id == Paper.paper_id)
    .where(Edge.layer == "evidence")
    .where(Edge.study_type == "rct")
    .where(Edge.evidence_strength > 0.9)
).all()
```

#### Contradiction Detection

```python
# "Which papers disagree?"
all_claims = session.exec(
    select(Edge).where(Edge.layer == "claim")
).all()

# Group by relationship
by_relationship = {}
for claim in all_claims:
    key = (claim.subject_id, claim.predicate, claim.object_id)
    by_relationship.setdefault(key, []).append(claim)

# Find contradictions
for key, claims_list in by_relationship.items():
    polarities = {c.polarity for c in claims_list}
    if len(polarities) > 1:
        print(f"CONTRADICTION: {claims_list[0].subject_name} → {claims_list[0].object_name}")
        for claim in claims_list:
            print(f"  {claim.asserted_by}: {claim.polarity}")
```

### Advantages of This Design

#### ✅ Conceptually Sound

The three layers ARE different roles, not true subtypes. Single table reflects this.

#### ✅ SQLModel Compatible

No complex inheritance, no joined tables. Just works.

#### ✅ All Queries Work

Layer-specific AND cross-layer queries are natural.

#### ✅ Database Enforces Rules

CHECK constraints ensure extraction edges have extractors, claims have predicates, etc.

#### ✅ Room to Grow

Easy to add new layers (add fields + constraint). Easy to add new fields to existing layers.

#### ✅ Performance

One table = one query for cross-layer. No joins between edge types needed.

### Trade-offs

#### ⚠️ Sparse Columns

Each row has NULLs for other layers' fields.

**Why this is OK:**
- Storage is cheap
- Modern databases handle NULLs efficiently
- You're doing graph queries, not table scans
- Typical row has ~15 NULL columns out of ~30 total

#### ⚠️ No Python Type Enforcement

All edges are `Edge` class, not `ExtractionEdge` / `ClaimEdge` / `EvidenceEdge`.

**Mitigations:**
- Database constraints enforce required fields
- Helper functions provide type-safe creation API
- Could add Pydantic validators for additional safety

---

## Lessons Learned

### 1. Cross-Layer Queries ARE Essential

Initial assumption: "Queries are always layer-specific"

Reality: Debugging, provenance, contradiction detection, and "show me everything" queries require cross-layer access.

### 2. Single-Table Inheritance is Underrated

It's often dismissed as "not normalized" or "wasteful". But for your use case:
- Sparse columns aren't a problem
- Queries are simpler
- Schema evolution is easier
- Performance is better (fewer joins)

### 3. Database Constraints > Python Type Checking

For data integrity, database constraints are more reliable than Python class hierarchies.

```python
# Python can't prevent this at DB level
edge = Edge(layer="claim")  # Missing required predicate!

# But database constraint will reject it
CHECK ((layer != 'claim') OR (predicate IS NOT NULL))
```

### 4. Pragmatism Over Purity

The "correct" OOP design (separate classes with inheritance) is harder to implement and maintain than the pragmatic design (single table with discriminator).

### 5. Test Your Assumptions With Queries

The breakthrough came from asking:

> "Will I ever need to query across layers?"

And then writing actual query examples. Theory is one thing; concrete use cases reveal the truth.

### 6. Inheritance Serves Different Purposes

In OOP, inheritance is for **code reuse** and **polymorphism**.

In databases, table inheritance is about:
- **Schema organization** (single-table vs joined-table)
- **Query patterns** (do you need polymorphic queries?)
- **Performance** (joins vs single-table scans)

These aren't the same concerns. Don't assume OOP patterns translate directly to databases.

### 7. The Value of Iteration

The design evolved through:
1. Initial Python schema (inheritance hierarchy)
2. SQL schema (gaps identified)
3. SQLModel attempt (inheritance failed)
4. "Drop inheritance" recommendation
5. Pushback with use cases
6. Single-table solution

Each step refined understanding. The final design is better than any single perspective.

---

## The Big Picture

This project isn't just about databases and schemas. It's about **how we represent knowledge**.

The three-layer architecture recognizes that scientific knowledge has **epistemic depth**:

- **Extraction**: What we *detected*
- **Claim**: What we *assert*
- **Evidence**: What we *observed*

These aren't just implementation details. They're fundamental to how science works.

By making these layers explicit in the schema, we can:

1. **Handle uncertainty properly** - Not all knowledge is equally certain
2. **Track evolution** - Understanding changes as new evidence arrives
3. **Detect contradictions** - Science advances through disagreement
4. **Enable reasoning** - "Show me RCT evidence" vs "Show me all claims"
5. **Maintain provenance** - Complete audit trail from extraction to conclusion

This is the kind of system that can support real clinical decision-making, because it doesn't hide the complexity - it makes the complexity navigable.

---

## What's Next

For production deployment, you'd want to:

1. **Switch to PostgreSQL** - Better for production than SQLite
2. **Add vector embeddings** - For semantic search across entities
3. **Implement entity resolution** - Match mentions to canonical entities
4. **Build the extraction pipeline** - LLMs + NER + validation
5. **Add more entity types** - Genes, proteins, pathways, etc.
6. **Implement aggregation** - Combine evidence across multiple papers
7. **Add citation graph** - Papers citing each other
8. **Build query API** - FastAPI endpoints for clinical queries
9. **Add visualization** - Graph visualization of relationships
10. **Scale testing** - Test with thousands of papers

But the foundational architecture is solid. The three-layer edge design, provenance tracking, and SQLModel implementation give you a strong base to build on.

---

## Code Artifacts

This discussion produced two key artifacts:

1. **sqlmodel_inheritance_poc.py** - Working proof-of-concept demonstrating:
   - Single-table edge design
   - Layer-based querying
   - Cross-layer queries
   - Contradiction detection
   - Complete provenance chain

2. **README_POC.md** - Documentation explaining:
   - Design rationale
   - Query patterns
   - Schema details
   - Trade-offs and next steps

Both are ready to run and serve as templates for your production schema.

---

## Conclusion

Building a medical knowledge graph is hard because medical knowledge itself is complex. It's contested, uncertain, and evolving.

The key insight was recognizing that different kinds of edges (extraction vs claim vs evidence) aren't just "types" - they represent different **epistemic roles** in the scientific process.

By making these roles explicit in the schema, we created a system that can:
- Track where knowledge comes from
- Handle contradictions gracefully
- Query by evidence quality
- Maintain complete provenance
- Support complex reasoning

And by using SQLModel with single-table inheritance, we got:
- Simple schema (one edges table)
- Type-safe queries
- Database-enforced constraints
- Room to grow

This is a foundation worth building on.

---

**Project**: wware/med-lit-graph
**Contributors**: Will Ware, Claude (Anthropic), ChatGPT (OpenAI), GitHub Copilot
**Date**: January 2, 2026
