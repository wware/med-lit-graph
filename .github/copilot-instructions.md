# GitHub Copilot Instructions for med-lit-graph

## Project Overview

This is a **provenance-first medical knowledge graph** built on PubMed/PMC literature. The system transforms medical research papers into a queryable graph database where every relationship is traceable to specific evidence from peer-reviewed literature.

**Core Purpose**: Enable clinicians and researchers to perform multi-hop graph queries for complex diagnostic reasoning, drug repurposing, and evidence synthesis with full citation traceability.

## Architecture

```
User Interfaces
├── Python Client Library (client/python/)
├── TypeScript/JavaScript Client (client/typescript/)
├── REST API (FastAPI)
└── MCP Server for LLMs (mcp/)
         │
    Query API (FastAPI)
         │
    ┌────┴────┬─────────┐
OpenSearch  Neptune     S3
(Vector)    (Graph)   (JSON Source)
```

**Key Components**:
- `schema/`: Pydantic models for entities and relationships (source of truth)
- `client/`: Client libraries in Python and TypeScript
- `mcp/`: MCP server for LLM integration (Claude, ChatGPT)
- `tests/`: Comprehensive test suite

## Critical Design Principles

### 1. Provenance is MANDATORY

**Every medical relationship MUST include evidence.** This is non-negotiable.

```python
# ❌ WRONG - Will fail validation
treats = Treats(
    subject_id="RxNorm:1187832",
    object_id="UMLS:C0006142",
    response_rate=0.59
)

# ✅ CORRECT - Evidence required
treats = Treats(
    subject_id="RxNorm:1187832",
    object_id="UMLS:C0006142",
    evidence=[
        Evidence(
            paper_id="PMC999888",
            section_type="results",
            paragraph_idx=8,
            extraction_method="table_parser",
            confidence=0.92,
            study_type="rct",
            sample_size=302
        )
    ],
    response_rate=0.59
)
```

**When writing any code that creates relationships**:
- ALWAYS include at least one Evidence object
- Use the Evidence model from `schema/entity.py`
- Include paper_id, confidence, and study_type at minimum
- Rich provenance (section_type, paragraph_idx, text_span) is strongly encouraged

### 2. Use Pydantic Models, Not Dataclasses

All entities and relationships are defined as **Pydantic models** for validation.

- ✅ Use: `from pydantic import BaseModel, Field`
- ❌ Don't use: `@dataclass` from Python standard library
- All entity classes inherit from `BaseMedicalEntity`
- All medical relationships inherit from `BaseMedicalRelationship`

### 3. Type Safety via Enums

Use strongly-typed enums for entity types and relationship types:

```python
from schema.entity import EntityType
from schema.relationship import RelationType

# ✅ CORRECT - Type safe
disease = Disease(entity_type=EntityType.DISEASE)
rel = Treats(predicate=RelationType.TREATS)

# ❌ WRONG - String literals bypass validation
disease = Disease(entity_type="disease")
```

### 4. Evidence Quality Weighting

Not all studies are equal. Use the study type hierarchy:

```python
STUDY_WEIGHTS = {
    'rct': 1.0,              # Gold standard
    'meta_analysis': 0.95,
    'cohort': 0.8,
    'observational': 0.6,
    'case_report': 0.4
}
```

When creating Evidence objects, use the appropriate study_type from the Literal type.

### 5. Ontology Standards

Use standardized identifiers:
- **Diseases**: UMLS Concept IDs (e.g., "C0006142")
- **Genes**: HGNC IDs (e.g., "HGNC:1100")
- **Drugs**: RxNorm IDs (e.g., "RxNorm:1187832")
- **Proteins**: UniProt IDs (e.g., "P38398")

## Code Style and Conventions

### Python Conventions

1. **Line Length**: 200 characters (configured in pyproject.toml)
2. **Type Hints**: Required everywhere that makes sense
3. **Docstrings**: Full docstrings everywhere, always
4. **Imports**: Use absolute imports, organize by standard library → third party → local

```python
# Example structure
"""
Module docstring explaining purpose.

Detailed description with examples if needed.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field
from tqdm import tqdm

from .entity import EntityType, Evidence
```

5. **String Quotes**: Consistent double quotes for docstrings, flexible for other strings
6. **Naming Conventions**:
   - Classes: PascalCase (e.g., `MedicalGraphClient`, `Evidence`)
   - Functions/methods: snake_case (e.g., `find_treatments`, `validate_evidence`)
   - Constants: UPPER_SNAKE_CASE (e.g., `STUDY_WEIGHTS`, `DEFAULT_CONFIDENCE`)
   - Private members: prefix with underscore (e.g., `_internal_method`)

