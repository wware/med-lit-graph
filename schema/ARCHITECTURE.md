# Schema Architecture: Domain/Persistence Separation Pattern

## Overview

The schema directory implements a **Domain/Persistence separation pattern** that cleanly separates application logic from database storage concerns. This architecture follows the principle that "how the code thinks about entities" should be different from "how the database stores entities."

This document explains:
1. The current architecture and design rationale
2. What has been implemented
3. What is missing (the mapper layer)
4. Implementation roadmap to complete the architecture

## Architecture Layers

### 1. Domain Models (`schema/entity.py`)

**Purpose**: "How the code thinks about entities."

**Technology**: Pure Pydantic v2 models with rich inheritance hierarchy.

**Design Characteristics**:
- **Rich class hierarchy**: `Disease`, `Gene`, `Drug`, `Protein`, etc., all inherit from `BaseMedicalEntity`
- **Type safety**: Strongly-typed with Pydantic validation
- **Clean OOP**: Pythonic object-oriented design without ORM concerns
- **Flexible**: Easy to extend and modify without database migrations
- **Standards-based**: Uses UMLS, HGNC, RxNorm, UniProt for canonical IDs

**Use Cases**:
- Ingestion pipelines processing PubMed/PMC papers
- API request/response models (FastAPI)
- Business logic and complex transformations
- Client libraries (Python, TypeScript)
- MCP server for LLM integration

**Example**:
```python
from schema import Disease, EntityType

disease = Disease(
    entity_id="C0006142",
    entity_type=EntityType.DISEASE,
    name="Breast Cancer",
    synonyms=["Breast Carcinoma", "Mammary Cancer"],
    abbreviations=["BC"],
    umls_id="C0006142",
    mesh_id="D001943",
    icd10_codes=["C50.9"],
    category="genetic",
    source="umls"
)
```

### 2. Persistence Models (`schema/entity_sqlmodel.py`)

**Purpose**: "How the database stores entities."

**Technology**: SQLModel (SQLAlchemy + Pydantic hybrid).

**Design Characteristics**:
- **Single-table inheritance**: All entity types stored in one `Entity` table
- **Flattened structure**: Type-specific fields are nullable columns
- **JSON serialization**: Complex fields (arrays, embeddings) stored as JSON strings
- **Optimized queries**: No JOINs needed to query "all entities"
- **Easier migrations**: Schema changes don't require complex table relationships

**Why Single-Table Inheritance?**
- ✅ **Performance**: Query all entities without JOINs
- ✅ **Simplicity**: One table to index, backup, and maintain
- ✅ **Flexibility**: Easy to add new entity types (just add columns)
- ✅ **Robustness**: Proven pattern for polymorphic data

**Trade-offs**:
- ⚠️ Many nullable columns (acceptable for medical domain)
- ⚠️ JSON serialization for arrays (acceptable, enables flexible storage)

**Example**:
```python
from schema.entity_sqlmodel import Entity, EntityType
import json

# Flattened persistence model
entity = Entity(
    id="C0006142",
    entity_type=EntityType.DISEASE.value,
    name="Breast Cancer",
    synonyms=json.dumps(["Breast Carcinoma", "Mammary Cancer"]),
    abbreviations=json.dumps(["BC"]),
    umls_id="C0006142",
    mesh_id="D001943",
    icd10_codes=json.dumps(["C50.9"]),
    disease_category="genetic",
    source="umls"
)
```

### 3. Mapper Layer (**MISSING**)

**Purpose**: Convert between Domain and Persistence representations.

**Expected Location**: `schema/mapper.py`

**Expected Functions**:
```python
def to_persistence(domain: BaseMedicalEntity) -> Entity:
    """Convert domain model to persistence model for database storage."""
    ...

def to_domain(persistence: Entity) -> BaseMedicalEntity:
    """Convert persistence model back to domain model."""
    ...
```

**The Documented Workflow** (from `schema/README.md`):
```
Data enters as Domain Objects → Mapper converts to Persistence Objects → Saved to DB
```

**The Current Reality**:
The mapper layer doesn't exist yet. This creates a gap between the documented architecture and actual implementation.

## Current Implementation Status

### ✅ What's Implemented

1. **Domain Models (`schema/entity.py`)**
   - ✅ Complete entity hierarchy with 14+ entity types
   - ✅ `BaseMedicalEntity` base class with common fields
   - ✅ Rich Pydantic validation
   - ✅ Evidence tracking with `EvidenceItem` class
   - ✅ `EntityCollection` for canonical entity management
   - ✅ Full ontology support (UMLS, HGNC, RxNorm, UniProt, etc.)

