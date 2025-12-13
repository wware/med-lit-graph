# tests/mini_server/synthetic_data.py
"""
Synthetic medical knowledge graph data for testing.

Adapted from the populate_sample_data.py script but without
database dependencies - just pure Python data structures.
"""

from typing import Dict, List
from datetime import datetime

def generate_entities() -> Dict[str, Dict]:
    """Generate synthetic medical entities."""
    entities = {}
    
    # Disease: Breast Cancer
    entities["UMLS:C0006142"] = {
        "id": "UMLS:C0006142",
        "type": "disease",
        "name": "Breast Cancer",
        "canonical_id": "UMLS:C0006142",
        "mentions": 1523,
        "aliases": ["mammary carcinoma", "breast malignancy"],
        "description": "A malignant neoplasm arising from the breast tissue"
    }
    
    # Drug: Olaparib
    entities["RxNorm:1187832"] = {
        "id": "RxNorm:1187832",
        "type": "drug",
        "name": "Olaparib",
        "canonical_id": "RxNorm:1187832",
        "mentions": 342,
        "aliases": ["Lynparza"],
        "description": "PARP inhibitor used in cancer treatment"
    }
    
    # Drug: Tamoxifen (for Example 1)
    entities["RxNorm:10324"] = {
        "id": "RxNorm:10324",
        "type": "drug",
        "name": "tamoxifen",
        "canonical_id": "RxNorm:10324",
        "mentions": 1892,
        "aliases": ["Nolvadex"],
        "description": "Selective estrogen receptor modulator for breast cancer"
    }
    
    # Drug: Trastuzumab (for Example 1)
    entities["RxNorm:224905"] = {
        "id": "RxNorm:224905",
        "type": "drug",
        "name": "trastuzumab",
        "canonical_id": "RxNorm:224905",
        "mentions": 1456,
        "aliases": ["Herceptin"],
        "description": "Monoclonal antibody for HER2-positive breast cancer"
    }
    
    # Drug: Metformin
    entities["RxNorm:860975"] = {
        "id": "RxNorm:860975",
        "type": "drug",
        "name": "Metformin",
        "canonical_id": "RxNorm:860975",
        "mentions": 2847,
        "aliases": ["Glucophage"],
        "description": "An oral antihyperglycemic agent"
    }
    
    # Protein: AMPK
    entities["NCBI:Gene:5562"] = {
        "id": "NCBI:Gene:5562",
        "type": "protein",
        "name": "AMPK",
        "canonical_id": "NCBI:Gene:5562",
        "mentions": 1205,
        "aliases": ["AMP-activated protein kinase", "5'-AMP-activated protein kinase"],
        "description": "A protein that plays a key role in cellular energy homeostasis"
    }
    
    # Biomarker: HbA1c
    entities["LOINC:4548-4"] = {
        "id": "LOINC:4548-4",
        "type": "biomarker",
        "name": "Glycated Hemoglobin",
        "canonical_id": "LOINC:4548-4",
        "mentions": 892,
        "aliases": ["HbA1c", "A1c"],
        "description": "A form of hemoglobin that is chemically linked to a sugar"
    }
    
    # Add more entities for richer queries...
    # Disease: Type 2 Diabetes
    entities["UMLS:C0011860"] = {
        "id": "UMLS:C0011860",
        "type": "disease",
        "name": "Type 2 Diabetes",
        "canonical_id": "UMLS:C0011860",
        "mentions": 3421,
        "aliases": ["diabetes mellitus type 2", "T2DM"],
        "description": "A metabolic disorder characterized by high blood sugar"
    }
    
    # Drug: Aspirin
    entities["RxNorm:1191"] = {
        "id": "RxNorm:1191",
        "type": "drug",
        "name": "Aspirin",
        "canonical_id": "RxNorm:1191",
        "mentions": 4123,
        "aliases": ["acetylsalicylic acid", "ASA"],
        "description": "A medication used to reduce pain, fever, or inflammation"
    }
    
    # Disease: Myocardial Infarction
    entities["UMLS:C0027051"] = {
        "id": "UMLS:C0027051",
        "type": "disease",
        "name": "Myocardial Infarction",
        "canonical_id": "UMLS:C0027051",
        "mentions": 2891,
        "aliases": ["heart attack", "MI"],
        "description": "Death of heart muscle due to interrupted blood supply"
    }
    
    return entities


