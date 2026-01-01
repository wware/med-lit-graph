"""
SQLModel Three-Layer Edge Architecture - Proof of Concept
==========================================================

Demonstrates single-table inheritance for medical knowledge graph with:
- ExtractionEdge: What models extracted from text
- ClaimEdge: What papers assert as true
- EvidenceEdge: Empirical evidence from studies

All edge types in one table with type-safe polymorphism.
"""

from datetime import datetime
from typing import List, Optional, Literal
from uuid import uuid4, UUID
from enum import Enum

from sqlmodel import (
    SQLModel, Field, Relationship, Session,
    create_engine, select, Column, CheckConstraint
)
from sqlalchemy import JSON


# ============================================================================
# Enums
# ============================================================================

class EntityType(str, Enum):
    DISEASE = "disease"
    DRUG = "drug"
    GENE = "gene"

class PredicateType(str, Enum):
    TREATS = "treats"
    CAUSES = "causes"
    INCREASES_RISK = "increases_risk"

class StudyType(str, Enum):
    RCT = "rct"
    OBSERVATIONAL = "observational"
    META_ANALYSIS = "meta_analysis"
    CASE_REPORT = "case_report"

class Polarity(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"


# ============================================================================
# Entities (Simplified - no inheritance)
# ============================================================================

class Disease(SQLModel, table=True):
    """Diseases, disorders, and syndromes"""
    __tablename__ = "diseases"

    id: str = Field(primary_key=True)
    name: str
    umls_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Drug(SQLModel, table=True):
    """Medications and therapeutic substances"""
    __tablename__ = "drugs"

    id: str = Field(primary_key=True)
    name: str
    rxnorm_id: Optional[str] = None
    drug_class: Optional[str] = None
    mechanism: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Papers
# ============================================================================

class Paper(SQLModel, table=True):
    """Research papers"""
    __tablename__ = "papers"

    paper_id: str = Field(primary_key=True)
    title: str
    abstract: str
    study_type: Optional[str] = None
    sample_size: Optional[int] = None
    publication_date: Optional[str] = None

    # Provenance
    extraction_model: Optional[str] = None
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Three-Layer Edge Architecture with Single-Table Inheritance
# ============================================================================

# ============================================================================
# Three-Layer Edge Architecture with Single Table
# ============================================================================

class Edge(SQLModel, table=True):
    """
    All edge types (Extraction/Claim/Evidence) stored in one table.

    The 'layer' field discriminates between types:
    - 'extraction': What models extracted from text
    - 'claim': What papers assert as true
    - 'evidence': Empirical evidence from studies

    Layer-specific fields are Optional, allowing flexibility.
    Use helper functions to create type-safe edges.
    """
    __tablename__ = "edges"

    # ===== Common Fields (all edge types) =====
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    layer: str = Field(index=True)  # 'extraction', 'claim', 'evidence'

    # The relationship being asserted
    subject_id: str = Field(index=True)
    subject_name: str
    subject_type: str  # 'drug', 'disease', etc.

    object_id: str = Field(index=True)
    object_name: str
    object_type: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ===== ExtractionEdge Fields (nullable) =====
    extractor_name: Optional[str] = None          # e.g., "llama3.1:70b"
    extractor_provider: Optional[str] = None      # e.g., "ollama", "anthropic"
    extraction_confidence: Optional[float] = None # 0.0-1.0
    extraction_paper_id: Optional[str] = Field(None, foreign_key="papers.paper_id")

    # ===== ClaimEdge Fields (nullable) =====
    predicate: Optional[str] = None               # "TREATS", "CAUSES", etc.
    asserted_by: Optional[str] = Field(None, foreign_key="papers.paper_id")
    polarity: Optional[str] = None                # "supports", "refutes", "neutral"
    claim_confidence: Optional[float] = None      # Based on evidence strength

    # ===== EvidenceEdge Fields (nullable) =====
    evidence_type: Optional[str] = None           # "rct_evidence", "observational", etc.
    evidence_strength: Optional[float] = None     # 0.0-1.0
    evidence_paper_id: Optional[str] = Field(None, foreign_key="papers.paper_id")
    evidence_section: Optional[str] = None        # "results", "discussion", etc.
    evidence_text_span: Optional[str] = None      # The actual quote
    study_type: Optional[str] = None              # "rct", "observational"
    sample_size: Optional[int] = None

    # ===== Database Constraints =====
    __table_args__ = (
        # Ensure ExtractionEdge has required fields
        CheckConstraint(
            "(layer != 'extraction') OR (extractor_name IS NOT NULL AND extraction_confidence IS NOT NULL)",
            name="extraction_must_have_extractor"
        ),
        # Ensure ClaimEdge has required fields
        CheckConstraint(
            "(layer != 'claim') OR (predicate IS NOT NULL AND asserted_by IS NOT NULL AND polarity IS NOT NULL)",
            name="claim_must_have_predicate"
        ),
        # Ensure EvidenceEdge has required fields
        CheckConstraint(
            "(layer != 'evidence') OR (evidence_type IS NOT NULL AND evidence_strength IS NOT NULL)",
            name="evidence_must_have_type"
        ),
    )


# Helper functions for type-safe edge creation
def create_extraction_edge(**kwargs) -> Edge:
    """Create an extraction layer edge with required fields enforced"""
    return Edge(layer="extraction", **kwargs)


def create_claim_edge(**kwargs) -> Edge:
    """Create a claim layer edge with required fields enforced"""
    return Edge(layer="claim", **kwargs)


def create_evidence_edge(**kwargs) -> Edge:
    """Create an evidence layer edge with required fields enforced"""
    return Edge(layer="evidence", **kwargs)


# ============================================================================
# Setup and Sample Data
# ============================================================================

def create_db_and_tables():
    """Create SQLite database and tables"""
    engine = create_engine("sqlite:///medical_kg_inheritance.db", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


def populate_sample_data(session: Session):
    """Add example data showing all three edge layers"""

    print("\n" + "="*70)
    print("POPULATING SAMPLE DATA")
    print("="*70)

    # ===== Create Entities =====
    breast_cancer = Disease(
        id="UMLS:C0006142",
        name="Breast Cancer",
        umls_id="C0006142"
    )

    olaparib = Drug(
        id="RxNorm:1187832",
        name="Olaparib",
        rxnorm_id="1187832",
        drug_class="PARP inhibitor",
        mechanism="Inhibits poly ADP-ribose polymerase enzymes"
    )

    session.add(breast_cancer)
    session.add(olaparib)
    print("✓ Added entities: Olaparib, Breast Cancer")

    # ===== Create Papers =====
    paper1 = Paper(
        paper_id="PMC999888",
        title="Efficacy of Olaparib in BRCA-Mutated Breast Cancer: Phase III Trial",
        abstract="We conducted a randomized phase III trial of olaparib...",
        study_type=StudyType.RCT.value,
        sample_size=302,
        publication_date="2023-06-15",
        extraction_model="llama3.1:70b"
    )

    paper2 = Paper(
        paper_id="PMC888777",
        title="Meta-Analysis of PARP Inhibitors in Breast Cancer",
        abstract="We analyzed 15 studies of PARP inhibitors...",
        study_type=StudyType.META_ANALYSIS.value,
        sample_size=1205,
        publication_date="2024-01-10",
        extraction_model="llama3.1:70b"
    )

    session.add(paper1)
    session.add(paper2)
    print("✓ Added papers: PMC999888 (RCT), PMC888777 (Meta-analysis)")

    # ===== Layer 1: Extraction Edge =====
    # What the LLM extracted from the paper text
    extraction = create_extraction_edge(
        subject_id=olaparib.id,
        subject_name=olaparib.name,
        subject_type=EntityType.DRUG.value,
        object_id=breast_cancer.id,
        object_name=breast_cancer.name,
        object_type=EntityType.DISEASE.value,
        extractor_name="llama3.1:70b",
        extractor_provider="ollama",
        extraction_confidence=0.89,
        extraction_paper_id=paper1.paper_id
    )
    session.add(extraction)
    print("✓ Added ExtractionEdge: What LLM extracted from PMC999888")

    # ===== Layer 2: Claim Edge =====
    # What the paper asserts to be true
    claim = create_claim_edge(
        subject_id=olaparib.id,
        subject_name=olaparib.name,
        subject_type=EntityType.DRUG.value,
        object_id=breast_cancer.id,
        object_name=breast_cancer.name,
        object_type=EntityType.DISEASE.value,
        predicate=PredicateType.TREATS.value,
        asserted_by=paper1.paper_id,
        polarity=Polarity.SUPPORTS.value,
        claim_confidence=0.92
    )
    session.add(claim)
    print("✓ Added ClaimEdge: Paper asserts Olaparib TREATS Breast Cancer")

    # ===== Layer 3: Evidence Edge =====
    # Empirical evidence from the study
    evidence = create_evidence_edge(
        subject_id=olaparib.id,
        subject_name=olaparib.name,
        subject_type=EntityType.DRUG.value,
        object_id=breast_cancer.id,
        object_name=breast_cancer.name,
        object_type=EntityType.DISEASE.value,
        evidence_type="rct_evidence",
        evidence_strength=0.95,
        evidence_paper_id=paper1.paper_id,
        evidence_section="results",
        evidence_text_span="Olaparib significantly improved progression-free survival (HR=0.58, 95% CI: 0.43-0.80, p<0.001)",
        study_type=StudyType.RCT.value,
        sample_size=302
    )
    session.add(evidence)
    print("✓ Added EvidenceEdge: RCT results supporting the claim")

    # ===== Add Contradicting Evidence =====
    # Show how the system handles disagreement
    paper3 = Paper(
        paper_id="PMC777666",
        title="Limited Benefit of Olaparib in Unselected Breast Cancer",
        abstract="In patients without BRCA mutations, olaparib showed minimal benefit...",
        study_type=StudyType.OBSERVATIONAL.value,
        sample_size=150,
        publication_date="2023-09-20",
        extraction_model="llama3.1:70b"
    )
    session.add(paper3)

    contradicting_claim = create_claim_edge(
        subject_id=olaparib.id,
        subject_name=olaparib.name,
        subject_type=EntityType.DRUG.value,
        object_id=breast_cancer.id,
        object_name=breast_cancer.name,
        object_type=EntityType.DISEASE.value,
        predicate=PredicateType.TREATS.value,
        asserted_by=paper3.paper_id,
        polarity=Polarity.NEUTRAL.value,  # Weak/no effect
        claim_confidence=0.65
    )
    session.add(contradicting_claim)
    print("✓ Added contradicting ClaimEdge: Different paper shows limited benefit")

    session.commit()
    print("\n✓ All data committed successfully")


# ============================================================================
# Demo Queries
# ============================================================================

def demo_queries(session: Session):
    """Demonstrate the power of three-layer architecture"""

    print("\n" + "="*70)
    print("DEMO QUERIES - Three-Layer Edge Architecture")
    print("="*70)

    # ===== Query 1: Layer-Specific Query =====
    print("\n1. LAYER-SPECIFIC: What do papers CLAIM about Olaparib?")
    print("-" * 70)
    claims = session.exec(
        select(Edge)
        .where(Edge.layer == "claim")
        .where(Edge.subject_id == "RxNorm:1187832")
    ).all()

    for claim in claims:
        paper = session.get(Paper, claim.asserted_by)
        print(f"\n   Paper: {paper.title}")
        print(f"   Claim: {claim.subject_name} {claim.predicate} {claim.object_name}")
        print(f"   Polarity: {claim.polarity}")
        print(f"   Confidence: {claim.claim_confidence:.2f}")
        print(f"   Study type: {paper.study_type} (n={paper.sample_size})")

    # ===== Query 2: Cross-Layer Query =====
    print("\n\n2. CROSS-LAYER: Show me EVERYTHING about Olaparib → Breast Cancer")
    print("-" * 70)
    all_edges = session.exec(
        select(Edge)
        .where(Edge.subject_id == "RxNorm:1187832")
        .where(Edge.object_id == "UMLS:C0006142")
        .order_by(Edge.created_at)
    ).all()

    print(f"\n   Found {len(all_edges)} edges across all layers:")
    for edge in all_edges:
        print(f"\n   [{edge.layer.upper()}]")

        if edge.layer == "extraction":
            print(f"      Extractor: {edge.extractor_name}")
            print(f"      Confidence: {edge.extraction_confidence:.2f}")

        elif edge.layer == "claim":
            print(f"      Predicate: {edge.predicate}")
            print(f"      Polarity: {edge.polarity}")
            print(f"      Asserted by: {edge.asserted_by}")

        elif edge.layer == "evidence":
            print(f"      Evidence: {edge.evidence_text_span[:80]}...")
            print(f"      Strength: {edge.evidence_strength:.2f}")
            print(f"      Study: {edge.study_type} (n={edge.sample_size})")

    # ===== Query 3: Evidence Quality Filter =====
    print("\n\n3. HIGH-QUALITY EVIDENCE: Show me RCT evidence with strength > 0.9")
    print("-" * 70)
    strong_evidence = session.exec(
        select(Edge, Paper)
        .join(Paper, Edge.evidence_paper_id == Paper.paper_id)
        .where(Edge.layer == "evidence")
        .where(Edge.study_type == StudyType.RCT.value)
        .where(Edge.evidence_strength > 0.9)
    ).all()

    for evidence, paper in strong_evidence:
        print(f"\n   Paper: {paper.title}")
        print(f"   Finding: {evidence.subject_name} → {evidence.object_name}")
        print(f"   Evidence: \"{evidence.evidence_text_span}\"")
        print(f"   Strength: {evidence.evidence_strength:.2f}")
        print(f"   Study: {evidence.study_type}, n={evidence.sample_size}")

    # ===== Query 4: Contradiction Detection =====
    print("\n\n4. CONTRADICTION DETECTION: Find conflicting claims")
    print("-" * 70)

    # Group claims by subject-predicate-object, check for different polarities
    claims_by_relationship = {}
    all_claims = session.exec(
        select(Edge).where(Edge.layer == "claim")
    ).all()

    for claim in all_claims:
        key = (claim.subject_id, claim.predicate, claim.object_id)
        if key not in claims_by_relationship:
            claims_by_relationship[key] = []
        claims_by_relationship[key].append(claim)

    for key, claims_list in claims_by_relationship.items():
        polarities = {c.polarity for c in claims_list}
        if len(polarities) > 1:
            print(f"\n   ⚠️  CONTRADICTION DETECTED:")
            print(f"   Relationship: {claims_list[0].subject_name} → {claims_list[0].object_name}")
            print(f"   Different papers disagree:")
            for claim in claims_list:
                paper = session.get(Paper, claim.asserted_by)
                print(f"      • {paper.title[:60]}...")
                print(f"        Polarity: {claim.polarity}, Confidence: {claim.claim_confidence:.2f}")

    # ===== Query 5: Provenance Chain =====
    print("\n\n5. PROVENANCE CHAIN: Trace extraction → claim → evidence")
    print("-" * 70)

    # Get one of each type for the same relationship
    extraction_edge = session.exec(
        select(Edge)
        .where(Edge.layer == "extraction")
        .where(Edge.subject_id == "RxNorm:1187832")
    ).first()

    claim_edge = session.exec(
        select(Edge)
        .where(Edge.layer == "claim")
        .where(Edge.subject_id == "RxNorm:1187832")
        .where(Edge.polarity == Polarity.SUPPORTS.value)
    ).first()

    evidence_edge = session.exec(
        select(Edge)
        .where(Edge.layer == "evidence")
        .where(Edge.subject_id == "RxNorm:1187832")
    ).first()

    print(f"\n   Relationship: {claim_edge.subject_name} → {claim_edge.object_name}")
    print(f"\n   [1. EXTRACTION LAYER]")
    print(f"      Model: {extraction_edge.extractor_name}")
    print(f"      Found in paper: {extraction_edge.extraction_paper_id}")
    print(f"      Confidence: {extraction_edge.extraction_confidence:.2f}")

    print(f"\n   [2. CLAIM LAYER]")
    print(f"      Paper asserts: {claim_edge.predicate}")
    print(f"      Polarity: {claim_edge.polarity}")
    print(f"      Source: {claim_edge.asserted_by}")

    print(f"\n   [3. EVIDENCE LAYER]")
    print(f"      Study type: {evidence_edge.study_type} (n={evidence_edge.sample_size})")
    print(f"      Finding: \"{evidence_edge.evidence_text_span}\"")
    print(f"      Strength: {evidence_edge.evidence_strength:.2f}")

    # ===== Query 6: Layer-Based Filtering Demo =====
    print("\n\n6. LAYER-BASED FILTERING: Query by layer type")
    print("-" * 70)

    edges = session.exec(
        select(Edge)
        .where(Edge.subject_id == "RxNorm:1187832")
        .limit(3)
    ).all()

    print(f"\n   Retrieved {len(edges)} edges:")
    for edge in edges:
        print(f"      • Layer: {edge.layer}")
        print(f"        ID: {str(edge.id)[:8]}...")

        # Layer-specific field access
        if edge.layer == "claim":
            print(f"        Predicate: {edge.predicate} (claim-specific)")
        elif edge.layer == "evidence":
            print(f"        Study type: {edge.study_type} (evidence-specific)")


# ============================================================================
# Main Demo
# ============================================================================

def main():
    print("="*70)
    print("SQLModel Three-Layer Edge Architecture - Proof of Concept")
    print("="*70)
    print("\nDemonstrating:")
    print("  • Single-table design with layer discriminator")
    print("  • Three distinct edge layers (Extraction/Claim/Evidence)")
    print("  • Layer-based querying and filtering")
    print("  • Cross-layer queries")
    print("  • Contradiction detection")

    # Create database
    engine = create_db_and_tables()
    print("\n✓ Database created: medical_kg_inheritance.db")

    # Populate sample data
    with Session(engine) as session:
        populate_sample_data(session)

    # Run demo queries
    with Session(engine) as session:
        demo_queries(session)

    print("\n" + "="*70)
    print("Demo complete!")
    print("="*70)
    print("\nInspect the database:")
    print("  sqlite3 medical_kg_inheritance.db")
    print("  .schema edges")
    print("  SELECT layer, count(*) FROM edges GROUP BY layer;")
    print("\nKey takeaways:")
    print("  ✓ All edge types in ONE table (single-table design)")
    print("  ✓ Layer field acts as discriminator (extraction/claim/evidence)")
    print("  ✓ Cross-layer queries work naturally")
    print("  ✓ Database constraints enforce layer-specific requirements")
    print("  ✓ Helper functions provide type-safe edge creation")
    print("="*70)


if __name__ == "__main__":
    main()