2. **Persistence Models (`schema/entity_sqlmodel.py`)**
   - ✅ Single `Entity` table with polymorphic discriminator
   - ✅ All entity-specific fields as nullable columns
   - ✅ JSON serialization for arrays and embeddings
   - ✅ Matches existing `migration.sql` schema
   - ✅ SQLModel integration (SQLAlchemy + Pydantic)

3. **Relationships (`schema/relationship.py`)**
   - ✅ Domain models for relationships (`Treats`, `Causes`, etc.)
   - ✅ Mandatory evidence tracking (provenance-first design)
   - ✅ `BaseMedicalRelationship` with confidence scoring
   - ✅ 30+ relationship types across clinical/molecular/provenance domains

4. **Testing**
   - ✅ Domain model tests (`tests/test_schema_entity.py`)
   - ✅ Persistence model tests (`schema/test_entity_sqlmodel.py`)
   - ✅ Validation tests for entity creation and queries

### ❌ What's Missing

1. **Mapper Functions** (`schema/mapper.py`)
   - ❌ `to_persistence()` function doesn't exist
   - ❌ `to_domain()` function doesn't exist
   - ❌ No conversion logic between domain ↔ persistence

2. **Mapper Tests**
   - ❌ No round-trip conversion tests (domain → persistence → domain)
   - ❌ No JSON serialization/deserialization tests for arrays
   - ❌ No tests verifying all entity types convert correctly

3. **Relationship Persistence**
   - ❌ No persistence models for relationships (only entities)
   - ❌ No `relationship_sqlmodel.py` module
   - ❌ Only domain models exist for relationships

4. **Integration**
   - ❌ `EntityCollection` doesn't use persistence layer
   - ❌ No database connection examples
   - ❌ No API layer demonstrating the full workflow

### ⚠️ Known Issues

1. **Polymorphic SQLAlchemy Configuration Disabled** (line 194 in `entity_sqlmodel.py`)
   ```python
   # Polymorphic configuration - Removed in favor of explicit type management
   # __mapper_args__ = {"polymorphic_on": "entity_type", "polymorphic_identity": "entity"}
   ```
   - Currently disabled, but unclear if this is intentional
   - May need to be re-enabled for polymorphic queries
   - Or document why explicit type management is preferred

## Implementation Roadmap

### Phase 1: Core Mapper (Priority: HIGH)

**Goal**: Implement the missing mapper layer to complete the documented architecture.

**Tasks**:
1. Create `schema/mapper.py` with core functions
2. Implement `to_persistence()` for all entity types
3. Implement `to_domain()` for all entity types
4. Handle JSON serialization for arrays and embeddings
5. Support polymorphic conversion (detect entity type and return correct class)

**Expected Implementation**:

