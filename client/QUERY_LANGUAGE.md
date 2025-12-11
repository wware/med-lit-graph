# Medical Knowledge Graph Query Language

## Overview

This document describes the JSON-based graph query language used to query the medical knowledge graph. The language is designed to be:

- **Declarative**: Describe what you want, not how to get it
- **JSON-based**: Easy to generate programmatically and use with LLMs
- **Database-agnostic**: Translates to openCypher (Neptune), Cypher (Neo4j), or Gremlin
- **Evidence-aware**: First-class support for provenance and confidence scoring
- **Composable**: Build complex queries from simple patterns

## Core Concepts

The query language is built around these key concepts:

1. **Find Type**: What you're looking for (`nodes`, `edges`, `paths`, or `subgraph`)
2. **Patterns**: Templates that describe graph elements to match
3. **Filters**: Conditions to narrow results
4. **Aggregations**: Group and summarize data
5. **Evidence**: Every medical relationship includes provenance

## Basic Query Structure

```json
{
  "find": "nodes",
  "node_pattern": { ... },
  "edge_pattern": { ... },
  "filters": [ ... ],
  "aggregate": { ... },
  "order_by": [ ... ],
  "limit": 20,
  "offset": 0,
  "return_fields": [ ... ]
}
```

## Find Types

### 1. Find Nodes

