# Query Executor Roadmap

This document outlines the evolution of the query executor for the mini-server, showing what has been implemented and what features are planned for future phases.

## Phase 1: Basic Query Execution (Current Implementation)

**Status**: ✅ Implemented

The current implementation in `query_executor.py` supports:

### Implemented Features:
1. **Node filtering by type** - Match entities by `node_type` (e.g., "drug")
2. **Edge filtering** - Match relationships by `relation_type` and `min_confidence`
3. **Target filtering** - Apply filters to the target node (e.g., `target.name == "breast cancer"`)
4. **Basic aggregations** - Support `count` and `avg` functions
5. **Group by** - Group results by specified fields (e.g., `drug.name`)
6. **Order by** - Sort results by aggregated fields with direction (asc/desc)
7. **Limit** - Restrict number of results

### Implementation Details:
- Case-insensitive name matching for entities
- Field references like `drug.name`, `treatment.confidence`, `target.name`
- Evidence counting via `evidence_count` field in relationships
- Simple operator support (currently only `eq` for equality)

### Example Query Support:
Example 1 from `client/curl/EXAMPLES.md` is fully supported:
```json
{
  "find": "nodes",
  "node_pattern": {"node_type": "drug", "var": "drug"},
  "edge_pattern": {"relation_type": "treats", "min_confidence": 0.7},
  "filters": [
    {"field": "target.node_type", "operator": "eq", "value": "disease"},
    {"field": "target.name", "operator": "eq", "value": "breast cancer"}
  ],
  "aggregate": {
    "group_by": ["drug.name"],
    "aggregations": {
      "paper_count": ["count", "treatment.evidence.paper_id"],
      "avg_confidence": ["avg", "treatment.confidence"]
    }
  },
  "order_by": [["paper_count", "desc"], ["avg_confidence", "desc"]],
  "limit": 20
}
```

---

## Phase 2: Extended Operators and Aggregations (Future)

**Status**: 🔜 Planned

### Additional Operators:
Expand the filtering capabilities beyond simple equality:

- **in** - Field value in a list
  ```json
  {"field": "source.name", "operator": "in", "value": ["aspirin", "ibuprofen"]}
  ```

- **contains** - String contains substring (case-insensitive)
  ```json
  {"field": "disease.name", "operator": "contains", "value": "cancer"}
  ```

- **regex** - Regular expression matching
  ```json
  {"field": "drug.name", "operator": "regex", "value": ".*mab$"}
  ```

- **gt/gte/lt/lte/ne** - Numeric and string comparisons
  ```json
  {"field": "edge.confidence", "operator": "gte", "value": 0.8}
  ```

### More Aggregations:
- **sum** - Sum numeric values
- **min/max** - Minimum/maximum values
- Multiple group_by fields simultaneously
- Aggregation on nested fields (e.g., `treatment.evidence.paper_id`)

### Multi-hop Paths (Basic):
Support for simple path queries:

- Parse `path_pattern` with start node and edges array
- Traverse relationships to build paths
- Support `max_hops` parameter
- Return path structures with nodes and edges

Example:
```json
{
  "find": "paths",
  "path_pattern": {
    "start": {"node_type": "drug", "name": "metformin"},
    "edges": [
      [{"relation_type": "activates"}, {"node_type": "protein"}],
      [{"relation_type": "downregulates"}, {"node_type": "biomarker"}]
    ],
    "max_hops": 2
  }
}
```

### Field Projections:
- `return_fields` - Only return specified fields from results
- Nested field access (e.g., `gene.external_ids.hgnc`)

---

## Phase 3: Advanced Query Features (Future)

**Status**: 💡 Proposed

### Advanced Query Types:
Different result types beyond simple nodes:

- **find: "edges"** - Return relationships instead of nodes
  - Useful for exploring relationship properties
  - Returns edge details with source and target info

- **find: "paths"** - Return complete multi-hop paths
  - Already started in Phase 2, enhanced here
  - Full path objects with all intermediate nodes/edges

- **find: "subgraph"** - Return nodes and edges as a subgraph
  - Useful for visualization
  - Returns connected components

### Path Features:
- **all_paths** - Return all paths, not just one
- **shortest_path** - Find shortest path between nodes
- **avoid_cycles** - Prevent circular paths
- **Path confidence scoring** - Multiply edge confidences along path
- **Path length constraints** - Min/max path length

### Evidence Filtering:
Fine-grained filtering on evidence provenance:

- Filter by `evidence.study_type` (e.g., only RCTs)
  ```json
  {"field": "edge.evidence.study_type", "operator": "eq", "value": "rct"}
  ```

- Filter by `evidence.sample_size`
  ```json
  {"field": "edge.evidence.sample_size", "operator": "gte", "value": 100}
  ```

- Filter by `evidence.paper_id`
  ```json
  {"field": "edge.evidence.paper_id", "operator": "in", "value": ["PMC123456", "PMC234567"]}
  ```

- Aggregate evidence across papers
  - Count unique papers supporting a relationship
  - Average confidence across different studies

### Optimization:
Performance improvements for larger datasets:

- **Index entities by type** - Faster lookups for node_type filters
- **Cache parsed queries** - Avoid re-parsing identical queries
- **Parallel aggregation** - Process groups concurrently for large result sets
- **Query planning** - Optimize execution order for complex multi-hop queries
- **Early termination** - Stop after finding N results if limit is specified

### Testing:
Comprehensive test coverage:

- Unit tests for each operator (eq, in, contains, regex, gt, gte, lt, lte, ne)
- Integration tests for Examples 2-22 from EXAMPLES.md
- Performance tests with larger synthetic datasets (1000+ entities, 10000+ relationships)
- Edge cases:
  - Empty results
  - Malformed queries
  - Invalid field references
  - Missing required fields
  - Cycles in path queries

---

## Implementation Strategy

### Phase 1 → Phase 2 Transition:
1. Add operator support incrementally (start with `in` and `contains`)
2. Refactor filter matching into pluggable operator system
3. Add basic path traversal (single hop → multi-hop)
4. Extend aggregation functions (sum, min, max)
5. Add field projection support

### Phase 2 → Phase 3 Transition:
1. Implement alternative query types (edges, subgraph)
2. Add evidence-level filtering
3. Implement path algorithms (shortest path, all paths)
4. Add indexing for performance
5. Build comprehensive test suite

### Development Principles:
- **Incremental development** - Add one feature at a time
- **Test-driven** - Write tests for each new feature
- **Backward compatible** - Don't break existing queries
- **Well-documented** - Update this roadmap as features are added
- **Keep it simple** - This is for development/testing, not production scale

---

## Future Considerations

### Beyond Phase 3:
- **Parameterized queries** - Support query templates with parameters
- **Query composition** - Combine multiple queries (UNION, INTERSECT)
- **Temporal queries** - Filter by publication date or evidence recency
- **Semantic search** - Use embeddings for similarity-based queries
- **Query optimization** - Cost-based query planning for complex queries
- **Streaming results** - Return results as they're computed for large result sets

---

## Notes

- This roadmap is a living document - update as implementation progresses
- Prioritize features based on actual usage in EXAMPLES.md
- Keep the implementation simple and readable - performance is secondary
- Focus on correctness over optimization (dataset is small for development)
