# JSON Output Format

## Overview

Each paper produces ONE JSON file: `output/papers/{pmc_id}.json`

This JSON contains all extraction results for the paper across all pipeline stages.

---

## Complete Schema

```json
{
  "paper_id": "PMC322947",
  "metadata": {
    "pmid": "3003749",
    "doi": "10.1073/pnas.83.3.772",
    "title": "Detection of lymphocytes expressing human T-lymphotropic virus type III in lymph nodes and peripheral blood from infected individuals by in situ hybridization",
    "journal": "Proc Natl Acad Sci U S A",
    "pub_date": "1986-02-01",
    "volume": "83",
    "issue": "3",
    "pages": "772-776",
    "authors": [
      {
        "name": "Harper ME",
        "affiliation": "Laboratory of Tumor Cell Biology, National Cancer Institute, Bethesda, MD"
      },
      {
        "name": "Marselle LM",
        "affiliation": "Laboratory of Tumor Cell Biology, National Cancer Institute, Bethesda, MD"
      },
      {
        "name": "Gallo RC",
        "affiliation": "Laboratory of Tumor Cell Biology, National Cancer Institute, Bethesda, MD"
      },
      {
        "name": "Wong-Staal F",
        "affiliation": "Laboratory of Tumor Cell Biology, National Cancer Institute, Bethesda, MD"
      }
    ],
    "keywords": [
      "HTLV-III",
      "AIDS",
      "in situ hybridization",
      "lymphocytes"
    ],
    "abstract": "By using in situ hybridization methodology with a 35S-labeled RNA probe..."
  },
  
  "sections": [
    {
      "section_id": "PMC322947_abstract",
      "section_type": "abstract",
      "section_order": 0,
      "title": null,
      "paragraphs": [
        {
          "paragraph_id": "PMC322947_abstract_p1",
          "paragraph_order": 0,
          "text": "By using in situ hybridization methodology with a 35S-labeled RNA probe, we have examined lymph nodes and peripheral blood cells from 9 patients with acquired immunodeficiency syndrome (AIDS) or AIDS-related complex for the presence of cells expressing human T-lymphotropic virus type III (HTLV-III) RNA sequences. HTLV-III-expressing cells were detected in 6 of 7 lymph nodes examined. These cells were present as dispersed single cells, and silver grains were localized to the cytoplasm of the positive cells.",
          "start_char": 0,
          "end_char": 523,
          "embedding": [0.023, 0.045, 0.012, ...],  // 768 dimensions
          "embedding_model": "sentence-transformers/all-mpnet-base-v2"
        }
      ]
    },
    {
      "section_id": "PMC322947_intro",
      "section_type": "introduction",
      "section_order": 1,
      "title": "Introduction",
      "paragraphs": [...]
    },
    {
      "section_id": "PMC322947_methods",
      "section_type": "methods",
      "section_order": 2,
      "title": "Materials and Methods",
      "paragraphs": [...]
    },
    {
      "section_id": "PMC322947_results",
      "section_type": "results",
      "section_order": 3,
      "title": "Results",
      "paragraphs": [
        {
          "paragraph_id": "PMC322947_results_p2",
          "paragraph_order": 1,
          "text": "HTLV-III-infected cells expressing viral RNA were detected in 6 of 7 lymph nodes examined by in situ hybridization.",
          "start_char": 1245,
          "end_char": 1362,
          "embedding": [0.034, 0.067, ...],
          "embedding_model": "sentence-transformers/all-mpnet-base-v2"
        }
      ]
    },
    {
      "section_id": "PMC322947_discussion",
      "section_type": "discussion",
      "section_order": 4,
      "title": "Discussion",
      "paragraphs": [...]
    }
  ],
  
  "entities": [
    {
      "entity_id": 42,
      "canonical_id": 15,
      "text": "HTLV-III",
      "type": "Disease",
      "confidence": 0.98,
      "paragraph_id": "PMC322947_abstract_p1",
      "char_start": 292,
      "char_end": 300,
      "embedding": [0.123, 0.234, 0.345, ...],
      "embedding_model": "sentence-transformers/all-mpnet-base-v2"
    },
    {
      "entity_id": 43,
      "canonical_id": 2,
      "text": "AIDS",
      "type": "Disease",
      "confidence": 0.99,
      "paragraph_id": "PMC322947_abstract_p1",
      "char_start": 185,
      "char_end": 189,
      "embedding": [0.234, 0.456, 0.678, ...],
      "embedding_model": "sentence-transformers/all-mpnet-base-v2"
    },
    {
      "entity_id": 56,
      "canonical_id": 56,
      "text": "lymphocytes",
      "type": "Cell",
      "confidence": 0.95,
      "paragraph_id": "PMC322947_abstract_p1",
      "char_start": 67,
      "char_end": 78,
      "embedding": [0.345, 0.567, ...],
      "embedding_model": "sentence-transformers/all-mpnet-base-v2"
    }
  ],
  
  "claims": [
    {
      "claim_id": "PMC322947_claim_1",
      "subject_entity": 42,
      "subject_canonical_id": 15,
      "subject_text": "HTLV-III",
      "predicate": "INFECTS",
      "object_entity": 56,
      "object_canonical_id": 56,
      "object_text": "lymphocytes",
      "paragraph_id": "PMC322947_results_p2",
      "section_id": "PMC322947_results",
      "extracted_text": "HTLV-III-infected cells expressing viral RNA were detected in 6 of 7 lymph nodes",
      "confidence": 0.92,
      "evidence_type": "molecular",
      "embedding": [0.456, 0.678, ...],
      "embedding_model": "sentence-transformers/all-mpnet-base-v2"
    },
    {
      "claim_id": "PMC322947_claim_2",
      "subject_entity": 42,
      "subject_canonical_id": 15,
      "subject_text": "HTLV-III",
      "predicate": "DETECTED_IN",
      "object_entity": 57,
      "object_canonical_id": 57,
      "object_text": "lymph nodes",
      "paragraph_id": "PMC322947_abstract_p1",
      "section_id": "PMC322947_abstract",
      "extracted_text": "HTLV-III-expressing cells were detected in 6 of 7 lymph nodes examined",
      "confidence": 0.95,
      "evidence_type": "molecular",
      "embedding": [0.567, 0.789, ...],
      "embedding_model": "sentence-transformers/all-mpnet-base-v2"
    }
  ],
  
  "evidence": [
    {
      "evidence_id": "PMC322947_ev_1",
      "supports_claim": "PMC322947_claim_1",
      "supports": true,
      "strength": "high",
      "type": "in_situ_hybridization",
      "paragraph_id": "PMC322947_methods_p5",
      "section_id": "PMC322947_methods",
      "details": {
        "method": "in situ hybridization",
        "probe": "35S-labeled RNA probe",
        "detection_method": "autoradiography",
        "target": "HTLV-III RNA sequences"
      },
      "metrics": {
        "positive_samples": 6,
        "total_samples": 7,
        "detection_rate": 0.857,
        "description": "HTLV-III-expressing cells detected in 6 of 7 lymph nodes"
      }
    },
    {
      "evidence_id": "PMC322947_ev_2",
      "supports_claim": "PMC322947_claim_1",
      "supports": true,
      "strength": "high",
      "type": "cellular_localization",
      "paragraph_id": "PMC322947_results_p3",
      "section_id": "PMC322947_results",
      "details": {
        "observation": "cytoplasmic localization",
        "cell_distribution": "dispersed single cells"
      },
      "metrics": {
        "description": "Silver grains localized to cytoplasm of positive cells"
      }
    }
  ],
  
  "citations": [
    {
      "cited_reference": "PMID:6328312",
      "cited_paper_id": null,
      "context": "As shown by Gallo et al., HTLV-III is the etiologic agent of AIDS",
      "paragraph_id": "PMC322947_intro_p2",
      "char_start": 45,
      "char_end": 112
    },
    {
      "cited_reference": "DOI:10.1126/science.6096202",
      "cited_paper_id": null,
      "context": "Previous studies demonstrated viral antigens in tissue specimens",
      "paragraph_id": "PMC322947_intro_p3",
      "char_start": 23,
      "char_end": 89
    }
  ],
  
  "extraction_metadata": {
    "pipeline_version": "0.1.0",
    "extracted_at": "2024-12-17T19:30:00Z",
    "stages_completed": [
      "extract_entities",
      "extract_provenance",
      "generate_embeddings",
      "extract_claims",
      "aggregate_evidence"
    ],
    "models": {
      "ner": "ugaray96/biobert_ncbi_disease_ner",
      "embeddings": "sentence-transformers/all-mpnet-base-v2",
      "claim_extraction": "rule_based_v1"
    },
    "statistics": {
      "total_entities": 15,
      "total_claims": 8,
      "total_evidence": 12,
      "total_paragraphs": 47,
      "total_sections": 5
    }
  }
}
```

