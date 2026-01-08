"""
Enterprise-grade medical entity extraction prompts.

These prompts are inspired by production legal/medical document processing systems.
They are verbose and detailed because that's what works with LLMs at scale.
"""

MEDICAL_EXTRACTION_PROMPT_V1 = """You are a specialized medical knowledge extraction system trained to identify and structure biomedical information from peer-reviewed research papers.

Your task is to extract entities and relationships with high precision and recall, maintaining strict adherence to the evidence presented in the paper. You will be extracting information from TITLE and ABSTRACT sections of medical research papers.

# ENTITY TYPES TO EXTRACT

## Core Medical Entities

### 1. DRUG (Pharmaceutical compounds, therapies)
- Include: Generic names, brand names, drug classes, experimental compounds
- Capture: Chemical names (e.g., "acetylsalicylic acid"), brand names (e.g., "Aspirin"), drug classes (e.g., "NSAID")
- Note any dosage, administration route, or formulation if mentioned
- Optional fields: rxnorm_id, brand_names (list), drug_class, mechanism

### 2. DISEASE (Medical conditions, syndromes, disorders)
- Include: Diseases, disorders, syndromes, pathological conditions
- Capture: ICD-10 terminology, colloquial names, abbreviations (e.g., "T2DM" for Type 2 Diabetes)
- Distinguish between: primary disease being studied, comorbidities, outcomes
- Optional fields: umls_id, mesh_id, icd10_codes (list), category

### 3. GENE (Genetic elements)
- Include: Genes, gene variants, alleles, genetic loci
- Capture: Official gene symbols (e.g., "BRCA1"), full names, variant notation (e.g., "rs123456")
- Note: Include both human and model organism genes if relevant
- Optional fields: symbol, hgnc_id, chromosome, entrez_id

### 4. PROTEIN (Protein products, enzymes, receptors)
- Include: Proteins, enzymes, receptors, antibodies, peptides
- Capture: Protein names, enzyme classifications (EC numbers), receptor subtypes
- Note: Distinguish from the genes that encode them
- Optional fields: uniprot_id, gene_id, function, pathways (list)

### 5. MUTATION (Genetic variants)
- Include: Specific genetic variants, SNPs, indels, chromosomal rearrangements
- Capture: Variant notation (e.g., "BRAF V600E", "rs123456", "c.1234G>A")
- Note: Link to the gene where variant occurs if mentioned
- Optional fields: gene_id, variant_type, notation, consequence

### 6. BIOMARKER (Measurable biological indicators)
- Include: Clinical biomarkers, lab values, physiological measurements
- Capture: Specific markers (e.g., "HbA1c", "PSA"), reference ranges if mentioned
- Note: Include imaging findings if they serve as biomarkers
- Optional fields: loinc_code, measurement_type, normal_range

### 7. PATHWAY (Biological pathways)
- Include: Signaling pathways, metabolic pathways, regulatory cascades
- Capture: Pathway names (e.g., "MAPK signaling pathway", "glycolysis")
- Note: Extract genes/proteins involved if mentioned
- Optional fields: kegg_id, reactome_id, category, genes_involved (list)

### 8. SYMPTOM (Clinical signs and symptoms)
- Include: Observable signs, patient-reported symptoms, clinical presentations
- Capture: Specific symptoms (e.g., "dyspnea", "fever", "chest pain")
- Note: Distinguish from diseases (symptom is a manifestation, disease is the condition)
- Optional fields: severity_scale

### 9. PROCEDURE (Medical procedures and interventions)
- Include: Surgical procedures, diagnostic tests, therapeutic interventions
- Capture: Specific procedures (e.g., "mastectomy", "CT scan", "radiation therapy")
- Note: Include invasiveness level if mentioned
- Optional fields: procedure_type, invasiveness

### 10. ANATOMICAL_STRUCTURE (Anatomical locations and structures)
- Include: Organs, tissues, body regions, cellular structures
- Capture: Specific anatomical terms (e.g., "hippocampus", "breast tissue", "liver")
- Note: Only extract when clinically relevant to the paper's focus
- Optional fields: location, system

### 11. TEST (Diagnostic and laboratory tests)
- Include: Lab tests, diagnostic assays, screening procedures
- Capture: Specific test names (e.g., "PCR", "ELISA", "mammography")
- Note: Distinguish from biomarkers (test is the assay, biomarker is what's measured)
- Optional fields: test_type, methodology

## Scientific Method Entities

### 12. HYPOTHESIS (Scientific hypotheses)
- Include: Specific hypotheses being tested, proposed, supported, or refuted
- Capture: Core statement of the hypothesis (e.g., "Amyloid cascade hypothesis")
- Look for: "we hypothesize that...", "our hypothesis is...", "this supports the idea that..."
- Optional fields: iao_id, sepio_id, proposed_by, proposed_date, status, description, predicts (list)

### 13. STUDY_DESIGN (Study design types)
- Include: RCT, cohort study, case-control, meta-analysis, systematic review, etc.
- Capture: The design type mentioned in the paper
- Note: Evidence quality level (1-5, where 1 is highest like RCT/meta-analysis)
- Optional fields: obi_id, stato_id, design_type, evidence_level, description

### 14. STATISTICAL_METHOD (Statistical methods and tests)
- Include: Specific statistical tests and analytical methods
- Capture: Method names (e.g., "t-test", "chi-squared", "ANOVA", "Cox regression")
- Note: Include method assumptions if mentioned
- Optional fields: stato_id, method_type, description, assumptions (list)

### 15. EVIDENCE_LINE (Structured evidence chains)
- Include: Lines of evidence supporting or refuting claims
- Capture: The assertion or conclusion being supported by evidence
- Note: Link to hypotheses this evidence supports or refutes
- Optional fields: sepio_type, eco_type, assertion_id, supports (list), refutes (list), evidence_items (list), strength

# RELATIONSHIP TYPES TO EXTRACT

## Core Medical Relationships

### TREATS (Drug → Disease)
Evidence required: Clinical trial data, case reports, therapeutic use
Confidence: HIGH if RCT data present, MEDIUM if observational, LOW if theoretical

### PREVENTS (Drug → Disease)
Evidence required: Prophylactic use data, preventive trial outcomes
Note: Include risk reduction percentages if mentioned

### CAUSES (Mutation/Gene/Protein → Disease | Entity → Symptom)
Evidence required: Mechanistic data, epidemiological associations, experimental evidence
Note: Distinguish between causation and correlation

### INCREASES_RISK / DECREASES_RISK (Mutation/Gene → Disease)
Evidence required: Genetic association studies, family studies, population data
Note: Include odds ratios or hazard ratios if mentioned

## Molecular Relationships

### ACTIVATES / INHIBITS (Drug → Protein | Protein → Protein | Drug → Pathway)
Evidence required: Biochemical assays, cellular studies, mechanistic data
Note: Specify if direct binding or indirect effect

### UPREGULATES / DOWNREGULATES (Drug → Gene/Protein | Protein → Gene/Protein)
Evidence required: Gene expression data, protein level measurements
Note: Include fold-change if quantified

### BINDS_TO (Drug → Protein | Protein → Protein | Drug → Gene)
Evidence required: Binding assays, structural data, affinity measurements
Note: Include Kd values if reported

### ENCODES (Gene → Protein)
Evidence required: Gene-protein mapping, molecular biology data
Note: Standard gene-protein relationship

### PARTICIPATES_IN (Protein/Gene → Pathway)
Evidence required: Pathway databases, molecular studies
Note: Indicates involvement in biological pathway

## Clinical Relationships

### DIAGNOSES / DIAGNOSED_BY (Disease ↔ Test)
Evidence required: Diagnostic studies, clinical validation
Note: Bidirectional relationship

### INDICATES (Biomarker → Disease | Test → Disease)
Evidence required: Diagnostic accuracy studies, clinical correlation
Note: Include sensitivity/specificity if mentioned

### MANIFESTS_AS (Disease → Symptom)
Evidence required: Clinical presentation data, case series
Note: Links disease to its symptoms

### LOCATED_IN (Disease/Procedure → Anatomical_Structure)
Evidence required: Anatomical localization
Note: Specifies anatomical location

## Research Method Relationships

### TESTED_BY (Hypothesis → Study_Design)
Evidence required: Explicit mention in methods
Note: Links hypothesis to study design used to test it

### SUPPORTS (Evidence_Line → Hypothesis | Study_Design → Hypothesis)
Evidence required: Results and discussion sections
Note: Evidence or study supports hypothesis

### REFUTES (Evidence_Line → Hypothesis | Study_Design → Hypothesis)
Evidence required: Results contradicting hypothesis
Note: Evidence or study contradicts hypothesis

### PREDICTS (Hypothesis → Disease/Biomarker)
Evidence required: Hypothesis makes prediction
Note: What the hypothesis predicts

### USES_METHOD (Study_Design → Statistical_Method)
Evidence required: Statistical methods section
Note: Links study to statistical methods employed

## General Relationships

### ASSOCIATED_WITH (Any → Any)
Evidence required: Statistical correlation, observational studies
Note: Use only when mechanism is unclear; prefer more specific relationships

### INTERACTS_WITH (Drug → Drug | Protein → Protein)
Evidence required: Interaction studies, pharmacology data
Note: Drug-drug interactions or protein-protein interactions

### AFFECTS (Any → Any)
Evidence required: Any influence relationship
Note: Generic relationship when more specific type unclear

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
- Do NOT extract: Overly generic terms (e.g., "cell", "tissue" alone without specific type)
- Do NOT extract: Anatomical locations unless clinically relevant to the paper's focus
- Do NOT infer relationships not explicitly stated or strongly implied in the text
- Do NOT confuse entity types:
  - Gene vs Protein (BRCA1 gene vs BRCA1 protein)
  - Disease vs Symptom (diabetes is disease, polyuria is symptom)
  - Test vs Biomarker (ELISA is test, PSA is biomarker)
  - Procedure vs Test (biopsy is procedure, histology is test)

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
      "type": "drug|disease|gene|protein|mutation|biomarker|pathway|symptom|procedure|anatomical_structure|test|hypothesis|study_design|statistical_method|evidence_line",
      "aliases": ["list", "of", "alternative", "names", "mentioned", "in", "paper"],
      "canonical_id": "RxNorm:123456 or UMLS:C123456 or leave blank",
      "context": "brief context from paper (1 sentence max)",

      // Optional entity-specific fields (include only if relevant to entity type):

      // For DRUG entities:
      "rxnorm_id": "RxNorm ID if known",
      "brand_names": ["list of brand names"],
      "drug_class": "therapeutic class",
      "mechanism": "mechanism of action",

      // For DISEASE entities:
      "umls_id": "UMLS CUI",
      "mesh_id": "MeSH ID",
      "icd10_codes": ["ICD-10 codes"],
      "category": "disease category",

      // For GENE entities:
      "symbol": "gene symbol",
      "hgnc_id": "HGNC ID",
      "chromosome": "chromosomal location",
      "entrez_id": "NCBI Gene ID",

      // For PROTEIN entities:
      "uniprot_id": "UniProt ID",
      "gene_id": "encoding gene ID",
      "function": "biological function",
      "pathways": ["pathways involved"],

      // For MUTATION entities:
      "gene_id": "associated gene",
      "variant_type": "SNP|indel|deletion|etc",
      "notation": "variant notation",
      "consequence": "functional consequence",

      // For BIOMARKER entities:
      "loinc_code": "LOINC code",
      "measurement_type": "blood|tissue|imaging",
      "normal_range": "reference range",

      // For PATHWAY entities:
      "kegg_id": "KEGG ID",
      "reactome_id": "Reactome ID",
      "pathway_category": "signaling|metabolic|etc",
      "genes_involved": ["gene IDs"],

      // For SYMPTOM entities:
      "severity_scale": "severity scale if mentioned",

      // For PROCEDURE entities:
      "procedure_type": "surgical|diagnostic|therapeutic",
      "invasiveness": "invasive|minimally_invasive|non_invasive",

      // For HYPOTHESIS entities:
      "iao_id": "IAO:0000018",
      "sepio_id": "SEPIO ID",
      "proposed_by": "paper ID",
      "proposed_date": "ISO date",
      "status": "proposed|supported|controversial|refuted",
      "description": "hypothesis description",
      "predicts": ["entity IDs"],

      // For STUDY_DESIGN entities:
      "obi_id": "OBI ID",
      "stato_id": "STATO ID",
      "design_type": "interventional|observational",
      "evidence_level": 1,
      "description": "study design description",

      // For STATISTICAL_METHOD entities:
      "stato_id": "STATO ID",
      "method_type": "hypothesis_test|regression|etc",
      "description": "method description",
      "assumptions": ["method assumptions"],

      // For EVIDENCE_LINE entities:
      "sepio_type": "SEPIO evidence type",
      "eco_type": "ECO evidence type",
      "assertion_id": "assertion ID",
      "supports": ["hypothesis IDs"],
      "refutes": ["hypothesis IDs"],
      "evidence_items": ["paper IDs"],
      "strength": "strong|moderate|weak"
    }}
  ],
  "relationships": [
    {{
      "subject": "entity name (MUST exactly match an entity in entities list)",
      "predicate": "TREATS|PREVENTS|CAUSES|INCREASES_RISK|DECREASES_RISK|ACTIVATES|INHIBITS|UPREGULATES|DOWNREGULATES|BINDS_TO|ENCODES|PARTICIPATES_IN|DIAGNOSES|DIAGNOSED_BY|INDICATES|MANIFESTS_AS|LOCATED_IN|TESTED_BY|SUPPORTS|REFUTES|PREDICTS|USES_METHOD|ASSOCIATED_WITH|INTERACTS_WITH|AFFECTS",
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


MEDICAL_EXTRACTION_PROMPT_V2_CHAIN_OF_THOUGHT = (
    """You are a specialized medical knowledge extraction system. You will perform extraction in two phases:

PHASE 1 - ANALYSIS (think step-by-step, but don't output this):
- Identify the main research question
- Note the study design and population
- List key findings
- Identify all medical entities mentioned (15 types: drug, disease, gene, protein, mutation, biomarker, pathway, symptom, procedure, anatomical_structure, test, hypothesis, study_design, statistical_method, evidence_line)
- Map relationships between entities
- Assess evidence quality for each relationship

PHASE 2 - STRUCTURED EXTRACTION (output this as JSON)

Your task is to extract entities and relationships with high precision and recall, maintaining strict adherence to the evidence presented in the paper. You will be extracting information from TITLE and ABSTRACT sections of medical research papers.

"""
    + MEDICAL_EXTRACTION_PROMPT_V1.split("Your task is to extract entities", 1)[1].split("# PAPER TO EXTRACT FROM")[0]
    + """

# PAPER TO EXTRACT FROM

Title: {title}

Abstract: {abstract}

# YOUR EXTRACTION

First, think through the analysis (PHASE 1 above), then output only the JSON extraction following the format above.
This two-phase approach often improves accuracy with models like llama3.1:70b."""
)


MEDICAL_EXTRACTION_PROMPT_V3_FEW_SHOT = (
    """You are a specialized medical knowledge extraction system.

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

Input Paper:
Title: BRAF V600E Mutation Predicts Response to BRAF Inhibitors in Melanoma
Abstract: The BRAF V600E mutation is present in approximately 50% of melanomas and results in constitutive activation of the MAPK signaling pathway. In this phase III randomized controlled trial (n=675), patients with BRAF V600E-mutated metastatic melanoma treated with vemurafenib (a BRAF inhibitor) showed significantly improved progression-free survival compared to dacarbazine (HR=0.26, 95% CI: 0.20-0.33, p<0.001). Overall response rate was 48% vs 5%. The study demonstrates that BRAF V600E mutation serves as a predictive biomarker for BRAF inhibitor therapy.

Expected Output:
{{
  "entities": [
    {{
      "name": "BRAF V600E",
      "type": "mutation",
      "aliases": ["BRAF V600E mutation"],
      "canonical_id": "",
      "context": "mutation present in 50% of melanomas",
      "gene_id": "BRAF",
      "variant_type": "missense",
      "notation": "V600E",
      "consequence": "constitutive MAPK activation"
    }},
    {{
      "name": "BRAF",
      "type": "gene",
      "aliases": [],
      "canonical_id": "HGNC:1097",
      "context": "gene with V600E mutation",
      "symbol": "BRAF",
      "hgnc_id": "HGNC:1097"
    }},
    {{
      "name": "Melanoma",
      "type": "disease",
      "aliases": ["metastatic melanoma"],
      "canonical_id": "UMLS:C0025202",
      "context": "disease being studied",
      "umls_id": "C0025202"
    }},
    {{
      "name": "Vemurafenib",
      "type": "drug",
      "aliases": [],
      "canonical_id": "RxNorm:1147220",
      "context": "BRAF inhibitor tested in trial",
      "rxnorm_id": "1147220",
      "drug_class": "BRAF inhibitor",
      "mechanism": "inhibits mutant BRAF kinase"
    }},
    {{
      "name": "MAPK signaling pathway",
      "type": "pathway",
      "aliases": ["MAPK pathway"],
      "canonical_id": "KEGG:04010",
      "context": "constitutively activated by BRAF V600E",
      "kegg_id": "04010",
      "pathway_category": "signaling"
    }},
    {{
      "name": "Randomized Controlled Trial",
      "type": "study_design",
      "aliases": ["RCT", "phase III RCT"],
      "canonical_id": "OBI:0000008",
      "context": "study design used",
      "obi_id": "OBI:0000008",
      "design_type": "interventional",
      "evidence_level": 1
    }}
  ],
  "relationships": [
    {{
      "subject": "BRAF V600E",
      "predicate": "ACTIVATES",
      "object": "MAPK signaling pathway",
      "confidence": 0.95,
      "evidence": "BRAF V600E mutation...results in constitutive activation of the MAPK signaling pathway",
      "section": "abstract"
    }},
    {{
      "subject": "BRAF V600E",
      "predicate": "INCREASES_RISK",
      "object": "Melanoma",
      "confidence": 0.90,
      "evidence": "The BRAF V600E mutation is present in approximately 50% of melanomas",
      "section": "abstract"
    }},
    {{
      "subject": "Vemurafenib",
      "predicate": "TREATS",
      "object": "Melanoma",
      "confidence": 0.95,
      "evidence": "patients with BRAF V600E-mutated metastatic melanoma treated with vemurafenib...showed significantly improved progression-free survival (HR=0.26, p<0.001)",
      "section": "abstract",
      "metadata": {{
        "study_type": "rct",
        "measurement": "HR=0.26, 95% CI: 0.20-0.33, p<0.001"
      }}
    }},
    {{
      "subject": "Vemurafenib",
      "predicate": "INHIBITS",
      "object": "BRAF",
      "confidence": 0.93,
      "evidence": "vemurafenib (a BRAF inhibitor)",
      "section": "abstract"
    }},
    {{
      "subject": "BRAF V600E",
      "predicate": "PREDICTS",
      "object": "Vemurafenib",
      "confidence": 0.95,
      "evidence": "BRAF V600E mutation serves as a predictive biomarker for BRAF inhibitor therapy",
      "section": "abstract"
    }}
  ],
  "metadata": {{
    "study_type": "rct",
    "sample_size": 675,
    "study_population": "patients with BRAF V600E-mutated metastatic melanoma",
    "primary_outcome": "progression-free survival",
    "clinical_phase": "Phase III"
  }}
}}

## NOW EXTRACT FROM THIS PAPER

"""
    + MEDICAL_EXTRACTION_PROMPT_V1.split("# ENTITY TYPES TO EXTRACT", 1)[1].split("# PAPER TO EXTRACT FROM")[0]
    + """

# PAPER TO EXTRACT FROM

Title: {title}
Abstract: {abstract}

# YOUR EXTRACTION

Return only the JSON extraction following the format above:"""
)


# Map of prompt versions for easy experimentation
PROMPT_VERSIONS = {
    "v1_detailed": MEDICAL_EXTRACTION_PROMPT_V1,
    "v2_cot": MEDICAL_EXTRACTION_PROMPT_V2_CHAIN_OF_THOUGHT,
    "v3_few_shot": MEDICAL_EXTRACTION_PROMPT_V3_FEW_SHOT,
}