Returns nodes matching the pattern.

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug",
    "var": "d"
  }
}
```

### 2. Find Edges

Returns relationships/edges matching the pattern.

```json
{
  "find": "edges",
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.7
  }
}
```

### 3. Find Paths

Returns multi-hop paths through the graph.

```json
{
  "find": "paths",
  "path_pattern": {
    "start": {"node_type": "drug", "name": "metformin"},
    "edges": [
      {
        "edge": {"relation_type": "inhibits"},
        "node": {"node_type": "protein"}
      }
    ]
  }
}
```

### 4. Find Subgraph

Returns a subgraph containing all matching nodes and edges.

```json
{
  "find": "subgraph",
  "filters": [
    {"field": "node.node_type", "operator": "in", "value": ["drug", "disease"]}
  ]
}
```

## Pattern Types

### NodePattern

Matches nodes in the graph.

**Fields:**
- `node_type`: Single entity type (e.g., `"drug"`, `"disease"`)
- `node_types`: Multiple entity types (e.g., `["test", "biomarker"]`)
- `id`: Specific node ID
- `name`: Exact name match
- `name_pattern`: Regex pattern for name
- `properties`: Property values to match
- `property_filters`: List of PropertyFilter objects
- `external_id`: External identifiers (e.g., `{"rxnorm": "1187832"}`)
- `var`: Variable name for referencing (default: `"n"`)

**Example:**
```json
{
  "node_type": "disease",
  "name": "breast cancer",
  "var": "disease"
}
```

**Example with pattern matching:**
```json
{
  "node_type": "gene",
  "name_pattern": ".*BRCA.*",
  "var": "gene"
}
```

**Example with multiple types:**
```json
{
  "node_types": ["test", "biomarker"],
  "var": "diagnostic"
}
```

### EdgePattern

Matches relationships between nodes.

**Fields:**
- `relation_type`: Single relationship type (e.g., `"treats"`)
- `relation_types`: Multiple relationship types (e.g., `["treats", "manages"]`)
- `direction`: `"outgoing"` (default), `"incoming"`, or `"both"`
- `min_confidence`: Minimum confidence score (0.0-1.0)
- `property_filters`: List of PropertyFilter objects
- `require_evidence_from`: Require evidence from specific papers
- `min_evidence_count`: Minimum number of supporting evidence items
- `var`: Variable name for referencing (default: `"r"`)

**Example:**
```json
{
  "relation_type": "treats",
  "direction": "outgoing",
  "min_confidence": 0.7,
  "var": "treatment"
}
```

**Example with multiple relation types:**
```json
{
  "relation_types": ["associated_with", "causes", "increases_risk"],
  "direction": "incoming",
  "min_confidence": 0.6
}
```

**Example requiring specific evidence:**
```json
{
  "relation_type": "treats",
  "min_confidence": 0.8,
  "min_evidence_count": 3,
  "require_evidence_from": ["PMC12345", "PMC67890"]
}
```

### PathPattern

Matches multi-hop paths through the graph.

**Fields:**
- `start`: NodePattern for the starting node
- `edges`: Array of path steps, each containing `{edge: EdgePattern, node: NodePattern}`
- `max_hops`: Maximum path length
- `avoid_cycles`: Don't revisit nodes (default: false)
- `shortest_path`: Return only shortest paths (default: false)
- `all_paths`: Return all paths, not just one (default: false)

**Example - Drug mechanism of action:**
```json
{
  "start": {
    "node_type": "drug",
    "name": "metformin",
    "var": "drug"
  },
  "edges": [
    {
      "edge": {
        "relation_types": ["binds_to", "inhibits", "activates"],
        "var": "interaction"
      },
      "node": {
        "node_types": ["protein", "gene"],
        "var": "target"
      }
    }
  ],
  "max_hops": 1
}
```

**Example - Multi-hop drug repurposing:**
```json
{
  "start": {
    "node_type": "disease",
    "name": "Alzheimer disease"
  },
  "edges": [
    {
      "edge": {"relation_type": "associated_with"},
      "node": {"node_type": "gene"}
    },
    {
      "edge": {"relation_type": "encodes"},
      "node": {"node_type": "protein"}
    },
    {
      "edge": {
        "relation_types": ["binds_to", "inhibits"],
        "direction": "incoming"
      },
      "node": {"node_type": "drug"}
    }
  ],
  "max_hops": 3,
  "avoid_cycles": true
}
```

### PropertyFilter

Filters based on property values.

**Fields:**
- `field`: Dot-notation path to field (e.g., `"drug.name"`, `"rel.confidence"`)
- `operator`: Comparison operator
- `value`: Value to compare against

**Operators:**
- `eq`: Equal to
- `ne`: Not equal to
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `in`: Value in list
- `contains`: String contains (case-insensitive)
- `regex`: Regular expression match

**Examples:**
```json
{"field": "drug.name", "operator": "eq", "value": "aspirin"}
```

```json
{"field": "disease.name", "operator": "contains", "value": "cancer"}
```

```json
{"field": "rel.confidence", "operator": "gte", "value": 0.8}
```

```json
{"field": "source.name", "operator": "in", "value": ["aspirin", "ibuprofen"]}
```

```json
{"field": "gene.name", "operator": "regex", "value": ".*BRCA[12].*"}
```

## Aggregations

Group and summarize results.

**Structure:**
```json
{
  "group_by": ["field1", "field2"],
  "aggregations": {
    "result_name": ["function", "field"]
  }
}
```

**Aggregation Functions:**
- `count`: Count items
- `sum`: Sum numeric values
- `avg`: Average numeric values
- `min`: Minimum value
- `max`: Maximum value

**Example - Count papers per drug:**
```json
{
  "group_by": ["drug.name"],
  "aggregations": {
    "paper_count": ["count", "rel.evidence.paper_id"],
    "avg_confidence": ["avg", "rel.confidence"]
  }
}
```

**Example - Find diseases with most genes:**
```json
{
  "group_by": ["disease.name"],
  "aggregations": {
    "gene_count": ["count", "gene.name"],
    "total_papers": ["count", "rel.evidence.paper_id"],
    "avg_confidence": ["avg", "rel.confidence"]
  }
}
```

## Complete Query Examples

### Example 1: Find Treatments for a Disease

Find drugs that treat breast cancer with high confidence.

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug",
    "var": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "direction": "outgoing",
    "min_confidence": 0.7,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "target.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "breast cancer"
    }
  ],
  "aggregate": {
    "group_by": ["drug.name"],
    "aggregations": {
      "paper_count": ["count", "treatment.evidence.paper_id"],
      "avg_confidence": ["avg", "treatment.confidence"]
    }
  },
  "order_by": [
    ["paper_count", "desc"],
    ["avg_confidence", "desc"]
  ],
  "limit": 20
}
```

### Example 2: Find Genes Associated with Disease

