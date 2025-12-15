"""
Medical Knowledge Graph Schema

This package defines the complete schema for the medical knowledge graph,
including entity types, relationship types, and supporting classes for
evidence tracking and measurements.

The schema is organized into three main modules:
- entity: Entity type definitions and entity classes
- relationship: Relationship type definitions and relationship classes
- Supporting classes: EvidenceItem, Measurement for rich provenance tracking

Quick Start Examples:

    # Create entities
    from schema.entity import Disease, Drug, EntityType

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

    # Create relationships
    from schema.relationship import Treats, PredicateType

    treats = Treats(
        subject_id=drug.entity_id,
        predicate=PredicateType.TREATS,
        object_id=disease.entity_id,
        response_rate=0.59,
        source_papers=["PMC999"],
        confidence=0.85
    )

    # Or use factory function
    from schema.relationship import create_relationship

    rel = create_relationship(
        PredicateType.TREATS,
        subject_id=drug.entity_id,
        object_id=disease.entity_id,
        response_rate=0.59
    )
"""

# Entity types and classes
from .entity import (
    Author,
    BaseMedicalEntity,
    Biomarker,
    ClinicalTrial,
    Disease,
    Drug,
    EntityCollection,
    EntityMention,
    EntityType,
    EvidenceItem,
    EvidenceLine,
    ExtractedEntity,
    Gene,
    Hypothesis,
    Measurement,
    Mutation,
    Paper,
    Pathway,
    Procedure,
    ProcessedPaper,
    Protein,
    StatisticalMethod,
    StudyDesign,
    Symptom,
    generate_embeddings_for_entities,
)

# Relationship types and classes
from .relationship import (
    AssociatedWith,
    AuthoredBy,
    BaseMedicalRelationship,
    BaseRelationship,
    Causes,
    Cites,
    ContraindicatedFor,
    DiagnosedBy,
    Encodes,
    Generates,
    IncreasesRisk,
    InteractsWith,
    ParticipatesIn,
    PartOf,
    Predicts,
    Refutes,
    PredicateType,
    ResearchRelationship,
    SideEffect,
    StudiedIn,
    TestedBy,
    Treats,
    create_relationship,
)

__all__ = [
    # Enums
    "EntityType",
    "PredicateType",
    # Base classes
    "BaseMedicalEntity",
    "BaseRelationship",
    "BaseMedicalRelationship",
    "ResearchRelationship",
    # Entity classes
    "Disease",
    "Gene",
    "Mutation",
    "Drug",
    "Protein",
    "Symptom",
    "Procedure",
    "Biomarker",
    "Pathway",
    "Paper",
    "Author",
    "ClinicalTrial",
    "ExtractedEntity",
    "EntityMention",
    "ProcessedPaper",
    "EntityCollection",
    # Scientific method entities
    "Hypothesis",
    "StudyDesign",
    "StatisticalMethod",
    "EvidenceLine",
    # Evidence and measurements
    "EvidenceItem",
    "Measurement",
    # Relationship classes
    "Causes",
    "Treats",
    "IncreasesRisk",
    "AssociatedWith",
    "InteractsWith",
    "Encodes",
    "ParticipatesIn",
    "ContraindicatedFor",
    "DiagnosedBy",
    "SideEffect",
    "Cites",
    "StudiedIn",
    "AuthoredBy",
    "PartOf",
    # Hypothesis and evidence relationships
    "Predicts",
    "Refutes",
    "TestedBy",
    "Generates",
    # Utility functions
    "create_relationship",
    "generate_embeddings_for_entities",
]