---

## Field Descriptions

### Metadata Section

- **paper_id**: PMC identifier (primary key)
- **pmid**: PubMed ID (if available)
- **doi**: Digital Object Identifier
- **pub_date**: Publication date (ISO 8601 format)
- **authors**: Array of author objects with name and affiliation
- **keywords**: Extracted from paper or inferred

### Sections

- **section_id**: Unique identifier (paper_id + section_type)
- **section_type**: One of: abstract, introduction, methods, results, discussion, conclusion
- **section_order**: Position in paper (0-indexed)
- **paragraphs**: Array of paragraph objects

### Paragraphs

- **paragraph_id**: Unique identifier (section_id + p + order)
- **text**: Full paragraph text
- **start_char/end_char**: Character offsets in full document
- **embedding**: 768-dimensional vector (list of floats)

### Entities

- **entity_id**: Local ID within this paper
- **canonical_id**: Global canonical entity ID (from entities.db)
- **text**: Entity mention as it appears in text
- **type**: Entity type (Disease, Gene, Chemical, etc.)
- **confidence**: NER model confidence score (0-1)
- **char_start/end**: Character offsets within paragraph
- **embedding**: Entity text embedding

### Claims

- **claim_id**: Unique identifier (paper_id + claim_ + sequence)
- **subject_entity/object_entity**: Local entity IDs
- **subject_canonical_id/object_canonical_id**: Global canonical IDs
- **predicate**: Relationship type (CAUSES, INFECTS, etc.)
- **extracted_text**: Sentence containing the claim
- **confidence**: Extraction confidence
- **evidence_type**: Type of evidence supporting this claim
- **embedding**: Claim text embedding

