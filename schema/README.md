# Medical Knowledge Graph Schema

This directory defines the complete data schema for the medical literature knowledge graph, including entity types, relationship types, and supporting classes for evidence tracking.

## Overview

The schema supports clinical decision-making by representing medical knowledge extracted from research papers. It enables multi-hop reasoning, contradiction detection, and evidence-based inference using strongly-typed entity and relationship classes.

## Design Philosophy

### 1. **Provenance as a First-Class Citizen**

**ALL medical relationships MUST include evidence.  Evidence is not optional.**

Every piece of evidence specifies:
- `paper_id`: Which PMC paper
- `section_type`: Where in the paper (results, methods, discussion)
- `paragraph_idx`: Exact paragraph number
- `extraction_method`: How it was extracted (for reproducibility)
- `confidence`: Confidence in this specific piece of evidence
- `study_type`: RCT, meta-analysis, observational, etc.

**Why this matters:**
- Doctors don't trust AI/ML systems that can't explain their sources
- Researchers can verify and audit data quality
- Users can distinguish high-quality evidence (RCTs) from low-quality (case reports)
- Full traceability means every claim can be verified

**Trade-off accepted:** ~20-30% storage overhead, but trustworthiness >> storage costs for medical applications.

### 2. **Evidence Quality Weighting**

Confidence scores are **automatically calculated** from evidence quality, not manually assigned.

```python
study_weights = {
    'rct': 1.0,              # Randomized controlled trial (gold standard)
    'meta_analysis': 0.95,   # Systematic review
    'cohort': 0.8,           # Longitudinal observational
    'case_control':  0.7,     # Retrospective
    'observational': 0.6,    # General observation
    'case_report': 0.4,      # Single patient
    'review': 0.5            # Literature review (not systematic)
}
```

This approach is:
- ✅ Objective and consistent
- ✅ Transparent (users see evidence breakdown)
- ✅ Filterable (show only RCT-supported claims)
- ✅ Aligned with evidence-based medicine principles

### 3. **Pydantic for Schema Validation**

All data models use **Pydantic v2** for runtime validation, ensuring it's impossible to create invalid data.

**Why Pydantic:**
- Runtime validation catches errors before they propagate
- JSON serialization built-in
- Type hints for IDE support
- Medical data **must** be validated—errors could be dangerous

## Module Structure

### `entity.py`
Defines all entity types in the knowledge graph:

**Core Medical Entities:**
- `Disease` - Diseases and conditions (UMLS IDs)
- `Gene` - Genes (HGNC IDs)
- `Drug` - Medications and compounds (RxNorm IDs)
- `Protein` - Proteins (UniProt IDs)
- `Mutation` - Genetic variants
- `Symptom` - Clinical presentations
- `Biomarker` - Diagnostic/prognostic markers
- `Pathway` - Biological pathways
- `Procedure` - Medical procedures

**Research Metadata:**
- `Paper` - Research publications (PMC IDs)
- `Author` - Paper authors
- `ClinicalTrial` - Clinical trials

**Key Features:**
- All entities share base properties:  `entity_id`, `name`, `synonyms`, `embedding`
- Standards-based IDs (UMLS, MeSH, RxNorm, HGNC, UniProt)
- Pre-computed embeddings for semantic search
- `EntityCollection` for efficient storage and retrieval

### `relationship.py`
Defines all relationship types between entities:

**Categories:**
- **Causal:** `CAUSES`, `INCREASES_RISK`, `PREVENTS`
- **Treatment:** `TREATS`, `MANAGES`, `CONTRAINDICATED_FOR`, `SIDE_EFFECT`
- **Molecular:** `BINDS_TO`, `INHIBITS`, `ACTIVATES`, `ENCODES`
- **Clinical:** `DIAGNOSED_BY`, `INDICATES`, `CO_OCCURS_WITH`, `ASSOCIATED_WITH`
- **Drug Interactions:** `INTERACTS_WITH`
- **Provenance:** `AUTHORED_BY`, `CITES`, `CONTRADICTS`, `SUPPORTS`

**Key Classes:**
- `BaseRelationship` - Minimal triple (subject, predicate, object)
- `BaseMedicalRelationship` - Adds evidence tracking and confidence scoring
- Specialized classes (e.g., `Treats`, `Causes`) with domain-specific fields

### `__init__.py`
Provides a clean public API with all entity and relationship classes exported.

## Quick Start

