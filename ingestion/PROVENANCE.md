# Data Provenance and Quality

Ensuring high-quality data extraction is critical for building a reliable knowledge graph. This document outlines the principles of provenance tracking and prompt engineering that we use to ensure our data is reproducible, debuggable, and accurate.

## 1. Provenance Tracking

Every piece of data extracted by the ingestion pipeline must be traceable. We embed detailed provenance metadata into the output of every extracted paper. This allows us to debug inconsistencies, reproduce results, and systematically re-process data when the pipeline is updated.

### Provenance Checklist

The following metadata is captured for every extraction:

-   **Parser Version**:
    -   Git commit hash (short and full)
    -   Git branch name
    -   A "dirty" flag to indicate if there were uncommitted changes.
-   **Models Used**:
    -   LLM name and version (e.g., `llama3.1:70b`)
    -   Embedding model name (e.g., `dmis-lab/biobert-base-cased-v1.2`)
    -   Model parameters (e.g., temperature).
-   **Prompt**:
    -   The version or name of the prompt template used for extraction.
-   **Execution Context**:
    -   UTC timestamp of the extraction.
    -   Hostname of the machine that ran the script.
    -   Python version.
    -   Total duration of the extraction process.
-   **Entity Resolution**:
    -   Similarity threshold used for deduplication.
    -   A count of how many entities were matched against existing ones versus newly created.

### Why It Matters

With this metadata, you can answer critical questions without ambiguity:
```bash
# Find all papers extracted with an old prompt
jq '.extraction_provenance.prompt.version == "v1"' data/papers/*.json

# Find papers that were processed with uncommitted code
jq '.extraction_provenance.extraction_pipeline.git_dirty == true' data/papers/*.json

# Compare the entities extracted by two different models
diff <(jq '.entities' paper_llama.json) <(jq '.entities' paper_claude.json)
```

This level of tracking is essential for scientific reproducibility and operational stability.

## 2. High-Quality Extraction Prompts

The quality of the extracted data is heavily dependent on the quality of the prompts provided to the Large Language Model (LLM). We use detailed, "enterprise-style" prompts that leave little room for ambiguity.

### Principles of a High-Quality Prompt

-   **Explicit Ontology**: Clearly define the types of entities and relationships to be extracted (e.g., `GENE`, `DISEASE`, `COMPOUND`).
-   **Evidence Requirements**: Specify the textual evidence required to support a relationship.
-   **Confidence Scoring**: Provide a rubric for the model to assign `HIGH`, `MEDIUM`, or `LOW` confidence to its findings.
-   **Error Prevention**: Explicitly list common mistakes for the model to avoid.
-   **Quality Checklist**: Force the model to review its own output against a checklist before finalizing the result.
-   **Few-Shot Examples**: Include 2-3 examples of high-quality input text and the desired JSON output.

By providing detailed, structured instructions, we improve the consistency and accuracy of the LLM's output, making the resulting knowledge graph more reliable. The prompts are versioned and stored in `medical_prompts.py`, and the version used is recorded in the provenance metadata.
