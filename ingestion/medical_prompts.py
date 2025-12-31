"""
Enterprise-grade medical entity extraction prompts.

These prompts are inspired by production legal/medical document processing systems.
They are verbose and detailed because that's what works with LLMs at scale.
"""

MEDICAL_EXTRACTION_PROMPT_V1 = """You are a specialized medical knowledge extraction system trained to identify and structure biomedical information from peer-reviewed research papers.

Your task is to extract entities and relationships with high precision and recall, maintaining strict adherence to the evidence presented in the paper. You will be extracting information from TITLE and ABSTRACT sections of medical research papers.

# ENTITY TYPES TO EXTRACT

## 1. DRUG (Pharmaceutical compounds, therapies)
- Include: Generic names, brand names, drug classes, experimental compounds
- Capture: Chemical names (e.g., "acetylsalicylic acid"), brand names (e.g., "Aspirin"), drug classes (e.g., "NSAID")
- Note any dosage, administration route, or formulation if mentioned

## 2. DISEASE (Medical conditions, syndromes, disorders)
- Include: Diseases, disorders, syndromes, symptoms, pathological conditions
- Capture: ICD-10 terminology, colloquial names, abbreviations (e.g., "T2DM" for Type 2 Diabetes)
- Distinguish between: primary disease being studied, comorbidities, outcomes

## 3. GENE (Genetic elements)
- Include: Genes, gene variants, alleles, genetic loci
- Capture: Official gene symbols (e.g., "BRCA1"), full names, variant notation (e.g., "rs123456")
- Note: Include both human and model organism genes if relevant

## 4. PROTEIN (Protein products, enzymes, receptors)
- Include: Proteins, enzymes, receptors, antibodies, peptides
- Capture: Protein names, enzyme classifications (EC numbers), receptor subtypes
- Note: Distinguish from the genes that encode them

## 5. BIOMARKER (Measurable biological indicators)
- Include: Clinical biomarkers, lab values, physiological measurements
- Capture: Specific markers (e.g., "HbA1c", "PSA"), reference ranges if mentioned
- Note: Include imaging findings if they serve as biomarkers

# RELATIONSHIP TYPES TO EXTRACT

## TREATS (Drug → Disease)
Evidence required: Clinical trial data, case reports, therapeutic use
Confidence: HIGH if RCT data present, MEDIUM if observational, LOW if theoretical

## CAUSES (Entity → Disease/Condition)
Evidence required: Mechanistic data, epidemiological associations, experimental evidence
Note: Distinguish between causation and correlation

## PREVENTS (Drug → Disease)
Evidence required: Prophylactic use data, preventive trial outcomes
Note: Include risk reduction percentages if mentioned

## ACTIVATES / INHIBITS (Drug → Protein, Protein → Protein)
Evidence required: Biochemical assays, cellular studies, mechanistic data
Note: Specify if direct binding or indirect effect

## UPREGULATES / DOWNREGULATES (Drug → Gene/Protein, Protein → Gene/Protein)
Evidence required: Gene expression data, protein level measurements
Note: Include fold-change if quantified

## BINDS_TO (Drug → Protein, Protein → Protein)
Evidence required: Binding assays, structural data, affinity measurements
Note: Include Kd values if reported

## ASSOCIATED_WITH (Any → Any)
Evidence required: Statistical correlation, observational studies
Note: Use only when mechanism is unclear; prefer more specific relationships

# EXTRACTION RULES

## Evidence Quality Assessment
For each relationship, assign confidence based on:
- HIGH (0.9-1.0): Randomized controlled trials, meta-analyses, replicated findings
- MEDIUM (0.7-0.89): Observational studies, single trials, mechanistic studies
- LOW (0.5-0.69): Case reports, preliminary findings, theoretical predictions

## Specificity Requirements
- Extract the MOST SPECIFIC entity name mentioned
- Example: Prefer "lisinopril" over "ACE inhibitor" when both are mentioned
- Example: Prefer "Type 2 Diabetes Mellitus" over "diabetes" when specified

## Avoid Common Errors
- Do NOT extract: General medical terms without specific relevance (e.g., "patient", "treatment")
- Do NOT extract: Study design elements as entities (e.g., "randomized controlled trial" is metadata, not an entity)
- Do NOT extract: Anatomical locations unless they are disease-specific (e.g., "breast" alone is not useful, but "breast tissue" in context might be)
- Do NOT infer relationships not explicitly stated or strongly implied in the text

## Canonical ID Assignment
When you recognize entities with standard identifiers, include them:
- Drugs: RxNorm codes (e.g., "RxNorm:860975" for Metformin)
- Diseases: UMLS CUIs (e.g., "UMLS:C0011860" for Type 2 Diabetes)
- Genes: HGNC symbols or Entrez Gene IDs
- Proteins: UniProt accessions
If you don't know the canonical ID with certainty, leave it blank (the entity resolution system will handle it)

## Section Attribution
Tag each relationship with the section it came from:
- "abstract": Information from the abstract
- "methods": Methodology section
- "results": Results/findings section
- "discussion": Discussion/interpretation section
If processing only abstract: use "abstract" for all

# OUTPUT FORMAT

Return ONLY valid JSON in this exact structure. No markdown formatting, no explanations, just the JSON:

{{
  "entities": [
    {{
      "name": "exact entity name as it appears in text",
      "type": "drug|disease|gene|protein|biomarker",
      "aliases": ["list", "of", "alternative", "names", "mentioned", "in", "paper"],
      "canonical_id": "RxNorm:123456 or UMLS:C123456 or leave blank",
      "context": "brief context from paper (1 sentence max)"
    }}
  ],
  "relationships": [
    {{
      "subject": "entity name (MUST exactly match an entity in entities list)",
      "predicate": "TREATS|CAUSES|PREVENTS|ACTIVATES|INHIBITS|UPREGULATES|DOWNREGULATES|BINDS_TO|ASSOCIATED_WITH",
      "object": "entity name (MUST exactly match an entity in entities list)",
      "confidence": 0.85,
      "evidence": "direct quote from paper, ideally 1-2 sentences, showing this relationship",
      "section": "abstract|methods|results|discussion",
      "metadata": {{
        "study_type": "if relationship comes from specific study type",
        "measurement": "quantitative data if available (e.g., 'HR=0.75, p<0.01')",
        "temporal": "timing information if relevant (e.g., 'after 6 months')"
      }}
    }}
  ],
  "metadata": {{
    "study_type": "rct|cohort|case_control|meta_analysis|systematic_review|in_vitro|in_vivo|case_report|review",
    "sample_size": 123,
    "study_population": "brief description if specified (e.g., 'postmenopausal women', 'adults >65')",
    "primary_outcome": "main outcome measured",
    "publication_date": "YYYY-MM-DD if available in text",
    "clinical_phase": "Phase I|II|III|IV if applicable"
  }}
}}

# QUALITY CHECKLIST

Before returning your extraction, verify:
1. ✓ All relationship subjects and objects appear in entities list (exact string match)
2. ✓ Each relationship has supporting evidence quote
3. ✓ Confidence scores reflect evidence quality (not all should be 0.9)
4. ✓ Entity types are appropriate (no genes labeled as proteins unless you're certain)
5. ✓ No duplicate entities (consolidate alternative names as aliases)
6. ✓ Predicate verbs match the allowed relationship types exactly
7. ✓ JSON is valid (no trailing commas, properly escaped quotes)

# PAPER TO EXTRACT FROM

Title: {title}

Abstract: {abstract}

# YOUR EXTRACTION

Return only the JSON extraction following the format above:"""


