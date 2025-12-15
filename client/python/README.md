# Medical Knowledge Graph Python Client

The `MedicalGraphClient` provides a high-level Python interface for querying the Medical Knowledge Graph. It supports both high-level convenience methods for common medical queries and a powerful `QueryBuilder` for complex, multi-hop graph traversals.

## Installation

```bash
# From the project root
pip install -e client/python
```

## Quick Start

```python
import os
from client.python.client import MedicalGraphClient

# Initialize the client (uses MEDGRAPH_SERVER env var by default)
client = MedicalGraphClient(os.getenv("MEDGRAPH_SERVER", "http://localhost:8000"))

# Basic query: Find drugs that treat a disease
results = client.find_treatments("breast cancer")

for drug in results:
    print(f"Drug: {drug['name']}, Confidence: {drug['confidence']}")
```

## Features

- **Entity Discovery**: Find diseases, genes, drugs, and more by name or criteria.
- **Relationship Traversal**: Explore connections between medical entities with provenance.
- **Provenance-First**: Every relationship includes direct evidence quotes and paper citations.
- **Query Builder**: Construct complex JSON-based queries with a fluent Python API.
- **Type Safety**: Uses Pydantic models for request validation and response handling.

## Using the Query Builder

For more complex queries, use the `QueryBuilder`:

```python
from client.python.client import MedicalGraphClient, QueryBuilder, EntityType, PredicateType

client = MedicalGraphClient()

# Find genes associated with a disease that are targeted by FDA-approved drugs
query = (QueryBuilder()
    .find_nodes(EntityType.GENE)
    .filter(name="BRCA1")
    .with_edge(PredicateType.ASSOCIATED_WITH)
    .filter_target(EntityType.DISEASE, name="breast cancer")
    .build())

results = client.execute(query)
```

## API Reference

### `MedicalGraphClient`

- `find_entities(name, entity_type=None)`
- `find_treatments(disease_name)`
- `find_drug_mechanisms(drug_name)`
- `find_gene_associations(gene_name)`
- `execute(query)`

### `QueryBuilder`

See [QUERY_LANGUAGE.md](../QUERY_LANGUAGE.md) for a full specification of the query language capabilities.
For more detailed examples, see [EXAMPLES.md](EXAMPLES.md).

## Requirements

- Python 3.9+
- `pydantic`
- `requests`
- `httpx` (for async support)