```python
from schema import Disease, Drug, Treats, RelationType, create_relationship

# Create entities
disease = Disease(
    entity_id="C0006142",
    name="Breast Cancer",
    synonyms=["Breast Carcinoma"],
    source="umls"
)

drug = Drug(
    entity_id="RxNorm:1187832",
    name="Olaparib",
    drug_class="PARP inhibitor"
)

# Create relationship with evidence
treats = create_relationship(
    RelationType.TREATS,
    subject_id=drug.entity_id,
    object_id=disease.entity_id,
    response_rate=0.59,
    source_papers=["PMC999"],
    confidence=0.85
)
```

## Design Principles (from DESIGN_DECISIONS.md)

1. **Clinical utility first** - Schema supports queries doctors actually ask
2. **Provenance always** - Every relationship traces back to source papers
3. **Handle uncertainty** - Represent confidence, contradictions, and evolution over time
4. **Standards-based** - Use UMLS, MeSH, and other medical ontologies for entity IDs
5. **Scalable** - Can grow from thousands to millions of papers

## Standards and Ontologies

The schema integrates with established medical ontologies:

- **UMLS** (Unified Medical Language System) - Diseases, symptoms, concepts
- **RxNorm** - Drugs and medications
- **HGNC** - Human genes
- **UniProt** - Proteins
- **MeSH** - Medical subject headings
- **ClinicalTrials.gov** - Clinical trial identifiers

## Evidence Tracking

Two levels of provenance are supported:

### Lightweight (minimum required)
```python
source_papers=["PMC123", "PMC456"]
confidence=0.85
```

### Rich (recommended)
```python
evidence=[
    Evidence(
        paper_id="PMC123",
        section_type="results",
        paragraph_idx=5,
        sentence_idx=2,
        text_span="Exact quote from paper",
        extraction_method="llm",
        confidence=0.90,
        study_type="rct",
        sample_size=302
    )
]
```

## Related Documentation

- **[DESIGN_DECISIONS.md](../DESIGN_DECISIONS.md)** - Full rationale for architectural choices
- **[tests/README.md](../tests/README.md)** - Test coverage and validation

## Validation Philosophy

> "Choose simplicity and correctness over performance. Medical applications require trustworthiness above all else."

The schema enforces strict validation to prevent invalid data from entering the system. This is a deliberate trade-off:  slightly higher runtime cost in exchange for data integrity that could impact patient care.

## Canonical Entity IDs: The Glue of the Knowledge Graph

### The Problem: Entity Resolution Across Papers

When processing millions of medical papers, the same entity appears in many forms:
- **"Type 2 Diabetes"** vs **"T2DM"** vs **"Type II Diabetes"** vs **"NIDDM"**
- **"Breast Cancer"** vs **"Breast Carcinoma"** vs **"Mammary Neoplasm"**
- **"BRCA1"** vs **"breast cancer 1"** vs **"BRCA1 gene"**

Without canonical IDs, these would be treated as separate entities, fragmenting the knowledge graph. Relationships from different papers wouldn't connect.

### The Solution: Standards-Based Canonical IDs

Every entity has a **canonical ID** from an established medical ontology:

| Entity Type | ID System | Example |
|------------|-----------|---------|
| Disease | UMLS Concept ID | `C0011860` (Type 2 Diabetes) |
| Gene | HGNC ID | `HGNC:1100` (BRCA1) |
| Drug | RxNorm ID | `RxNorm:1187832` (Olaparib) |
| Protein | UniProt ID | `P38398` (BRCA1 protein) |
| Clinical Trial | NCT ID | `NCT01234567` |

**All mentions of the same entity across ALL papers map to the same canonical ID.**

### EntityCollection: The Master Entity Registry

The `EntityCollection` class maintains the **authoritative set** of canonical entities that paper extractions link to.

```python
from schema import EntityCollection, Disease, Gene, Drug

# Create master entity collection
collection = EntityCollection()

# Add canonical entities
collection.add_disease(Disease(
    entity_id="C0006142",
    name="Breast Cancer",
    synonyms=["Breast Carcinoma", "Mammary Cancer"],
    abbreviations=["BC"],
    umls_id="C0006142",
    mesh_id="D001943"
))

collection.add_gene(Gene(
    entity_id="HGNC:1100",
    name="BRCA1",
    synonyms=["breast cancer 1"],
    symbol="BRCA1",
    hgnc_id="HGNC:1100"
))

# Look up entities during paper processing
entity = collection.get_by_id("C0006142")
# or by ontology-specific ID
entity = collection.get_by_umls("C0006142")
```

### How Entity Resolution Works

**During paper processing:**