MEDICAL_EXTRACTION_PROMPT_V2_CHAIN_OF_THOUGHT = """You are a specialized medical knowledge extraction system. You will perform extraction in two phases:

PHASE 1 - ANALYSIS (think step-by-step, but don't output this):
- Identify the main research question
- Note the study design and population
- List key findings
- Identify all medical entities mentioned
- Map relationships between entities
- Assess evidence quality for each relationship

PHASE 2 - STRUCTURED EXTRACTION (output this as JSON)

[REST OF PROMPT SAME AS V1...]

This approach often improves accuracy with models like llama3.1:70b."""


MEDICAL_EXTRACTION_PROMPT_V3_FEW_SHOT = """You are a specialized medical knowledge extraction system.

Here are two examples of high-quality extractions:

## EXAMPLE 1

Input Paper:
Title: Metformin Improves Glycemic Control via AMPK Activation
Abstract: Metformin, a first-line therapy for type 2 diabetes, activates AMP-activated protein kinase (AMPK), leading to decreased hepatic glucose production and improved insulin sensitivity. In this randomized controlled trial of 450 patients, metformin (1500mg daily) reduced HbA1c by 1.2% compared to placebo (p<0.001).

Expected Output:
{{
  "entities": [
    {{
      "name": "Metformin",
      "type": "drug",
      "aliases": ["metformin"],
      "canonical_id": "RxNorm:860975",
      "context": "first-line therapy for type 2 diabetes"
    }},
    {{
      "name": "Type 2 Diabetes",
      "type": "disease",
      "aliases": ["T2DM"],
      "canonical_id": "UMLS:C0011860",
      "context": "condition being treated"
    }},
    {{
      "name": "AMPK",
      "type": "protein",
      "aliases": ["AMP-activated protein kinase"],
      "canonical_id": "NCBI:Gene:5562",
      "context": "activated by metformin"
    }},
    {{
      "name": "HbA1c",
      "type": "biomarker",
      "aliases": ["glycated hemoglobin"],
      "canonical_id": "LOINC:4548-4",
      "context": "glycemic control biomarker"
    }}
  ],
  "relationships": [
    {{
      "subject": "Metformin",
      "predicate": "TREATS",
      "object": "Type 2 Diabetes",
      "confidence": 0.95,
      "evidence": "Metformin, a first-line therapy for type 2 diabetes",
      "section": "abstract"
    }},
    {{
      "subject": "Metformin",
      "predicate": "ACTIVATES",
      "object": "AMPK",
      "confidence": 0.92,
      "evidence": "Metformin...activates AMP-activated protein kinase (AMPK), leading to decreased hepatic glucose production",
      "section": "abstract",
      "metadata": {{
        "mechanism": "direct activation"
      }}
    }},
    {{
      "subject": "Metformin",
      "predicate": "DOWNREGULATES",
      "object": "HbA1c",
      "confidence": 0.93,
      "evidence": "metformin (1500mg daily) reduced HbA1c by 1.2% compared to placebo (p<0.001)",
      "section": "abstract",
      "metadata": {{
        "study_type": "rct",
        "measurement": "HbA1c reduction: 1.2%, p<0.001"
      }}
    }}
  ],
  "metadata": {{
    "study_type": "rct",
    "sample_size": 450
  }}
}}

## EXAMPLE 2

[Add another example for a different domain, e.g., oncology...]

## NOW EXTRACT FROM THIS PAPER

[INCLUDE FULL EXTRACTION RULES FROM V1...]

Title: {title}
Abstract: {abstract}

Return only JSON:"""


# Map of prompt versions for easy experimentation
PROMPT_VERSIONS = {
    "v1_detailed": MEDICAL_EXTRACTION_PROMPT_V1,
    "v2_cot": MEDICAL_EXTRACTION_PROMPT_V2_CHAIN_OF_THOUGHT,
    "v3_few_shot": MEDICAL_EXTRACTION_PROMPT_V3_FEW_SHOT,
}