Find genes linked to Alzheimer's disease.

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "gene",
    "var": "gene"
  },
  "edge_pattern": {
    "relation_types": ["associated_with", "causes", "increases_risk"],
    "direction": "incoming",
    "min_confidence": 0.6,
    "var": "association"
  },
  "filters": [
    {
      "field": "source.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "source.name",
      "operator": "eq",
      "value": "Alzheimer disease"
    }
  ],
  "return_fields": [
    "gene.name",
    "gene.external_ids.hgnc",
    "association.relation_type",
    "association.confidence",
    "association.evidence.paper_id"
  ],
  "order_by": [["association.confidence", "desc"]],
  "limit": 50
}
```

### Example 3: Drug Mechanism of Action (Multi-Hop)

How does metformin affect glucose metabolism?

```json
{
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
    "avoid_cycles": true
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
```

### Example 4: Differential Diagnosis from Symptoms

What diseases present with fatigue, joint pain, and butterfly rash?

```json
{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "symptom",
      "name": ["fatigue", "joint pain", "butterfly rash"],
      "var": "symptom"
    },
    "edges": [
      {
        "edge": {
          "relation_type": "symptom_of",
          "direction": "outgoing",
          "var": "symptom_disease"
        },
        "node": {
          "node_type": "disease",
          "var": "disease"
        }
      }
    ],
    "max_hops": 1
  },
  "aggregate": {
    "group_by": ["disease.name"],
    "aggregations": {
      "symptom_count": ["count", "symptom.name"],
      "specificity_score": ["avg", "symptom_disease.confidence"],
      "supporting_papers": ["count", "symptom_disease.evidence.paper_id"]
    }
  },
  "order_by": [
    ["symptom_count", "desc"],
    ["specificity_score", "desc"]
  ]
}
```

### Example 5: Compare Treatment Evidence Quality

Compare statins vs PCSK9 inhibitors for cholesterol.

```json
{
  "find": "edges",
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.5,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "source.node_type",
      "operator": "eq",
      "value": "drug"
    },
    {
      "field": "source.name",
      "operator": "in",
      "value": ["atorvastatin", "simvastatin", "evolocumab", "alirocumab"]
    },
    {
      "field": "target.name_pattern",
      "operator": "regex",
      "value": ".*(hypercholesterolemia|high cholesterol).*"
    }
  ],
  "aggregate": {
    "group_by": ["source.name", "target.name"],
    "aggregations": {
      "total_papers": ["count", "treatment.evidence.paper_id"],
      "rct_count": ["count", "treatment.evidence[study_type='rct'].paper_id"],
      "avg_confidence": ["avg", "treatment.confidence"],
      "avg_sample_size": ["avg", "treatment.evidence.sample_size"]
    }
  },
  "order_by": [
    ["rct_count", "desc"],
    ["avg_confidence", "desc"]
  ]
}
```

### Example 6: Find Diagnostic Tests

What tests diagnose systemic lupus erythematosus?

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_types": ["test", "biomarker"],
    "var": "diagnostic"
  },
  "edge_pattern": {
    "relation_types": ["diagnoses", "indicates"],
    "direction": "outgoing",
    "min_confidence": 0.6,
    "var": "diagnostic_rel"
  },
  "filters": [
    {
      "field": "target.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "systemic lupus erythematosus"
    }
  ],
  "aggregate": {
    "group_by": ["diagnostic.name", "diagnostic.node_type"],
    "aggregations": {
      "paper_count": ["count", "diagnostic_rel.evidence.paper_id"],
      "avg_confidence": ["avg", "diagnostic_rel.confidence"]
    }
  },
  "return_fields": [
    "diagnostic.name",
    "diagnostic.node_type",
    "paper_count",
    "avg_confidence"
  ],
  "order_by": [
    ["avg_confidence", "desc"]
  ]
}
```

### Example 7: Identify Contradictory Evidence

Are there conflicting studies about aspirin and heart attacks?

