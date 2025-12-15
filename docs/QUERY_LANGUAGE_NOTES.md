# JSON graph query language for PostgreSQL

## Overview

The Medical Knowledge Graph uses a declarative, JSON-based query language that is translated into PostgreSQL SQL. This approach provides a database-agnostic interface while allowing for complex graph-like traversals using Recursive Common Table Expressions (CTEs).

## Core Concepts

1.  **Find Types**: What to retrieve (`nodes`, `edges`, `paths`, or `subgraph`).
2.  **Patterns**: Templates describing the graph elements to match.
3.  **Filters**: Property-based conditions (e.g., `confidence >= 0.7`).
4.  **Evidence**: Support for medical provenance and confidence scores.

## Query Structure

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug",
    "var": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.7
  },
  "filters": [
    {
      "field": "target.name",
      "operator": "eq",
      "value": "breast cancer"
    }
  ],
  "aggregate": {
    "group_by": ["drug.name"],
    "aggregations": {
      "paper_count": ["count", "treatment.evidence.paper_id"]
    }
  },
  "limit": 20
}
```

## Language Reference

### Node Patterns
Matching criteria for nodes:
- `node_type`: String (e.g., "drug", "disease").
- `name`: Exact name match.
- `name_pattern`: Regex pattern matching.
- `var`: Variable name for referencing in filters or aggregations.

### Edge Patterns
Matching criteria for relationships:
- `relation_type`: Type of relationship (e.g., "treats", "inhibits").
- `min_confidence`: Minimum confidence threshold (0.0 to 1.0).
- `direction`: "outgoing", "incoming", or "both".

### Path Patterns
Used for multi-hop queries:
- `start`: Initial Node Pattern.
- `edges`: List of (Edge Pattern, Node Pattern) pairs.
- `max_hops`: Maximum traversal depth.

## Implementation Details

The query executor translates these structures into SQL:
- **Node Queries**: Simple SELECT with JOINs between `entities` and `relationships`.
- **Path Queries**: Translated into Recursive Common Table Expressions (CTEs) for efficient graph traversal.

For full examples, see [EXAMPLES.md](../client/curl/EXAMPLES.md) or the [Python Client](../client/python/client.py).
