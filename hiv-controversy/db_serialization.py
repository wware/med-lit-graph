"""
Database Serialization Helpers

Provides functions to serialize/deserialize Pydantic models to/from:
1. SQLite (canonical entity store)
2. PostgreSQL/AGE (graph store)

Design Philosophy:
- Pydantic models are the source of truth in Python
- Databases are storage layers with their own query capabilities
- Serialization is bidirectional: Python <-> Database
"""

import json
from typing import Dict, Any, List
import uuid

from base import (
    EntityType, ExtractionEdge, ClaimEdge, EvidenceEdge, Edge
)
from entity import Disease, Gene, Drug, Protein, BaseMedicalEntity
from relationship import BaseMedicalRelationship


# ============================================================================
# SQLite Serialization
# ============================================================================

def serialize_entity_to_sqlite(entity: BaseMedicalEntity) -> Dict[str, Any]:
    """
    Serialize a Pydantic entity model to SQLite-compatible dict.

    Stores the full model as JSON for complete reconstruction,
    plus key fields extracted for efficient querying.

    Args:
        entity: Any BaseMedicalEntity subclass (Disease, Gene, Drug, etc.)

    Returns:
        Dict with keys: entity_id, canonical_name, type, entity_json

    Example:
        >>> disease = Disease(entity_id="C0011860", name="Type 2 Diabetes")
        >>> row = serialize_entity_to_sqlite(disease)
        >>> # Insert into SQLite:
        >>> # INSERT INTO entities (entity_id, canonical_name, type, entity_json)
        >>> # VALUES (row['entity_id'], row['canonical_name'], row['type'], row['entity_json'])
    """
    return {
        'entity_id': entity.entity_id,
        'canonical_name': entity.name,
        'type': entity.entity_type,
        'entity_json': entity.model_dump_json()
    }


def deserialize_entity_from_sqlite(row: tuple, entity_type: EntityType) -> BaseMedicalEntity:
    """
    Deserialize an entity from SQLite row.

    Args:
        row: (id, entity_id, canonical_name, type, entity_json, created_at, updated_at)
        entity_type: EntityType enum to determine which class to deserialize to

    Returns:
        Appropriate entity subclass instance

    Example:
        >>> cursor = conn.execute("SELECT * FROM entities WHERE entity_id=?", ("C0011860",))
        >>> row = cursor.fetchone()
        >>> disease = deserialize_entity_from_sqlite(row, EntityType.DISEASE)
    """
    entity_json = row[4]  # entity_json column

    # Map EntityType to appropriate Pydantic class
    type_to_class = {
        EntityType.DISEASE: Disease,
        EntityType.GENE: Gene,
        EntityType.DRUG: Drug,
        EntityType.PROTEIN: Protein,
        # Add others as needed
    }

    entity_class = type_to_class.get(entity_type)
    if entity_class is None:
        raise ValueError(f"Unknown entity type: {entity_type}")

    return entity_class.model_validate_json(entity_json)


# ============================================================================
# PostgreSQL/AGE Serialization
# ============================================================================

def serialize_edge_to_age(edge: Edge) -> Dict[str, Any]:
    """
    Serialize an edge (ExtractionEdge, ClaimEdge, EvidenceEdge) to AGE Cypher format.

    AGE uses Cypher query language. This creates a dict that can be used
    in a CREATE statement.

    Args:
        edge: Any Edge subclass

    Returns:
        Dict with keys: edge_id, subject_id, object_id, edge_type, properties

    Example:
        >>> edge = ExtractionEdge(...)
        >>> age_dict = serialize_edge_to_age(edge)
        >>> # Use in Cypher:
        >>> # CREATE (s)-[r:EXTRACTION_EDGE {properties}]->(o)
    """
    # Determine edge type for AGE label
    edge_type_map = {
        ExtractionEdge: "EXTRACTION_EDGE",
        ClaimEdge: "CLAIM_EDGE",
        EvidenceEdge: "EVIDENCE_EDGE"
    }
    edge_type = edge_type_map.get(type(edge), "EDGE")

    # Serialize all properties as JSON
    properties = edge.model_dump()

    # Convert UUIDs to strings
    if isinstance(properties.get('id'), uuid.UUID):
        properties['id'] = str(properties['id'])

    # Convert nested objects to JSON strings for AGE storage
    if 'subject' in properties:
        properties['subject'] = json.dumps(properties['subject'])
    if 'object' in properties:
        properties['object'] = json.dumps(properties['object'])
    if 'provenance' in properties:
        properties['provenance'] = json.dumps(properties['provenance'])
    if 'extractor' in properties:
        properties['extractor'] = json.dumps(properties['extractor'])

    return {
        'edge_id': str(properties['id']),
        'subject_id': edge.subject.id,
        'object_id': edge.object.id,
        'edge_type': edge_type,
        'properties': json.dumps(properties)  # Store full properties as JSON
    }