```python
"""
Mapper functions to convert between Domain Models and Persistence Models.

This module bridges the gap between:
- Domain Models (schema/entity.py) - Rich Pydantic classes for application logic
- Persistence Models (schema/entity_sqlmodel.py) - Flattened SQLModel for database
"""

import json
from typing import Union

from .entity import (
    BaseMedicalEntity,
    Disease,
    Gene,
    Drug,
    Protein,
    Mutation,
    Symptom,
    Biomarker,
    Pathway,
    Procedure,
    Paper,
    Author,
    Hypothesis,
    StudyDesign,
    StatisticalMethod,
    EvidenceLine,
    EntityType,
)
from .entity_sqlmodel import Entity


def to_persistence(domain: BaseMedicalEntity) -> Entity:
    """
    Convert a domain model to a persistence model for database storage.

    Args:
        domain: Any domain entity (Disease, Gene, Drug, etc.)

    Returns:
        Flattened Entity model ready for database insertion

    Example:
        >>> disease = Disease(
        ...     entity_id="C0006142",
        ...     entity_type=EntityType.DISEASE,
        ...     name="Breast Cancer",
        ...     synonyms=["Breast Carcinoma"],
        ...     umls_id="C0006142"
        ... )
        >>> entity = to_persistence(disease)
        >>> entity.entity_type == "disease"
        True
    """
    # Common fields for all entities
    base_data = {
        "id": domain.entity_id,
        "entity_type": domain.entity_type.value if hasattr(domain.entity_type, 'value') else domain.entity_type,
        "name": domain.name,
        "synonyms": json.dumps(domain.synonyms) if domain.synonyms else None,
        "abbreviations": json.dumps(domain.abbreviations) if domain.abbreviations else None,
        "embedding": json.dumps(domain.embedding) if domain.embedding else None,
        "created_at": domain.created_at,
        "source": domain.source,
    }

    # Type-specific fields
    if isinstance(domain, Disease):
        base_data.update({
            "umls_id": domain.umls_id,
            "mesh_id": domain.mesh_id,
            "icd10_codes": json.dumps(domain.icd10_codes) if domain.icd10_codes else None,
            "disease_category": domain.category,
        })
    elif isinstance(domain, Gene):
        base_data.update({
            "symbol": domain.symbol,
            "hgnc_id": domain.hgnc_id,
            "chromosome": domain.chromosome,
            "entrez_id": domain.entrez_id,
        })
    elif isinstance(domain, Drug):
        base_data.update({
            "rxnorm_id": domain.rxnorm_id,
            "brand_names": json.dumps(domain.brand_names) if domain.brand_names else None,
            "drug_class": domain.drug_class,
            "mechanism": domain.mechanism,
        })
    elif isinstance(domain, Protein):
        base_data.update({
            "uniprot_id": domain.uniprot_id,
            "gene_id": domain.gene_id,
            "function": domain.function,
            "pathways": json.dumps(domain.pathways) if domain.pathways else None,
        })
    # Add other entity types as needed...

    return Entity(**base_data)


def to_domain(persistence: Entity) -> BaseMedicalEntity:
    """
    Convert a persistence model back to a domain model.

    Args:
        persistence: Flattened Entity from database

    Returns:
        Rich domain model (Disease, Gene, Drug, etc.)

    Example:
        >>> entity = Entity(
        ...     id="C0006142",
        ...     entity_type="disease",
        ...     name="Breast Cancer",
        ...     umls_id="C0006142"
        ... )
        >>> disease = to_domain(entity)
        >>> isinstance(disease, Disease)
        True
    """
    # Parse common JSON fields
    synonyms = json.loads(persistence.synonyms) if persistence.synonyms else []
    abbreviations = json.loads(persistence.abbreviations) if persistence.abbreviations else []
    embedding = json.loads(persistence.embedding) if persistence.embedding else None

    # Common fields
    base_data = {
        "entity_id": persistence.id,
        "entity_type": persistence.entity_type,
        "name": persistence.name,
        "synonyms": synonyms,
        "abbreviations": abbreviations,
        "embedding": embedding,
        "created_at": persistence.created_at,
        "source": persistence.source,
    }

    # Polymorphic conversion based on entity_type
    if persistence.entity_type == EntityType.DISEASE.value or persistence.entity_type == "disease":
        return Disease(
            **base_data,
            umls_id=persistence.umls_id,
            mesh_id=persistence.mesh_id,
            icd10_codes=json.loads(persistence.icd10_codes) if persistence.icd10_codes else None,
            category=persistence.disease_category,
        )
    elif persistence.entity_type == EntityType.GENE.value or persistence.entity_type == "gene":
        return Gene(
            **base_data,
            symbol=persistence.symbol,
            hgnc_id=persistence.hgnc_id,
            chromosome=persistence.chromosome,
            entrez_id=persistence.entrez_id,
        )
    elif persistence.entity_type == EntityType.DRUG.value or persistence.entity_type == "drug":
        return Drug(
            **base_data,
            rxnorm_id=persistence.rxnorm_id,
            brand_names=json.loads(persistence.brand_names) if persistence.brand_names else None,
            drug_class=persistence.drug_class,
            mechanism=persistence.mechanism,
        )
    elif persistence.entity_type == EntityType.PROTEIN.value or persistence.entity_type == "protein":
        return Protein(
            **base_data,
            uniprot_id=persistence.uniprot_id,
            gene_id=persistence.gene_id,
            function=persistence.function,
            pathways=json.loads(persistence.pathways) if persistence.pathways else None,
        )
    # Add other entity types...
    else:
        raise ValueError(f"Unknown entity type: {persistence.entity_type}")


# Convenience functions for batch operations
def to_persistence_batch(domains: list[BaseMedicalEntity]) -> list[Entity]:
    """Convert multiple domain models to persistence models."""
    return [to_persistence(d) for d in domains]


def to_domain_batch(persistences: list[Entity]) -> list[BaseMedicalEntity]:
    """Convert multiple persistence models to domain models."""
    return [to_domain(p) for p in persistences]
```

**Estimated Effort**: 2-3 days
- Day 1: Core functions for Disease, Gene, Drug, Protein
- Day 2: Remaining entity types (Mutation, Symptom, etc.)
- Day 3: Edge cases and JSON handling

### Phase 2: Mapper Tests (Priority: HIGH)