### Evidence

- **evidence_id**: Unique identifier
- **supports_claim**: Claim ID this evidence relates to
- **supports**: Boolean - true if supports, false if refutes
- **strength**: high/medium/low
- **type**: Method type (in_situ_hybridization, PCR, cohort_study, etc.)
- **details**: Method-specific information (JSON object)
- **metrics**: Quantitative measurements (sample size, p-value, etc.)

### Citations

- **cited_reference**: PMID, DOI, or freetext reference
- **context**: Text surrounding the citation
- **paragraph_id**: Where citation appears

---

## Usage Examples

### Load and inspect a paper

```python
import json

with open('output/papers/PMC322947.json', 'r') as f:
    paper = json.load(f)

print(f"Title: {paper['metadata']['title']}")
print(f"Authors: {', '.join(a['name'] for a in paper['metadata']['authors'])}")
print(f"Entities: {len(paper['entities'])}")
print(f"Claims: {len(paper['claims'])}")
```

### Find all CAUSES claims

```python
causes_claims = [
    c for c in paper['claims']
    if c['predicate'] == 'CAUSES'
]

for claim in causes_claims:
    print(f"{claim['subject_text']} → {claim['object_text']}")
    print(f"  Evidence: {claim['extracted_text']}")
    print(f"  Confidence: {claim['confidence']}")
```

### Extract entity embeddings for clustering

```python
import numpy as np

entity_embeddings = {
    e['canonical_id']: np.array(e['embedding'])
    for e in paper['entities']
}

# Compute similarity between HIV and HTLV-III
from sklearn.metrics.pairwise import cosine_similarity
hiv_emb = entity_embeddings[15]
htlv_emb = entity_embeddings[15]  # Same canonical_id if clustered
similarity = cosine_similarity([hiv_emb], [htlv_emb])[0][0]
```

### Find high-quality evidence

```python
high_quality_evidence = [
    ev for ev in paper['evidence']
    if ev['strength'] == 'high' and ev['supports']
]

for ev in high_quality_evidence:
    claim = next(c for c in paper['claims'] if c['claim_id'] == ev['supports_claim'])
    print(f"Claim: {claim['extracted_text']}")
    print(f"Method: {ev['type']}")
    print(f"Metrics: {ev['metrics']}")
```

---

## Benefits of JSON Format

1. **Self-contained**: Each paper is independent
2. **Version control**: Git diff shows extraction changes
3. **Portable**: Import to any database (Neo4j, AGE, etc.)
4. **Inspectable**: Human-readable, easy to debug
5. **Incremental**: Process papers one at a time
6. **Testable**: Validate against JSON schema
7. **Extensible**: Add new fields without breaking existing code

---

## JSON Schema Validation

```python
from jsonschema import validate

schema = {
    "type": "object",
    "required": ["paper_id", "metadata", "sections", "entities"],
    "properties": {
        "paper_id": {"type": "string", "pattern": "^PMC[0-9]+$"},
        "metadata": {
            "type": "object",
            "required": ["title", "pub_date", "authors"]
        },
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["entity_id", "canonical_id", "text", "type"]
            }
        }
    }
}

# Validate
with open('output/papers/PMC322947.json') as f:
    paper = json.load(f)
    validate(instance=paper, schema=schema)
```
