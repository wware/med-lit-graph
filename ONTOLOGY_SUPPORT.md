# Ontology-Based Scientific Methodology Support

This document describes the enhanced schema support for representing scientific evidence, hypotheses, study designs, and statistical methods using established biomedical ontologies.

## Overview

The schema now integrates several core scientific method ontologies to enable structured representation of:
- **Hypotheses** and their evolution (IAO, SEPIO)
- **Study designs** and experimental protocols (OBI)
- **Statistical methods** used in analysis (STATO)
- **Evidence types** and quality classification (ECO)
- **Evidence chains** linking assertions to supporting data (SEPIO)

## Ontologies Used

### 1. ECO - Evidence & Conclusion Ontology
- **URL**: http://www.evidenceontology.org/
- **Purpose**: Standardize evidence type classification
- **Example IDs**:
  - `ECO:0007673` - Randomized controlled trial evidence
  - `ECO:0007674` - Cohort study evidence
  - `ECO:0007675` - Case-control study evidence
  - `ECO:0007676` - Case report evidence

### 2. OBI - Ontology for Biomedical Investigations
- **URL**: http://obi-ontology.org/
- **Purpose**: Standardize study designs and experimental protocols
- **Example IDs**:
  - `OBI:0000008` - Randomized controlled trial
  - `OBI:0000070` - Assay
  - `OBI:0000011` - Planned process
  - `OBI:0000066` - Investigation

### 3. STATO - Statistics Ontology
- **URL**: http://stato-ontology.org/
- **Purpose**: Standardize statistical methods and concepts
- **Example IDs**:
  - `STATO:0000288` - Student's t-test
  - `STATO:0000039` - Study design
  - `STATO:0000376` - Kaplan-Meier estimator
  - `STATO:0000304` - Cox proportional hazards model

### 4. IAO - Information Artifact Ontology
- **URL**: https://github.com/information-artifact-ontology/IAO
- **Purpose**: Represent information entities like hypotheses
- **Example IDs**:
  - `IAO:0000018` - Hypothesis
  - `IAO:0000030` - Information content entity
  - `IAO:0000005` - Objective specification

### 5. SEPIO - Scientific Evidence and Provenance Information Ontology
- **URL**: https://github.com/monarch-initiative/SEPIO
- **Purpose**: Represent evidence chains and provenance
- **Example IDs**:
  - `SEPIO:0000001` - Assertion
  - `SEPIO:0000084` - Evidence line
  - `SEPIO:0000173` - Experimental evidence

## New Entity Types

### Hypothesis

Represents a scientific hypothesis tracked across the literature.

```python
from schema.entity import Hypothesis

hypothesis = Hypothesis(
    entity_id="HYPOTHESIS:amyloid_cascade_alzheimers",
    name="Amyloid Cascade Hypothesis",
    iao_id="IAO:0000018",  # IAO hypothesis ID
    sepio_id="SEPIO:0000001",  # SEPIO assertion ID
    proposed_by="PMC123456",
    proposed_date="1992",
    status="controversial",  # proposed, supported, controversial, refuted
    description="Beta-amyloid accumulation drives Alzheimer's disease pathology",
    predicts=["C0002395"]  # Alzheimer's disease
)
```

### StudyDesign

Represents a study design or experimental protocol.

```python
from schema.entity import StudyDesign

rct = StudyDesign(
    entity_id="OBI:0000008",
    name="Randomized Controlled Trial",
    obi_id="OBI:0000008",
    stato_id="STATO:0000402",
    design_type="interventional",
    evidence_level=1,  # 1=highest quality, 5=lowest
    description="Gold standard experimental design with random assignment"
)
```

### StatisticalMethod

Represents a statistical method used in analysis.

```python
from schema.entity import StatisticalMethod

ttest = StatisticalMethod(
    entity_id="STATO:0000288",
    name="Student's t-test",
    stato_id="STATO:0000288",
    method_type="hypothesis_test",
    description="Parametric test comparing means of two groups",
    assumptions=["Normal distribution", "Equal variances", "Independence"]
)
```

### EvidenceLine

Represents a structured evidence chain using SEPIO framework.