### Testing with pytest

- Use **pytest** for all tests
- Fixtures should be used where appropriate
- Test files in `tests/` directory
- Naming: `test_*.py` for test files, `test_*` for test functions

```python
# Example test structure
import pytest
from schema.relationship import Treats
from schema.entity import Evidence

def test_relationship_requires_evidence():
    """Test that medical relationships require evidence."""
    with pytest.raises(ValueError):
        Treats(
            subject_id="drug123",
            object_id="disease456"
            # Missing evidence - should fail
        )
```

## Building, Linting, and Testing

### Environment Setup

This project uses **uv** for virtual environment management (preferred over venv/virtualenv).

```bash
# Setup
uv sync  # Install dependencies

# Development
uv pip install -e .
```

### Linting and Formatting

Run in this order (as defined in `check.sh`):

```bash
# 1. Lint with ruff
uv run ruff check <files>

# 2. Format with black
uv run black <files>

# 3. Lint with pylint (errors only)
uv run pylint -E <files>

# 4. Check with flake8
uv run flake8 --max-line-length=200 <files>

# 5. Type check with mypy
uv run mypy <files>

# 6. Run tests
uv run pytest tests/
```

**OR** use the provided script:
```bash
./check.sh
```

### Pre-commit Checklist

Before committing:
1. Run ruff check and fix any issues
2. Run black to format code
3. Run pylint -E to catch errors
4. Run mypy to check types
5. Run pytest to ensure tests pass

## Common Patterns

### Creating Entities

```python
from schema.entity import Disease, EntityType

disease = Disease(
    entity_id="C0006142",
    entity_type=EntityType.DISEASE,
    name="Breast Cancer",
    synonyms=["Breast Carcinoma", "Mammary Cancer"],
    abbreviations=["BC"],
    umls_id="C0006142",
    mesh_id="D001943",
    icd10_codes=["C50.9"],
    source="umls"
)
```

### Creating Relationships with Evidence

```python
from schema.relationship import Treats
from schema.entity import Evidence

treats = Treats(
    subject_id="RxNorm:1187832",
    predicate=RelationType.TREATS,
    object_id="C0006142",
    evidence=[
        Evidence(
            paper_id="PMC999888",
            section_type="results",
            paragraph_idx=8,
            confidence=0.92,
            study_type="rct",
            sample_size=302,
            extraction_method="table_parser"
        )
    ],
    response_rate=0.59
)
```

### Using the Query Client

```python
from client.python.client import MedicalGraphClient, QueryBuilder
import os

client = MedicalGraphClient(os.getenv("MEDGRAPH_SERVER"))

# High-level convenience method
treatments = client.find_treatments("breast cancer")

# Custom query with builder
query = (QueryBuilder()
    .find_nodes("drug")
    .with_edge("treats", min_confidence=0.7)
    .filter_target("disease", name="breast cancer")
    .limit(20)
    .build())

results = client.execute(query)
```

## Anti-Patterns to Avoid

### ❌ Don't: Create relationships without evidence
```python
# This will fail validation
treats = Treats(subject_id="drug1", object_id="disease1")
```

### ❌ Don't: Use string literals instead of enums
```python
# This bypasses type checking
disease = Disease(entity_type="disease")
```

### ❌ Don't: Ignore confidence scores
```python
# Always provide meaningful confidence
evidence = Evidence(paper_id="PMC123", confidence=0.5)  # Default, but be explicit
```

### ❌ Don't: Mix dataclasses with Pydantic models
```python
# Don't use @dataclass - use Pydantic BaseModel
from dataclasses import dataclass  # ❌ Wrong

@dataclass
class MyEntity:  # ❌ Wrong approach
    name: str
```

### ❌ Don't: Skip study_type in evidence
```python
# Always include study type for quality weighting
evidence = Evidence(
    paper_id="PMC123",
    study_type="rct",  # ✅ Essential for evidence quality
    confidence=0.92
)
```

## File Organization