def generate_relationships() -> List[Dict]:
    """Generate synthetic relationships with full provenance."""
    relationships = []
    
    # Tamoxifen TREATS Breast Cancer (for Example 1)
    # Expected: paper_count=234, avg_confidence=0.89, total_evidence=456
    relationships.append({
        "id": "rel_tam_bc",
        "subject_id": "RxNorm:10324",  # Tamoxifen
        "predicate": "TREATS",
        "object_id": "UMLS:C0006142",  # Breast Cancer
        "confidence": 0.89,
        "evidence_count": 456,  # total_evidence
        "papers": ["PMC" + str(i) for i in range(1000, 1234)],  # 234 papers
        "metadata": {
            "response_rate": 0.75,
            "study_type": "rct",
            "sample_size": 1250,
            "phase": "III"
        }
    })
    
    # Trastuzumab TREATS Breast Cancer (for Example 1)
    # Expected: paper_count=189, avg_confidence=0.92, total_evidence=312
    relationships.append({
        "id": "rel_tras_bc",
        "subject_id": "RxNorm:224905",  # Trastuzumab
        "predicate": "TREATS",
        "object_id": "UMLS:C0006142",  # Breast Cancer
        "confidence": 0.92,
        "evidence_count": 312,  # total_evidence
        "papers": ["PMC" + str(i) for i in range(2000, 2189)],  # 189 papers
        "metadata": {
            "response_rate": 0.82,
            "study_type": "rct",
            "sample_size": 980,
            "phase": "III",
            "her2_positive": True
        }
    })
    
    # Olaparib TREATS Breast Cancer
    relationships.append({
        "id": "rel_001",
        "subject_id": "RxNorm:1187832",  # Olaparib
        "predicate": "TREATS",
        "object_id": "UMLS:C0006142",  # Breast Cancer
        "confidence": 0.92,
        "evidence_count": 1,
        "papers": ["PMC123456"],
        "metadata": {
            "response_rate": 0.599,
            "study_type": "rct",
            "sample_size": 302,
            "phase": "III"
        }
    })
    
    # Metformin ACTIVATES AMPK
    relationships.append({
        "id": "rel_002",
        "subject_id": "RxNorm:860975",  # Metformin
        "predicate": "ACTIVATES",
        "object_id": "NCBI:Gene:5562",  # AMPK
        "confidence": 0.90,
        "evidence_count": 1,
        "papers": ["PMC234567"],
        "metadata": {
            "study_type": "cohort",
            "sample_size": 450
        }
    })
    
    # AMPK DOWNREGULATES HbA1c
    relationships.append({
        "id": "rel_003",
        "subject_id": "NCBI:Gene:5562",  # AMPK
        "predicate": "DOWNREGULATES",
        "object_id": "LOINC:4548-4",  # HbA1c
        "confidence": 0.88,
        "evidence_count": 1,
        "papers": ["PMC234567"],
        "metadata": {
            "study_type": "rct",
            "sample_size": 320
        }
    })
    
    # Metformin TREATS Type 2 Diabetes
    relationships.append({
        "id": "rel_004",
        "subject_id": "RxNorm:860975",  # Metformin
        "predicate": "TREATS",
        "object_id": "UMLS:C0011860",  # Type 2 Diabetes
        "confidence": 0.95,
        "evidence_count": 3,
        "papers": ["PMC234567", "PMC345678", "PMC456789"],
        "metadata": {
            "efficacy": 0.78,
            "adverse_events": ["GI upset", "lactic acidosis (rare)"]
        }
    })
    
    # Aspirin PREVENTS Myocardial Infarction
    relationships.append({
        "id": "rel_005",
        "subject_id": "RxNorm:1191",  # Aspirin
        "predicate": "PREVENTS",
        "object_id": "UMLS:C0027051",  # MI
        "confidence": 0.82,
        "evidence_count": 2,
        "papers": ["PMC567890", "PMC678901"],
        "metadata": {
            "risk_reduction": 0.25,
            "study_type": "meta_analysis"
        }
    })
    
    return relationships


def generate_papers() -> Dict[str, Dict]:
    """Generate synthetic paper metadata."""
    papers = {}
    
    papers["PMC123456"] = {
        "paper_id": "PMC123456",
        "title": "Efficacy of Olaparib in BRCA-Mutated Breast Cancer",
        "authors": ["Robson M", "Im SA", "Senkus E", "Xu B", "Domchek SM"],
        "abstract": "This randomized controlled trial demonstrates the efficacy of olaparib in treating BRCA-mutated breast cancer patients. The response rate was 59.9% compared to standard therapy.",
        "publication_date": "2017-08-10",
        "journal": "New England Journal of Medicine",
        "entity_count": 2,
        "relationship_count": 1
    }
    
    papers["PMC234567"] = {
        "paper_id": "PMC234567",
        "title": "Metformin Activation of AMPK and Effects on Glycemic Control",
        "authors": ["Zhou G", "Myers R", "Li Y", "Chen Y", "Shen X"],
        "abstract": "This study investigates the molecular mechanism by which metformin activates AMPK and subsequently improves glycemic control through downregulation of hepatic glucose production.",
        "publication_date": "2018-03-15",
        "journal": "Journal of Clinical Investigation",
        "entity_count": 3,
        "relationship_count": 2
    }
    
    papers["PMC345678"] = {
        "paper_id": "PMC345678",
        "title": "Long-term Metformin Use in Type 2 Diabetes: A Cohort Study",
        "authors": ["Turner RC", "Holman RR", "Cull CA", "Stratton IM"],
        "abstract": "Long-term follow-up of metformin therapy in type 2 diabetes demonstrates sustained glycemic control and reduced cardiovascular events.",
        "publication_date": "2019-06-22",
        "journal": "Diabetes Care",
        "entity_count": 2,
        "relationship_count": 1
    }
    
    papers["PMC567890"] = {
        "paper_id": "PMC567890",
        "title": "Aspirin for Primary Prevention of Cardiovascular Events",
        "authors": ["Ridker PM", "Cook NR", "Lee IM", "Gordon D"],
        "abstract": "Meta-analysis of aspirin use for primary prevention of myocardial infarction shows 25% risk reduction in high-risk patients.",
        "publication_date": "2020-01-10",
        "journal": "Circulation",
        "entity_count": 2,
        "relationship_count": 1
    }
    
    return papers


def load_all_synthetic_data():
    """Load all synthetic data into structured dictionaries."""
    return {
        "entities": generate_entities(),
        "relationships": generate_relationships(),
        "papers": generate_papers()
    }