**Goal**: Comprehensive test coverage for mapper functions.

**Tasks**:
1. Create `tests/test_mapper.py`
2. Test round-trip conversion for all entity types
3. Test JSON serialization/deserialization
4. Test edge cases (empty arrays, null fields)
5. Test error handling (unknown entity types)

**Expected Test Structure**:

```python
"""
Tests for mapper functions converting between domain and persistence models.
"""

import json
import pytest

from schema.entity import Disease, Gene, Drug, EntityType
from schema.entity_sqlmodel import Entity
from schema.mapper import to_persistence, to_domain


def test_disease_roundtrip():
    """Test domain → persistence → domain conversion for Disease."""
    # Create domain model
    disease = Disease(
        entity_id="C0006142",
        entity_type=EntityType.DISEASE,
        name="Breast Cancer",
        synonyms=["Breast Carcinoma", "Mammary Cancer"],
        abbreviations=["BC"],
        umls_id="C0006142",
        mesh_id="D001943",
        icd10_codes=["C50.9"],
        category="genetic",
        source="umls"
    )

    # Convert to persistence
    entity = to_persistence(disease)
    assert entity.id == "C0006142"
    assert entity.entity_type == "disease"
    assert entity.name == "Breast Cancer"
    assert json.loads(entity.synonyms) == ["Breast Carcinoma", "Mammary Cancer"]
    assert entity.umls_id == "C0006142"

    # Convert back to domain
    disease2 = to_domain(entity)
    assert isinstance(disease2, Disease)
    assert disease2.entity_id == disease.entity_id
    assert disease2.name == disease.name
    assert disease2.synonyms == disease.synonyms
    assert disease2.umls_id == disease.umls_id


def test_gene_roundtrip():
    """Test domain → persistence → domain conversion for Gene."""
    gene = Gene(
        entity_id="HGNC:1100",
        entity_type=EntityType.GENE,
        name="BRCA1",
        symbol="BRCA1",
        hgnc_id="HGNC:1100",
        chromosome="17q21.31",
        source="hgnc"
    )

    entity = to_persistence(gene)
    gene2 = to_domain(entity)

    assert isinstance(gene2, Gene)
    assert gene2.entity_id == gene.entity_id
    assert gene2.symbol == gene.symbol


def test_json_array_handling():
    """Test that arrays are properly serialized/deserialized."""
    disease = Disease(
        entity_id="C0001",
        entity_type=EntityType.DISEASE,
        name="Test Disease",
        synonyms=["Syn1", "Syn2", "Syn3"],
        abbreviations=["TD"],
        icd10_codes=["C01", "C02"]
    )

    entity = to_persistence(disease)

    # Check JSON strings are valid
    assert isinstance(entity.synonyms, str)
    assert json.loads(entity.synonyms) == ["Syn1", "Syn2", "Syn3"]

    # Round-trip preserves arrays
    disease2 = to_domain(entity)
    assert disease2.synonyms == disease.synonyms
    assert disease2.icd10_codes == disease.icd10_codes


def test_empty_arrays():
    """Test handling of empty arrays."""
    disease = Disease(
        entity_id="C0002",
        entity_type=EntityType.DISEASE,
        name="Test",
        synonyms=[],  # Empty
        abbreviations=[]  # Empty
    )

    entity = to_persistence(disease)
    disease2 = to_domain(entity)

    assert disease2.synonyms == []
    assert disease2.abbreviations == []


def test_unknown_entity_type():
    """Test error handling for unknown entity types."""
    entity = Entity(
        id="UNKNOWN:123",
        entity_type="unknown_type",
        name="Unknown"
    )

    with pytest.raises(ValueError, match="Unknown entity type"):
        to_domain(entity)
```

**Estimated Effort**: 1-2 days

### Phase 3: Polymorphic Query Configuration (Priority: MEDIUM)

**Goal**: Determine if polymorphic SQLAlchemy configuration should be enabled.

**Tasks**:
1. Research SQLAlchemy single-table inheritance patterns
2. Test performance with/without polymorphic configuration
3. Document decision with rationale
4. Either re-enable with documentation or document why it's disabled

**Investigation Questions**:
- Does explicit type filtering (`WHERE entity_type = 'disease'`) perform well?
- Would polymorphic queries improve API ergonomics?
- Are there any downsides to re-enabling it?

**Estimated Effort**: 1 day

### Phase 4: Relationship Persistence (Priority: MEDIUM)

**Goal**: Add persistence layer for relationships (not just entities).