```json
{
  "find": "edges",
  "edge_pattern": {
    "relation_types": ["prevents", "increases_risk", "decreases_risk", "associated_with"],
    "var": "relationship"
  },
  "filters": [
    {
      "field": "source.name",
      "operator": "eq",
      "value": "aspirin"
    },
    {
      "field": "target.name_pattern",
      "operator": "regex",
      "value": ".*(heart attack|myocardial infarction|MI).*"
    }
  ],
  "aggregate": {
    "group_by": ["relationship.relation_type"],
    "aggregations": {
      "paper_count": ["count", "relationship.evidence.paper_id"],
      "avg_confidence": ["avg", "relationship.confidence"],
      "avg_sample_size": ["avg", "relationship.evidence.sample_size"]
    }
  },
  "order_by": [["relationship.relation_type", "asc"]]
}
```

## Field References

### Node Field References

When referencing node fields in filters, aggregations, or return_fields:

- `n.name` - Node name (or use variable name like `drug.name`)
- `n.node_type` - Entity type
- `n.id` - Internal node ID
- `n.external_ids.rxnorm` - External identifier
- `n.properties.fda_approved` - Custom property

### Edge Field References

When referencing edge fields:

- `r.relation_type` - Type of relationship (or use variable name like `treatment.relation_type`)
- `r.confidence` - Confidence score (0.0-1.0)
- `r.evidence` - Array of evidence objects
- `r.evidence.paper_id` - Paper identifiers
- `r.evidence.study_type` - Study type (rct, meta_analysis, etc.)
- `r.evidence.sample_size` - Study sample size
- `r.source_papers` - List of source paper IDs
- `r.contradicted_by` - Papers with contradictory evidence

### Special Field References

- `target.*` - Target node in edge pattern queries
- `source.*` - Source node in edge pattern queries
- `incoming_edges[...]` - Incoming relationships
- `outgoing_edges[...]` - Outgoing relationships

## Entity Types

**Medical Entities:**
- `disease` - Diseases and conditions
- `symptom` - Symptoms and signs
- `drug` - Drugs and medications
- `gene` - Genes
- `protein` - Proteins
- `anatomical_structure` - Anatomical structures
- `procedure` - Medical procedures
- `test` - Diagnostic tests
- `biomarker` - Biomarkers
- `measurement` - Measurements

**Research Entities:**
- `paper` - Research papers
- `author` - Authors
- `institution` - Institutions
- `clinical_trial` - Clinical trials

## Relationship Types

**Causal:**
- `causes` - Direct causation
- `prevents` - Prevention
- `increases_risk` - Increases risk
- `decreases_risk` - Decreases risk

**Treatment:**
- `treats` - Treatment relationship
- `manages` - Disease management
- `contraindicates` - Contraindication
- `side_effect` - Side effect

**Biological:**
- `encodes` - Gene encodes protein
- `binds_to` - Molecular binding
- `inhibits` - Inhibition
- `activates` - Activation
- `upregulates` - Upregulation
- `downregulates` - Downregulation
- `metabolizes` - Metabolism

**Clinical:**
- `diagnoses` - Diagnostic relationship
- `indicates` - Indication
- `precedes` - Temporal precedence
- `co_occurs_with` - Co-occurrence
- `associated_with` - General association
- `symptom_of` - Symptom relationship
- `affects` - Affects relationship
- `located_in` - Location

**Provenance:**
- `authored_by` - Authorship
- `cites` - Citation
- `contradicts` - Contradiction
- `supports` - Support

## Pagination

Use `limit` and `offset` for pagination:

```json
{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "limit": 20,
  "offset": 0
}
```

Page 2:
```json
{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "limit": 20,
  "offset": 20
}
```

## Best Practices

### 1. Use Confidence Thresholds

Always filter by evidence quality for medical queries:

```json
{
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.7
  }
}
```

### 2. Filter by Study Type

For high-quality evidence, filter by study type:

```json
{
  "filters": [
    {
      "field": "rel.evidence.study_type",
      "operator": "in",
      "value": ["rct", "meta_analysis"]
    }
  ]
}
```

### 3. Use Aggregations

Aggregate to summarize evidence across papers:

```json
{
  "aggregate": {
    "group_by": ["drug.name"],
    "aggregations": {
      "paper_count": ["count", "rel.evidence.paper_id"],
      "rct_count": ["count", "rel.evidence[study_type='rct'].paper_id"],
      "avg_confidence": ["avg", "rel.confidence"]
    }
  }
}
```

### 4. Return Only Needed Fields