def cypher_create_edge(edge: Edge) -> str:
    """
    Generate Cypher CREATE statement for an edge.

    Args:
        edge: Any Edge subclass

    Returns:
        Cypher statement string

    Example:
        >>> edge = ExtractionEdge(...)
        >>> cypher = cypher_create_edge(edge)
        >>> # Execute in AGE:
        >>> # cursor.execute(cypher)
    """
    age_dict = serialize_edge_to_age(edge)

    cypher = f"""
    MATCH (s {{entity_id: '{age_dict['subject_id']}'}})
    MATCH (o {{entity_id: '{age_dict['object_id']}'}})
    CREATE (s)-[r:{age_dict['edge_type']} {{
        edge_id: '{age_dict['edge_id']}',
        properties: '{age_dict['properties']}'
    }}]->(o)
    RETURN r
    """
    return cypher


def serialize_relationship_to_age(relationship: BaseMedicalRelationship) -> Dict[str, Any]:
    """
    Serialize a relationship (Treats, Causes, etc.) to AGE Cypher format.

    Args:
        relationship: Any BaseMedicalRelationship subclass

    Returns:
        Dict with keys: subject_id, predicate, object_id, properties

    Example:
        >>> treats = Treats(subject_id="RxNorm:123", object_id="C0011860", ...)
        >>> age_dict = serialize_relationship_to_age(treats)
    """
    properties = relationship.model_dump()

    # The predicate becomes the edge label in AGE
    predicate = properties.pop('predicate')

    return {
        'subject_id': relationship.subject_id,
        'predicate': predicate,
        'object_id': relationship.object_id,
        'properties': json.dumps(properties)
    }


def cypher_create_relationship(relationship: BaseMedicalRelationship) -> str:
    """
    Generate Cypher CREATE statement for a relationship.

    Args:
        relationship: Any BaseMedicalRelationship subclass

    Returns:
        Cypher statement string

    Example:
        >>> treats = Treats(...)
        >>> cypher = cypher_create_relationship(treats)
        >>> # Execute in AGE
    """
    rel_dict = serialize_relationship_to_age(relationship)

    cypher = f"""
    MATCH (s {{entity_id: '{rel_dict['subject_id']}'}})
    MATCH (o {{entity_id: '{rel_dict['object_id']}'}})
    CREATE (s)-[r:{rel_dict['predicate']} {{
        properties: '{rel_dict['properties']}'
    }}]->(o)
    RETURN r
    """
    return cypher


def serialize_entity_to_age(entity: BaseMedicalEntity) -> Dict[str, Any]:
    """
    Serialize an entity to AGE vertex format.

    Args:
        entity: Any BaseMedicalEntity subclass

    Returns:
        Dict with keys: entity_id, label, properties

    Example:
        >>> disease = Disease(entity_id="C0011860", name="Type 2 Diabetes")
        >>> age_dict = serialize_entity_to_age(disease)
    """
    properties = entity.model_dump()

    # Use entity_type as the vertex label
    label = entity.entity_type

    return {
        'entity_id': entity.entity_id,
        'label': label,
        'properties': json.dumps(properties)
    }


def cypher_create_vertex(entity: BaseMedicalEntity) -> str:
    """
    Generate Cypher CREATE statement for a vertex.

    Args:
        entity: Any BaseMedicalEntity subclass

    Returns:
        Cypher statement string

    Example:
        >>> disease = Disease(...)
        >>> cypher = cypher_create_vertex(disease)
    """
    entity_dict = serialize_entity_to_age(entity)

    cypher = f"""
    CREATE (n:{entity_dict['label']} {{
        entity_id: '{entity_dict['entity_id']}',
        properties: '{entity_dict['properties']}'
    }})
    RETURN n
    """
    return cypher


# ============================================================================
# Batch Operations
# ============================================================================

def batch_insert_edges_to_age(edges: List[Edge], batch_size: int = 100) -> List[str]:
    """
    Generate batched Cypher statements for bulk edge insertion.

    Args:
        edges: List of Edge objects
        batch_size: Number of edges per batch

    Returns:
        List of Cypher statements (one per batch)

    Example:
        >>> edges = [edge1, edge2, edge3, ...]
        >>> cyphers = batch_insert_edges_to_age(edges, batch_size=100)
        >>> for cypher in cyphers:
        ...     cursor.execute(cypher)
    """
    batches = []
    for i in range(0, len(edges), batch_size):
        batch = edges[i:i + batch_size]
        # Generate multi-statement batch
        statements = [cypher_create_edge(edge) for edge in batch]
        batches.append("\n".join(statements))
    return batches


# ============================================================================
# Query Helpers
# ============================================================================

def cypher_find_entity(entity_id: str) -> str:
    """
    Generate Cypher query to find an entity by ID.

    Args:
        entity_id: Entity ID to search for

    Returns:
        Cypher query string

    Example:
        >>> query = cypher_find_entity("C0011860")
        >>> # cursor.execute(query)
    """
    return f"MATCH (n {{entity_id: '{entity_id}'}}) RETURN n"


def cypher_find_edges_between(subject_id: str, object_id: str) -> str:
    """
    Generate Cypher query to find all edges between two entities.

    Args:
        subject_id: Subject entity ID
        object_id: Object entity ID

    Returns:
        Cypher query string
    """
    return f"""
    MATCH (s {{entity_id: '{subject_id}'}})-[r]->(o {{entity_id: '{object_id}'}})
    RETURN r
    """


def cypher_find_extraction_edges() -> str:
    """
    Generate Cypher query to find all extraction edges.

    Returns:
        Cypher query string
    """
    return "MATCH ()-[r:EXTRACTION_EDGE]->() RETURN r"
