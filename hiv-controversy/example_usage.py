"""
Example Usage: Pydantic Schema with SQLite and PostgreSQL/AGE

Demonstrates how the updated schema works with both databases.
"""

import sqlite3

from base import EntityType, EntityReference, ExtractionEdge, ModelInfo
from entity import Disease
from relationship import Treats
from db_serialization import (
    serialize_entity_to_sqlite,
    deserialize_entity_from_sqlite,
    cypher_create_relationship,
    cypher_create_vertex
)


# ============================================================================
# Example 1: Creating and validating entities with Pydantic
# ============================================================================

print("=" * 60)
print("Example 1: Creating Pydantic Disease entity")
print("=" * 60)

# Create a Disease entity - Pydantic validates all fields
disease = Disease(
    entity_id="C0011860",
    name="Type 2 Diabetes Mellitus",
    synonyms=["Type II Diabetes", "Adult-Onset Diabetes"],
    abbreviations=["T2DM", "NIDDM"],
    umls_id="C0011860",
    mesh_id="D003924",
    category="metabolic",
    source="umls"
)

print(f"Created: {disease.name}")
print(f"Entity ID: {disease.entity_id}")
print(f"Type: {disease.entity_type}")
print(f"Synonyms: {disease.synonyms}")
print()


# ============================================================================
# Example 2: Storing Pydantic entity in SQLite
# ============================================================================

print("=" * 60)
print("Example 2: Storing in SQLite")
print("=" * 60)

# Connect to SQLite
conn = sqlite3.connect(":memory:")  # Use in-memory for demo
conn.execute("""
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE,
    canonical_name TEXT,
    type TEXT,
    entity_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
)
""")

# Serialize and insert
entity_dict = serialize_entity_to_sqlite(disease)
conn.execute(
    "INSERT INTO entities (entity_id, canonical_name, type, entity_json) VALUES (?, ?, ?, ?)",
    (entity_dict['entity_id'], entity_dict['canonical_name'],
     entity_dict['type'], entity_dict['entity_json'])
)
conn.commit()

print(f"Stored in SQLite: {entity_dict['canonical_name']}")
print(f"  entity_id: {entity_dict['entity_id']}")
print(f"  type: {entity_dict['type']}")
print(f"  entity_json length: {len(entity_dict['entity_json'])} chars")
print()

# Retrieve and deserialize
cursor = conn.execute("SELECT * FROM entities WHERE entity_id=?", ("C0011860",))
row = cursor.fetchone()
retrieved_disease = deserialize_entity_from_sqlite(row, EntityType.DISEASE)

print(f"Retrieved from SQLite: {retrieved_disease.name}")
print(f"  Synonyms preserved: {retrieved_disease.synonyms}")
print(f"  Validation: {retrieved_disease.entity_type == EntityType.DISEASE}")
print()


# ============================================================================
# Example 3: Creating ExtractionEdge with provenance
# ============================================================================

print("=" * 60)
print("Example 3: Creating ExtractionEdge")
print("=" * 60)

# Create entity references
metformin_ref = EntityReference(
    id="RxNorm:6809",
    name="Metformin",
    type=EntityType.DRUG
)

diabetes_ref = EntityReference(
    id="C0011860",
    name="Type 2 Diabetes Mellitus",
    type=EntityType.DISEASE
)

# Model info for provenance
model_info = ModelInfo(
    name="biobert_ncbi_disease_ner",
    provider="huggingface",
    temperature=None,
    version="v1"
)

# Create extraction edge with placeholder provenance
# (In real code, use proper Provenance from base.py)
extraction_edge = ExtractionEdge(
    id="edge-001",  # Will be UUID in real code
    subject=metformin_ref,
    object=diabetes_ref,
    provenance={},  # Placeholder
    extractor=model_info,
    confidence=0.92
)

print("Created ExtractionEdge:")
print(f"  Subject: {extraction_edge.subject.name}")
print(f"  Object: {extraction_edge.object.name}")
print(f"  Confidence: {extraction_edge.confidence}")
print(f"  Extractor: {extraction_edge.extractor.name}")
print()


# ============================================================================
# Example 4: Serializing to PostgreSQL/AGE (Cypher)
# ============================================================================

print("=" * 60)
print("Example 4: Generating Cypher for AGE")
print("=" * 60)

# Generate Cypher for vertex (entity)
vertex_cypher = cypher_create_vertex(disease)
print("Cypher to create vertex:")
print(vertex_cypher)
print()

# Generate Cypher for edge
# Note: This would fail with placeholder provenance in real use
# Uncomment when Provenance is properly defined
# edge_cypher = cypher_create_edge(extraction_edge)
# print("Cypher to create extraction edge:")
# print(edge_cypher)
# print()


# ============================================================================
# Example 5: Creating and serializing relationships
# ============================================================================

print("=" * 60)
print("Example 5: Creating Treats relationship")
print("=" * 60)

# Create a Treats relationship with rich metadata
treats = Treats(
    subject_id="RxNorm:6809",  # Metformin
    object_id="C0011860",  # Type 2 Diabetes
    confidence=0.95,
    source_papers=["PMC123", "PMC456", "PMC789"],
    evidence_count=3,
    efficacy="Reduces HbA1c by 1-2%",
    response_rate=0.75,
    line_of_therapy="first-line",
    indication="Type 2 Diabetes Mellitus"
)

print("Created Treats relationship:")
print(f"  Drug: {treats.subject_id}")
print(f"  Disease: {treats.object_id}")
print(f"  Confidence: {treats.confidence}")
print(f"  Evidence papers: {len(treats.source_papers)}")
print(f"  Response rate: {treats.response_rate}")
print()

# Generate Cypher for relationship
rel_cypher = cypher_create_relationship(treats)
print("Cypher to create TREATS relationship:")
print(rel_cypher)
print()


# ============================================================================
# Summary
# ============================================================================

print("=" * 60)
print("Summary: Benefits of This Architecture")
print("=" * 60)
print("""
1. **Type Safety**: Pydantic validates all fields at creation time
2. **Rich Schema**: Entities have proper fields (umls_id, synonyms, etc.)
3. **Provenance**: Full extraction metadata tracked
4. **Flexible Storage**: Same models work with SQLite and PostgreSQL/AGE
5. **Three-Layer Edges**: ExtractionEdge, ClaimEdge, EvidenceEdge keep concerns separate
6. **Bidirectional**: Easy to serialize to DB and deserialize back to Python

The schema is the source of truth in Python.
Databases are just storage layers.
""")

conn.close()