Use `return_fields` to reduce response size:

```json
{
  "return_fields": [
    "drug.name",
    "rel.confidence",
    "rel.evidence.paper_id"
  ]
}
```

### 5. Use Meaningful Variable Names

Use descriptive variable names instead of generic ones:

```json
{
  "node_pattern": {"node_type": "drug", "var": "drug"},
  "edge_pattern": {"relation_type": "treats", "var": "treatment"}
}
```

## Query Translation

The JSON query language translates to native graph query languages including Cypher (Neo4j), openCypher (Neptune), and Gremlin. Here are two examples to illustrate the translation:

### Example 1: Simple Node Query

**JSON Query:**
```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug",
    "var": "drug"
  },
  "filters": [
    {
      "field": "drug.name",
      "operator": "contains",
      "value": "metformin"
    }
  ],
  "limit": 10
}
```

**Translates to Cypher (Neo4j) / openCypher (Neptune):**
```cypher
MATCH (drug:Drug)
WHERE drug.name CONTAINS 'metformin'
RETURN drug
LIMIT 10
```

**Translates to Gremlin:**
```groovy
g.V().hasLabel('Drug')
  .has('name', containing('metformin'))
  .limit(10)
```

### Example 2: Query with Edge Pattern

**JSON Query:**
```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug",
    "var": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "direction": "outgoing",
    "min_confidence": 0.7,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "target.name",
      "operator": "eq",
      "value": "diabetes"
    }
  ]
}
```

**Translates to Cypher:**
```cypher
MATCH (drug:Drug)-[treatment:TREATS]->(target)
WHERE treatment.confidence >= 0.7
  AND target.name = 'diabetes'
RETURN drug
```

**Translates to Gremlin:**
```groovy
g.V().hasLabel('Drug').as('drug')
  .outE('TREATS').has('confidence', gte(0.7))
  .inV().has('name', 'diabetes')
  .select('drug')
```

The translation layer handles the complexity of mapping JSON patterns to each database's native query syntax, allowing you to write queries once and target multiple graph databases.

## Query Validation

All queries are validated before execution. Common validation errors:

1. **Missing required fields**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "field 'find' is required"
}
```

2. **Invalid field**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid field: node_pattern.invalid_field"
}
```

3. **Type mismatch**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "field 'min_confidence' must be a number between 0 and 1"
}
```

## Client Libraries

### Python

```python
from medgraph import MedicalGraphClient, QueryBuilder, EntityType, RelationType

client = MedicalGraphClient("https://api.medgraph.com")

# Using QueryBuilder
query = (QueryBuilder()
    .find_nodes(EntityType.DRUG)
    .with_edge(RelationType.TREATS, min_confidence=0.7)
    .filter_target(EntityType.DISEASE, name="diabetes")
    .aggregate(
        ["drug.name"],
        paper_count=("count", "rel.evidence.paper_id"),
        avg_confidence=("avg", "rel.confidence")
    )
    .order_by("paper_count", "desc")
    .limit(20)
    .build())

results = client.execute(query)
```

### TypeScript

```typescript
import { MedicalGraphClient, QueryBuilder, EntityType, RelationType } from '@medgraph/client';

const client = new MedicalGraphClient('https://api.medgraph.com');

const query = new QueryBuilder()
  .findNodes(EntityType.DRUG)
  .withEdge(RelationType.TREATS, { minConfidence: 0.7 })
  .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
  .aggregate(
    ['drug.name'],
    {
      paper_count: ['count', 'rel.evidence.paper_id'],
      avg_confidence: ['avg', 'rel.confidence']
    }
  )
  .orderBy('paper_count', 'desc')
  .limit(20)
  .build();

const results = await client.execute(query);
```

### curl

See [curl/EXAMPLES.md](curl/EXAMPLES.md) for complete curl examples.

## Additional Resources

- [Python Client Documentation](python/README.md)
- [TypeScript Client Documentation](ts/README.md)
- [curl Examples](curl/EXAMPLES.md)
- [Schema Documentation](../schema/README.md)
- [API Reference](../README.md)

---

**Last Updated**: 2025-12-10
**Version**: 2.0.0
**Maintainer**: Medical Knowledge Graph Team
