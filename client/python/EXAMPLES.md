# Python Client Examples

This document provides examples of how to query the medical knowledge graph using the Python client library. It mirrors the structure of the [Query Language Documentation](../QUERY_LANGUAGE.md).

## Setup

```python
import os
from client import MedicalGraphClient, QueryBuilder, EntityType, PredicateType

# Initialize client
client = MedicalGraphClient(
    base_url=os.getenv("MEDGRAPH_SERVER", "https://api.medgraph.example.com"),
    api_key="your-api-key"
)
```

## Example 1: Find Treatments for a Disease

**Find drugs that treat breast cancer with high confidence:**

```python
results = client.find_treatments("breast cancer", min_confidence=0.7)

# OR using QueryBuilder for more control:
query = (
    QueryBuilder()
    .find_nodes(EntityType.DRUG)
    .with_edge(PredicateType.TREATS, direction="outgoing", min_confidence=0.7, var="treatment")
    .filter_target(EntityType.DISEASE, name="breast cancer")
    .aggregate(
        group_by=["drug.name"],
        paper_count=("count", "treatment.evidence.paper_id"),
        avg_confidence=("avg", "treatment.confidence")
    )
    .order_by("paper_count", "desc")
    .limit(20)
    .build()
)
results = client.execute(query)
```

## Example 2: Find Genes Associated with Disease

**Find genes linked to Alzheimer's disease:**

```python
query = (
    QueryBuilder()
    .find_nodes(EntityType.GENE)
    .with_edge(
        [PredicateType.ASSOCIATED_WITH, PredicateType.CAUSES, PredicateType.INCREASES_RISK],
        direction="incoming", 
        min_confidence=0.6,
        var="association"
    )
    .filter_target(EntityType.DISEASE, name="Alzheimer disease")
    .return_fields(
        "gene.name",
        "gene.external_ids.hgnc",
        "association.relation_type",
        "association.confidence",
        "association.evidence.paper_id"
    )
    .order_by("association.confidence", "desc")
    .limit(50)
    .build()
)

results = client.execute(query)
```

## Example 3: Drug Mechanism of Action (Multi-Hop)

**How does metformin affect glucose metabolism?**

```python
# Multi-hop queries currently require the execute_raw method or constructing a GraphQuery object manually 
# if the builder doesn't fully support complex paths yet. 
# Here is how to do it with a raw dictionary for maximum flexibility:

query = {
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "name": "metformin",
      "var": "drug"
    },
    "edges": [
      {
        "edge": {
          "relation_types": ["binds_to", "inhibits", "activates"],
          "var": "drug_target"
        },
        "node": {
          "node_types": ["protein", "gene"],
          "var": "target"
        }
      },
      {
        "edge": {
          "relation_types": ["inhibits", "activates", "upregulates", "downregulates"],
          "var": "target_effect"
        },
        "node": {
          "node_type": "biomarker",
          "var": "biomarker"
        }
      }
    ],
    "max_hops": 2,
    "avoid_cycles": True
  },
  "filters": [
    {
      "field": "biomarker.name_pattern",
      "operator": "regex",
      "value": ".*(glucose|blood sugar|glyc).*"
    }
  ],
  "return_fields": [
    "drug.name",
    "target.name",
    "target.node_type",
    "drug_target.relation_type",
    "biomarker.name",
    "target_effect.relation_type"
  ]
}

results = client.execute_raw(query)
```

## Example 4: Compare Treatment Evidence Quality

**Compare statins vs PCSK9 inhibitors for cholesterol:**

```python
query = (
    QueryBuilder()
    .find_edges(PredicateType.TREATS, var="treatment")
    .filter("treatment.confidence", "gte", 0.5)
    .filter("source.node_type", "eq", "drug")
    .filter("source.name", "in", ["atorvastatin", "simvastatin", "evolocumab", "alirocumab"])
    .filter("target.name_pattern", "regex", ".*(hypercholesterolemia|high cholesterol).*")
    .aggregate(
        group_by=["source.name", "target.name"],
        total_papers=("count", "treatment.evidence.paper_id"),
        rct_count=("count", "treatment.evidence[study_type='rct'].paper_id"),
        avg_confidence=("avg", "treatment.confidence"),
        avg_sample_size=("avg", "treatment.evidence.sample_size")
    )
    .order_by("rct_count", "desc")
    .build()
)

results = client.execute(query)
```

## Example 5: Batch Queries

**Execute multiple queries in parallel:**

```python
query1 = (
    QueryBuilder()
    .find_nodes(EntityType.DRUG)
    .with_edge(PredicateType.TREATS)
    .filter_target(EntityType.DISEASE, name="diabetes")
    .limit(10)
    .build()
)

query2 = (
    QueryBuilder()
    .find_nodes(EntityType.GENE)
    .with_edge(PredicateType.ASSOCIATED_WITH, direction="incoming")
    .filter_target(EntityType.DISEASE, name="diabetes")
    .limit(10)
    .build()
)

# Pass a list of dictionaries with 'id' and 'query'
results = client.batch([
    {"id": "treatments", "query": query1},
    {"id": "genes", "query": query2}
])

print("Treatments:", results["treatments"])
print("Genes:", results["genes"])
```

## Example 6: Pagination

**Retrieve results in pages:**

```python
def get_all_drugs(offset=0, limit=20):
    query = (
        QueryBuilder()
        .find_nodes("drug")
        .limit(limit)
        .offset(offset)
        .build()
    )
    return client.execute(query)

# Fetch first page
page1 = get_all_drugs(0)

# Fetch second page
page2 = get_all_drugs(20)
```
