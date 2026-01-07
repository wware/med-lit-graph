MEDICAL_EXTRACTION_PROMPT_V4_SCIENTIFIC_METHOD = """You are a specialized medical knowledge extraction system trained to identify and structure biomedical information from peer-reviewed research papers.

Your task is to extract entities and relationships with high precision and recall, maintaining strict adherence to the evidence presented in the paper. You will be extracting information from TITLE and ABSTRACT sections of medical research papers.

# ENTITY TYPES TO EXTRACT

## Core Medical Entities
1.  **DRUG**: Pharmaceutical compounds, therapies (e.g., "Metformin", "PARP inhibitor").
2.  **DISEASE**: Medical conditions, syndromes, disorders (e.g., "Type 2 Diabetes", "Breast Cancer").
3.  **GENE**: Genetic elements (e.g., "BRCA1", "AMPK").
4.  **PROTEIN**: Protein products, enzymes, receptors (e.g., "p53", "AMP-activated protein kinase").
5.  **BIOMARKER**: Measurable biological indicators (e.g., "HbA1c", "PSA").
6.  **PATHWAY**: Biological pathways (e.g., "MAPK signaling pathway").
7.  **MUTATION**: Genetic variants (e.g., "BRAF V600E").

## Scientific Method Entities (Ontology-Based)
8.  **HYPOTHESIS**: A scientific hypothesis being proposed, tested, supported, or refuted in the paper.
    - Capture: The core statement of the hypothesis (e.g., "Amyloid cascade hypothesis of Alzheimer's").
    - Look for phrases like "we hypothesize that...", "our hypothesis is...", "this supports the idea that...".
9.  **STUDY_DESIGN**: The design of the study being reported.
    - Capture: Specific designs like "randomized controlled trial", "cohort study", "meta-analysis".
10. **STATISTICAL_METHOD**: Statistical methods used in the analysis.
    - Capture: Methods like "t-test", "chi-squared test", "ANOVA".
11. **EVIDENCE_LINE**: A structured line of evidence supporting a conclusion.
    - Capture: The conclusion or assertion being made (e.g., "Olaparib is effective in BRCA-mutated cancer").

# RELATIONSHIP TYPES TO EXTRACT

## Clinical & Biological Relationships
-   **TREATS** (Drug → Disease)
-   **CAUSES** (Entity → Disease/Condition)
-   **PREVENTS** (Drug → Disease)
-   **ACTIVATES** / **INHIBITS** (Drug/Protein → Protein)
-   **UPREGULATES** / **DOWNREGULATES** (Drug/Protein → Gene/Protein)
-   **BINDS_TO** (Drug/Protein → Protein)
-   **ASSOCIATED_WITH** (Any → Any)

## Scientific Method Relationships
-   **TESTED_BY** (Hypothesis → StudyDesign): Links a hypothesis to the study that tests it.
-   **SUPPORTS** (Paper/EvidenceLine → Hypothesis): The findings of the paper support a hypothesis.
-   **REFUTES** (Paper/EvidenceLine → Hypothesis): The findings of the paper contradict a hypothesis.
-   **PREDICTS** (Hypothesis → Disease/Biomarker): The hypothesis makes a prediction about an outcome.

# OUTPUT FORMAT

Return ONLY valid JSON in this exact structure. No markdown formatting, no explanations, just the JSON:

{{
  "entities": [
    {{
      "name": "exact entity name as it appears in text",
      "type": "drug|disease|gene|protein|biomarker|pathway|mutation|hypothesis|study_design|statistical_method|evidence_line",
      "aliases": ["list", "of", "alternative", "names"],
      "canonical_id": "RxNorm:123456 or UMLS:C123456 or leave blank",
      "context": "brief context from paper (1 sentence max)",
      "iao_id": "IAO:0000018 for Hypothesis",
      "sepio_id": "SEPIO ID for Hypothesis or EvidenceLine",
      "status": "proposed|supported|controversial|refuted for Hypothesis",
      "obi_id": "OBI ID for StudyDesign",
      "stato_id": "STATO ID for StudyDesign or StatisticalMethod",
      "strength": "strong|moderate|weak for EvidenceLine"
    }}
  ],
  "relationships": [
    {{
      "subject": "entity name (MUST exactly match an entity in entities list)",
      "predicate": "TREATS|CAUSES|PREVENTS|ACTIVATES|INHIBITS|UPREGULATES|DOWNREGULATES|BINDS_TO|ASSOCIATED_WITH|TESTED_BY|SUPPORTS|REFUTES|PREDICTS",
      "object": "entity name (MUST exactly match an entity in entities list)",
      "confidence": 0.85,
      "evidence": "direct quote from paper, ideally 1-2 sentences, showing this relationship",
      "section": "abstract|methods|results|discussion"
    }}
  ],
  "metadata": {{
    "study_type": "rct|cohort|case_control|meta_analysis|systematic_review|in_vitro|in_vivo|case_report|review",
    "sample_size": 123,
    "study_population": "brief description if specified"
  }}
}}

# PAPER TO EXTRACT FROM

Title: {title}

Abstract: {abstract}

# YOUR EXTRACTION

Return only the JSON extraction following the format above:
"""

# Map of prompt versions for easy experimentation
PROMPT_VERSIONS = {
    "v1_detailed": MEDICAL_EXTRACTION_PROMPT_V1,
    "v2_cot": MEDICAL_EXTRACTION_PROMPT_V2_CHAIN_OF_THOUGHT,
    "v3_few_shot": MEDICAL_EXTRACTION_PROMPT_V3_FEW_SHOT,
    "v4_scientific_method": MEDICAL_EXTRACTION_PROMPT_V4_SCIENTIFIC_METHOD,
}