```
med-lit-graph/
├── schema/              # Core schema definitions (Pydantic models)
│   ├── entity.py       # Entity types (Disease, Gene, Drug, etc.)
│   ├── relationship.py # Relationship types (Treats, Causes, etc.)
│   └── __init__.py
├── client/             # Client libraries
│   ├── python/        # Python client
│   │   ├── client.py  # Main client and QueryBuilder
│   │   └── __init__.py
│   └── typescript/    # TypeScript client (future)
├── mcp/               # MCP server for LLM integration
│   ├── server.py      # MCP server implementation
│   └── __init__.py
├── tests/             # Test suite
│   ├── test_schema_entity.py
│   ├── test_relationship.py
│   ├── test_client.py
│   └── ...
├── pyproject.toml     # Project configuration
├── check.sh          # Linting and testing script
└── README.md         # Project documentation
```

## Query Language

The project uses a JSON-based query language that's:
- **LLM-friendly**: Easy for AI to generate
- **Database-agnostic**: Translates to Cypher, Gremlin, or SPARQL
- **Human-readable**: Clear structure and semantics

### Query Structure

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.7
  },
  "filters": [
    {"field": "target.name", "operator": "contains", "value": "cancer"}
  ],
  "limit": 20
}
```

## When Adding New Features

1. **Entities**: Add to `schema/entity.py`
   - Inherit from `BaseMedicalEntity`
   - Use proper EntityType enum value
   - Include ontology IDs (UMLS, HGNC, etc.)
   - Full docstrings with examples

2. **Relationships**: Add to `schema/relationship.py`
   - Inherit from `BaseMedicalRelationship`
   - Use proper RelationType enum value
   - Evidence field is MANDATORY
   - Include domain-specific fields (e.g., response_rate for Treats)

3. **Client Methods**: Add to `client/python/client.py`
   - Use QueryBuilder pattern
   - Return typed results
   - Handle errors gracefully
   - Include docstrings with examples

4. **Tests**: Add to `tests/`
   - Test validation (especially evidence requirement)
   - Test query construction
   - Test error handling
   - Use pytest fixtures for common setups

## Documentation Standards

All public functions, classes, and modules must have docstrings:

```python
def find_treatments(disease: str, min_confidence: float = 0.7) -> list[dict]:
    """
    Find treatments for a specific disease.

    Args:
        disease: Name or ID of the disease
        min_confidence: Minimum confidence threshold (0.0-1.0)

    Returns:
        List of treatment dictionaries with evidence

    Example:
        >>> client = MedicalGraphClient("https://api.example.com")
        >>> treatments = client.find_treatments("breast cancer", min_confidence=0.8)
        >>> for t in treatments:
        ...     print(f"{t['name']}: {t['confidence']}")
    """
```

## Environment Variables

- `MEDGRAPH_SERVER`: API endpoint URL (required for client)
- `MEDGRAPH_API_KEY`: Authentication key (if required)

## Security Considerations

1. **Input Validation**: All external inputs are validated through Pydantic models
2. **SQL Injection**: Not applicable (graph database, not SQL)
3. **API Keys**: Never commit API keys or credentials
4. **Data Privacy**: PubMed/PMC data is public, but be mindful of derived data

## Performance Considerations

1. **Batch Processing**: Use tqdm for progress bars on long operations
2. **Caching**: Consider caching frequently accessed entities
3. **Query Optimization**: Use filters early, limit results appropriately
4. **Evidence Storage**: Per-paper JSON files for immutability and reproducibility

## Common Tasks

### Adding a New Entity Type

1. Add to EntityType enum in `schema/entity.py`
2. Create new class inheriting from BaseMedicalEntity
3. Add relevant ontology ID fields
4. Update tests in `tests/test_schema_entity.py`

### Adding a New Relationship Type

1. Add to RelationType enum in `schema/relationship.py`
2. Create new class inheriting from BaseMedicalRelationship
3. Ensure evidence field is present (inherited)
4. Add domain-specific fields as needed
5. Update tests in `tests/test_relationship.py`

### Adding a Client Method

1. Add method to MedicalGraphClient class
2. Use QueryBuilder internally
3. Add type hints for parameters and return values
4. Write docstring with example
5. Add tests in `tests/test_client.py`

## Resources

- **PubMed/PMC**: https://www.ncbi.nlm.nih.gov/pmc/
- **UMLS**: https://www.nlm.nih.gov/research/umls/
- **RxNorm**: https://www.nlm.nih.gov/research/umls/rxnorm/
- **HGNC**: https://www.genenames.org/
- **UniProt**: https://www.uniprot.org/

## Questions?

- Check existing code in `schema/` for patterns
- Look at tests for usage examples
- Review README.md and DESIGN_DECISIONS.md for context