**Tasks**:
1. Create `schema/relationship_sqlmodel.py`
2. Design single-table or multi-table approach for relationships
3. Implement relationship persistence models
4. Add mapper functions for relationships
5. Add tests for relationship persistence

**Design Considerations**:
- Should relationships also use single-table inheritance?
- How to store evidence arrays efficiently?
- How to query relationships by type and confidence?

**Estimated Effort**: 3-4 days

### Phase 5: Integration Examples (Priority: LOW)

**Goal**: Demonstrate the full workflow in production-like scenarios.

**Tasks**:
1. Update `EntityCollection` to use persistence layer
2. Add database connection examples
3. Create end-to-end example: load entities → query → save
4. Add API examples using FastAPI with mapper
5. Document best practices for using the architecture

**Estimated Effort**: 2-3 days

## Key Design Rationale

### Why Separate Domain and Persistence Models?

**Alternative Approach (Single Model)**:
```python
# Combine domain + persistence in one class
class Disease(SQLModel, table=True):
    # This mixes ORM concerns with business logic
    ...
```

**Rejected Because**:
- ❌ ORM annotations pollute domain logic
- ❌ Database migrations affect application code
- ❌ Hard to use in contexts without database (API clients, tests)
- ❌ SQLAlchemy dependencies leak into business logic

**Our Approach (Separation)**:
```python
# Domain: Pure Pydantic, no database concerns
class Disease(BaseMedicalEntity):
    ...

# Persistence: SQLModel, database-optimized
class Entity(SQLModel, table=True):
    ...

# Mapper: Bridge between the two
def to_persistence(disease: Disease) -> Entity:
    ...
```

**Benefits**:
- ✅ Clean separation of concerns
- ✅ Domain models work without database (tests, client libraries)
- ✅ Can optimize database schema independently
- ✅ Easier to swap database implementation
- ✅ Better testability (mock mapper in tests)

### Why Single-Table Inheritance for Persistence?

**Alternative Approaches**:

1. **Joined-Table Inheritance** (separate table per entity type)
   ```sql
   CREATE TABLE entities (...);
   CREATE TABLE diseases (...) INHERITS entities;
   CREATE TABLE genes (...) INHERITS entities;
   ```
   - ❌ Requires JOINs for polymorphic queries
   - ❌ Complex migrations when adding fields
   - ❌ Harder to query "all entities"

2. **Multiple Tables** (no inheritance)
   ```sql
   CREATE TABLE diseases (...);
   CREATE TABLE genes (...);
   CREATE TABLE drugs (...);
   ```
   - ❌ Can't query across entity types
   - ❌ Relationship tables need multiple foreign keys
   - ❌ Duplicates common fields

3. **Single-Table Inheritance** (current approach)
   ```sql
   CREATE TABLE entities (
     id TEXT PRIMARY KEY,
     entity_type TEXT,  -- discriminator
     name TEXT,
     -- Disease fields (nullable)
     umls_id TEXT,
     -- Gene fields (nullable)
     hgnc_id TEXT,
     ...
   );
   ```
   - ✅ No JOINs needed
   - ✅ Simple queries: `SELECT * FROM entities WHERE entity_type = 'disease'`
   - ✅ Easy migrations (ALTER TABLE ADD COLUMN)
   - ✅ Proven pattern (used by Django, Rails, etc.)

## Related Documentation

- **[schema/README.md](README.md)** - Schema overview and design philosophy
- **[schema/entity.py](entity.py)** - Domain model implementations
- **[schema/entity_sqlmodel.py](entity_sqlmodel.py)** - Persistence model implementation
- **[schema/relationship.py](relationship.py)** - Relationship domain models
- **[docs/DESIGN_DECISIONS.md](../docs/DESIGN_DECISIONS.md)** - Overall architectural decisions
- **[tests/test_schema_entity.py](../tests/test_schema_entity.py)** - Domain model tests
- **[schema/test_entity_sqlmodel.py](test_entity_sqlmodel.py)** - Persistence model tests

## Summary

The schema architecture is **80% complete**:
- ✅ Domain models fully implemented
- ✅ Persistence models fully implemented
- ❌ **Mapper layer missing** (critical gap)
- ❌ Relationship persistence missing

The documented workflow ("Domain Objects → Mapper → Persistence → DB") cannot currently be executed because the mapper layer doesn't exist. This ARCHITECTURE.md document provides a clear roadmap to complete the implementation.

**Next Steps**:
1. Implement `schema/mapper.py` (Phase 1)
2. Add comprehensive mapper tests (Phase 2)
3. Update documentation with usage examples

Once the mapper is implemented, the architecture will be complete and match the documented design.