```python
from schema.entity import EvidenceLine

evidence_line = EvidenceLine(
    entity_id="EVIDENCE_LINE:olaparib_brca_001",
    name="Clinical evidence for Olaparib in BRCA-mutated breast cancer",
    sepio_type="SEPIO:0000084",  # Evidence line
    eco_type="ECO:0007673",  # RCT evidence
    assertion_id="ASSERTION:olaparib_brca",
    supports=["HYPOTHESIS:parp_inhibitor_synthetic_lethality"],
    evidence_items=["PMC999888", "PMC888777"],
    strength="strong",  # strong, moderate, weak
    provenance="Meta-analysis of 3 RCTs"
)
```

## Enhanced Evidence Class

The `Evidence` class now includes ontology references for standardized classification:

```python
from schema.entity import Evidence

evidence = Evidence(
    paper_id="PMC999888",
    confidence=0.92,
    section_type="results",
    paragraph_idx=8,
    text_span="Olaparib showed significant efficacy in BRCA-mutated breast cancer",
    study_type="rct",
    sample_size=302,
    # Ontology references
    eco_type="ECO:0007673",  # RCT evidence
    obi_study_design="OBI:0000008",  # Randomized controlled trial
    stato_methods=["STATO:0000288", "STATO:0000376"]  # t-test, Kaplan-Meier
)
```

## New Relationship Types

### PREDICTS

Hypothesis predicting an observable outcome.

```python
from schema.relationship import Predicts, RelationType

predicts = Predicts(
    subject_id="HYPOTHESIS:amyloid_cascade",
    predicate=RelationType.PREDICTS,
    object_id="C0002395",  # Alzheimer's disease
    prediction_type="positive",  # positive, negative, conditional
    testable=True,
    conditions="In presence of beta-amyloid plaques",
    source_papers=["PMC123456"]
)
```

### REFUTES

Evidence refuting a hypothesis.

```python
from schema.relationship import Refutes, RelationType

refutes = Refutes(
    subject_id="PMC999888",
    predicate=RelationType.REFUTES,
    object_id="HYPOTHESIS:amyloid_cascade",
    refutation_strength="moderate",  # strong, moderate, weak
    alternative_explanation="Tau pathology may be primary driver",
    limitations="Small sample size, limited follow-up",
    source_papers=["PMC999888"],
    confidence=0.75
)
```

### TESTED_BY

Hypothesis being tested by a study.

```python
from schema.relationship import TestedBy, RelationType

tested = TestedBy(
    subject_id="HYPOTHESIS:parp_inhibitor_synthetic_lethality",
    predicate=RelationType.TESTED_BY,
    object_id="PMC999888",
    test_outcome="supported",  # supported, refuted, inconclusive
    methodology="randomized controlled trial",
    study_design_id="OBI:0000008",
    source_papers=["PMC999888"],
    confidence=0.90
)
```

### GENERATES

Study generating evidence.

```python
from schema.relationship import Generates, RelationType

generates = Generates(
    subject_id="PMC999888",
    predicate=RelationType.GENERATES,
    object_id="EVIDENCE_LINE:olaparib_brca_001",
    evidence_type="experimental",
    eco_type="ECO:0007673",  # RCT evidence
    quality_score=0.92,
    source_papers=["PMC999888"]
)
```

## Complete Workflow Example

Here's a complete example of tracking a hypothesis through testing and validation:

```python
from schema.entity import Hypothesis, StudyDesign, Evidence, EvidenceLine
from schema.relationship import Predicts, TestedBy, Generates

# 1. Define the hypothesis
hypothesis = Hypothesis(
    entity_id="HYPOTHESIS:parp_inhibitor_brca",
    name="PARP Inhibitor Synthetic Lethality in BRCA-Mutated Cancers",
    iao_id="IAO:0000018",
    sepio_id="SEPIO:0000001",
    proposed_by="PMC456789",
    proposed_date="2005",
    status="supported",
    description="PARP inhibitors exploit synthetic lethality in BRCA1/2-deficient cells",
    predicts=["C0006142"]  # Breast cancer treatment response
)

# 2. Hypothesis predicts treatment response
predicts_rel = Predicts(
    subject_id="HYPOTHESIS:parp_inhibitor_brca",
    object_id="C0006142",  # Breast cancer
    prediction_type="positive",
    testable=True,
    source_papers=["PMC456789"]
)

# 3. Hypothesis tested by clinical trial
tested_by_rel = TestedBy(
    subject_id="HYPOTHESIS:parp_inhibitor_brca",
    object_id="PMC999888",
    test_outcome="supported",
    methodology="randomized controlled trial",
    study_design_id="OBI:0000008",
    source_papers=["PMC999888"],
    confidence=0.92
)

# 4. Clinical trial generates evidence
evidence = Evidence(
    paper_id="PMC999888",
    confidence=0.92,
    section_type="results",
    study_type="rct",
    sample_size=302,
    eco_type="ECO:0007673",
    obi_study_design="OBI:0000008",
    stato_methods=["STATO:0000288"]
)

generates_rel = Generates(
    subject_id="PMC999888",
    object_id="EVIDENCE_LINE:olaparib_brca_001",
    evidence_type="experimental",
    eco_type="ECO:0007673",
    quality_score=0.92,
    source_papers=["PMC999888"],
    evidence=[evidence]
)

# 5. Evidence line supports hypothesis
evidence_line = EvidenceLine(
    entity_id="EVIDENCE_LINE:olaparib_brca_001",
    name="Clinical evidence for Olaparib in BRCA-mutated breast cancer",
    sepio_type="SEPIO:0000084",
    eco_type="ECO:0007673",
    assertion_id="ASSERTION:olaparib_brca",
    supports=["HYPOTHESIS:parp_inhibitor_brca"],
    evidence_items=["PMC999888", "PMC888777"],
    strength="strong"
)
```

## Evidence Quality Weighting

Map ECO evidence types to confidence weights for automatic quality scoring:

```python
ECO_WEIGHTS = {
    "ECO:0007673": 1.0,    # RCT evidence
    "ECO:0007674": 0.8,    # Cohort study
    "ECO:0007675": 0.6,    # Case-control study
    "ECO:0007676": 0.4,    # Case report
    "ECO:0000033": 0.3,    # Author statement
}

def calculate_evidence_confidence(evidence: Evidence) -> float:
    """Calculate confidence score based on ECO evidence type"""
    if evidence.eco_type and evidence.eco_type in ECO_WEIGHTS:
        return ECO_WEIGHTS[evidence.eco_type]
    return 0.5  # Default
```

## Query Examples

### Find all hypotheses with supporting RCT evidence

```python
from client.python.client import QueryBuilder

query = (QueryBuilder()
    .find_nodes("hypothesis")
    .with_edge("tested_by")
    .filter_edge(
        field="edge.evidence.eco_type",
        operator="eq",
        value="ECO:0007673"  # RCT evidence
    )
    .filter_edge(
        field="edge.test_outcome",
        operator="eq",
        value="supported"
    )
    .build())
```

### Compare study designs by evidence quality

```python
query = {
    "find": "nodes",
    "node_pattern": {"node_type": "study_design"},
    "aggregate": {
        "group_by": ["study_design.name"],
        "aggregations": {
            "evidence_count": ["count", "rel.evidence.paper_id"],
            "avg_confidence": ["avg", "rel.confidence"]
        }
    },
    "order_by": [{"field": "avg_confidence", "direction": "desc"}]
}
```

### Find statistical methods used in RCTs

```python
query = {
    "find": "nodes",
    "node_pattern": {"node_type": "statistical_method"},
    "filters": [{
        "field": "usage_in.evidence.eco_type",
        "operator": "eq",
        "value": "ECO:0007673"
    }],
    "aggregate": {
        "group_by": ["statistical_method.name"],
        "aggregations": {"usage_count": ["count", "usage_in.paper_id"]}
    }
}
```

## References

- **OBI**: http://obi-ontology.org/
- **STATO**: http://stato-ontology.org/
- **ECO**: http://www.evidenceontology.org/
- **IAO**: https://github.com/information-artifact-ontology/IAO
- **SEPIO**: https://github.com/monarch-initiative/SEPIO
- **Ontology Lookup Service**: https://www.ebi.ac.uk/ols/index
- **BioPortal**: https://bioportal.bioontology.org/