1. **Extract mentions** - NER finds "T2DM" in a paper
2. **Entity linking** - Map "T2DM" → canonical ID `C0011860`
3. **Store relationship** - Use canonical ID in relationships:
   ```python
   Treats(
       subject_id="RxNorm:1187832",  # Olaparib (canonical drug ID)
       object_id="C0006142",          # Breast Cancer (canonical disease ID)
       source_papers=["PMC999"]
   )
   ```
4. **Graph integration** - All papers referencing "Breast Cancer" (regardless of exact wording) connect to the same node

**Without canonical IDs:** 1000 papers might create 50 different "diabetes" nodes

**With canonical IDs:** 1000 papers all reference `C0011860`, creating a single unified knowledge base

### Implementation in AWS

For a production deployment, `EntityCollection` would be implemented as:

#### Development/Small Scale
```python
# Load from local JSONL file
collection = EntityCollection.load("entities.jsonl")
entity = collection.get_by_id("C0006142")
```

#### Production/Large Scale (AWS)

**Option 1: DynamoDB + S3**
```python
# Master entity collection in S3 (versioned)
s3://med-graph-entities/
  └── entities-v1.jsonl
  └── entities-v2.jsonl

# DynamoDB for fast lookups
Table: canonical-entities
  Partition Key: entity_id (e.g., "C0006142")
  Attributes: entity_type, name, synonyms, embedding, ontology_mappings
  GSI: umls_id, hgnc_id, rxnorm_id (for ontology-specific lookups)

# Lambda function for entity resolution
def resolve_entity(mention_text: str, entity_type: str) -> str:
    """Map mention → canonical ID using DynamoDB"""
    # 1. Exact match on name/synonyms
    response = dynamodb.query(
        IndexName='synonym-index',
        KeyConditionExpression='synonym = :text',
        FilterExpression='entity_type = :type'
    )
    if response['Items']:
        return response['Items'][0]['entity_id']

    # 2. Embedding similarity search via OpenSearch
    embedding = embed(mention_text)
    opensearch_results = opensearch.knn_search(
        index='entities',
        vector=embedding,
        k=5
    )
    return opensearch_results[0]['entity_id']  # Best match
```

**Option 2: Hybrid Approach**
```python
# Entities stored across multiple systems for different purposes:
# - S3 for immutable entity snapshots (version control)
# - DynamoDB for fast API lookups (entity resolution)
# - Neptune for graph queries (multi-hop traversal)
# - OpenSearch for semantic entity search (embedding similarity)
```

#### Entity Resolution Pipeline

```
Paper Processing Flow:
┌─────────────────┐
│  Raw Paper      │
│  "T2DM affects" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  NER Extract    │ ← sciSpacy/BioBERT
│  mention="T2DM" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Entity Linking  │ ← EntityCollection / DynamoDB
│ "T2DM"→C0011860 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Relationship    │
│ subject_id:     │
│   C0011860      │ ← Canonical ID used
│ predicate:      │
│   CAUSES        │
│ object_id:      │
│   C0006142      │
└─────────────────┘
```

### Why This Matters

**Without canonical entity resolution:**
- Knowledge is fragmented across different mentions
- Can't aggregate evidence from multiple papers
- Graph queries miss related information
- Contradictions can't be detected

**With canonical entity resolution:**
- ✅ One entity = one node in the graph
- ✅ Evidence accumulates across all papers
- ✅ Confidence scores improve with more papers
- ✅ Contradictions become visible (same entity, conflicting relationships)
- ✅ Multi-hop reasoning works (connected graph)

**Example Query:**
```
"What drugs treat BRCA-mutated breast cancer?"

With canonical IDs:
  BRCA1 (HGNC:1100) --[increases_risk]--> Breast Cancer (C0006142)
  Breast Cancer (C0006142) <--[treats]-- Olaparib (RxNorm: 1187832)
  Result: Olaparib found (via graph traversal)

Without canonical IDs:
  "BRCA1" --[increases_risk]--> "breast cancer"
  "Breast Cancer" <--[treats]-- "Lynparza"
  Result: No connection found (different string representations)
```

### Maintaining the Entity Collection

**Initial Population:**
1. Load from medical ontologies (UMLS, RxNorm, HGNC, etc.)
2. Generate embeddings for semantic search
3. Upload to S3 + DynamoDB

**Ongoing Updates:**
- New entities discovered during paper processing → added to collection
- Periodic refreshes from updated ontologies (quarterly)
- Versioning in S3 enables rollback if issues detected

**Quality Assurance:**
- Pydantic validation ensures all entities have required fields
- Duplicate detection (same ontology ID with different data)
- Orphan detection (entities referenced in relationships but not in collection)
