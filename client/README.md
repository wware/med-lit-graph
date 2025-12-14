# Medical Knowledge Graph Client Libraries

This directory contains client libraries for querying the medical knowledge graph API across multiple programming languages.

## Available Clients

### Python (`python/`)
Full-featured Python client with type hints and Pydantic models.

**Installation:**
```bash
pip install medical-graph-client
# Or for development:
cd client/python && pip install -e .
```

**Quick Start:**
```python
from client.python.client import MedicalGraphClient, QueryBuilder

client = MedicalGraphClient("https://api.medgraph.example.com")

# Simple convenience method
results = client.find_treatments("breast cancer", min_confidence=0.7)

# Complex query with builder
query = (QueryBuilder()
    .find_nodes("drug")
    .with_edge("treats", min_confidence=0.7)
    .filter_target("disease", name="diabetes")
    .limit(10)
    .build())

results = client.execute(query)
```

### TypeScript (`ts/`)
TypeScript client with full type definitions.

**Installation:**
```bash
npm install @medgraph/client
# Or yarn add @medgraph/client
```

### cURL (`curl/`)
Example cURL commands for direct API access.

**Usage:**
```bash
# See examples in curl/examples.sh
./client/curl/examples.sh
```

## Query Language

All clients use the same JSON-based graph query language. See **[QUERY_LANGUAGE.md](./QUERY_LANGUAGE.md)** for:
- Query language specification
- Complete examples
- How JSON queries translate to Cypher, Gremlin, and SPARQL

## Features

All client libraries support:
- ✅ **Type-safe query building** - Fluent APIs with full IDE support
- ✅ **Convenience methods** - Common queries (find_treatments, find_disease_genes, etc.)
- ✅ **Raw query execution** - Full access to the query language
- ✅ **Aggregations** - Group by and aggregate functions
- ✅ **Evidence filtering** - Filter by study type, confidence, paper count
- ✅ **Multi-hop paths** - Complex graph traversals
- ✅ **Pagination** - Limit and offset support

## Client Comparison

| Feature | Python | TypeScript | cURL |
|---------|--------|------------|------|
| Type safety | ✅ | ✅ | ❌ |
| Query builder | ✅ | ✅ | ❌ |
| Convenience methods | ✅ | ✅ | ❌ |
| Raw queries | ✅ | ✅ | ✅ |
| Async support | ❌* | ✅ | N/A |
| Best for | Scripts, notebooks | Web apps, Node.js | Testing, debugging |

*Python async client coming soon

## Authentication

All clients support API key authentication:

```python
# Python
client = MedicalGraphClient(base_url="...", api_key="your-key")
```

```typescript
// TypeScript
const client = new MedicalGraphClient({
  baseUrl: "...",
  apiKey: "your-key"
});
```

```bash
# cURL
curl -H "Authorization: Bearer your-key" \
  https://api.medgraph.example.com/api/v1/query
```

## Examples by Use Case

### Find Treatments
**Question:** "What drugs treat breast cancer?"

```python
results = client.find_treatments("breast cancer", min_confidence=0.7)
```

### Drug Mechanism of Action
**Question:** "How does metformin work?"

```python
results = client.find_drug_mechanisms("metformin")
# Returns: metformin -> inhibits -> complex I, metformin -> activates -> AMPK
```

### Differential Diagnosis
**Question:** "What diseases cause fever, fatigue, and joint pain?"

```python
results = client.search_by_symptoms(
    ["fever", "fatigue", "joint pain"],
    min_symptom_matches=2
)
```

### Evidence Comparison
**Question:** "Compare evidence quality for different diabetes treatments"

```python
results = client.compare_treatment_evidence(
    disease="type 2 diabetes",
    drugs=["metformin", "glipizide", "insulin"]
)
```

### Contradiction Detection
**Question:** "Is there conflicting evidence about drug X and disease Y?"

```python
results = client.find_contradictory_evidence(
    drug="aspirin",
    disease="heart disease"
)
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/query` | POST | Execute graph query |
| `/api/v1/health` | GET | Health check |
| `/api/v1/schema` | GET | Get schema info |

## Contributing

When adding new client libraries:

1. Implement the core query types (see Python reference)
2. Add convenience methods for common queries
3. Include comprehensive tests
4. Update this README with examples
5. Add to the comparison table

## Related Documentation

- **[QUERY_LANGUAGE.md](./QUERY_LANGUAGE.md)** - Complete query language specification
- **[../docs/DESIGN_DECISIONS.md](../docs/DESIGN_DECISIONS.md)** - Why we chose JSON over Cypher/Gremlin
- **[../tests/README.md](../tests/README.md)** - Test coverage

## Support

- **Issues:** https://github.com/wware/med-lit-graph/issues
- **Discussions:** https://github.com/wware/med-lit-graph/discussions