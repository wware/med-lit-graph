# TODO and Development Roadmap

This file tracks implementation status and next steps for the medical knowledge graph project.

## ✅ Completed (Phase 1)

### Query Executor
- [x] Basic query execution for `find:  "nodes"` queries
- [x] Node filtering by entity type
- [x] Edge filtering by relation_type and min_confidence
- [x] Target filtering with field references (target. name, target.node_type)
- [x] Aggregations:  count, avg
- [x] Group by single field
- [x] Order by with direction (asc/desc)
- [x] Result limiting

### Testing
- [x] Integration test for Example 1 passing
- [x] Test framework gracefully handles unimplemented features
- [x] Expected responses documented for all examples

### Documentation
- [x] Query language specification (QUERY_LANGUAGE.md)
- [x] Complete curl examples (EXAMPLES.md)
- [x] Phase 2/3 roadmap (tests/mini_server/QUERY_EXECUTOR_ROADMAP.md)

## 🔜 Phase 2: Extended Query Features (Next Priority)

### Additional Operators
- [ ] `in` - Field value in a list
- [ ] `contains` - String contains substring (case-insensitive)
- [ ] `regex` - Regular expression matching
- [ ] `gt/gte/lt/lte/ne` - Numeric and string comparisons

### Multi-hop Path Queries
- [ ] Parse `path_pattern` with start node and edges array
- [ ] Traverse relationships to build paths
- [ ] Support `max_hops` parameter
- [ ] Support `avoid_cycles`
- [ ] Return path structures with nodes and edges
- [ ] **Enables**:  Examples 3, 4, 11, 13, 15, 24, 26

### Edge Queries
- [ ] `find:  "edges"` - Return relationships instead of nodes
- [ ] Edge-specific return fields
- [ ] **Enables**: Example 23

### More Aggregations
- [ ] `sum` - Sum numeric values
- [ ] `min/max` - Minimum/maximum values
- [ ] Multiple group_by fields
- [ ] **Enables**: Example 5, 25

### Field Projections
- [ ] `return_fields` - Only return specified fields
- [ ] Nested field access (e.g., `gene.external_ids.hgnc`)

## 💡 Phase 3: Advanced Features (Future)

### Evidence Filtering
- [ ] Filter by `evidence. study_type` (e.g., only RCTs)
- [ ] Filter by `evidence.sample_size`
- [ ] Filter by `evidence.paper_id`
- [ ] Aggregate evidence across papers

### Advanced Query Types
- [ ] `find: "subgraph"` - Return nodes and edges as subgraph
- [ ] Path confidence scoring (multiply edge confidences)
- [ ] Shortest path algorithms
- [ ] All paths between nodes

### Performance Optimization
- [ ] Index entities by type for faster lookups
- [ ] Cache parsed queries
- [ ] Parallel aggregation for large result sets
- [ ] Query planning for complex multi-hop queries

### New Entity Types (PR #3 additions)
- [ ] Hypothesis entities and tracking
- [ ] Study design entities (OBI-based)
- [ ] Statistical method entities (STATO-based)
- [ ] Evidence line entities (SEPIO-based)
- [ ] **Enables**: Examples 13, 14, 15

## 📊 Examples Status

| Example | Feature Required | Status |
|---------|-----------------|--------|
| 1 | Basic nodes + aggregation | ✅ Implemented |
| 2 | Basic nodes + filtering | ✅ Implemented (same as 1) |
| 3 | Multi-hop paths | ⏳ Phase 2 |
| 4 | Multi-hop paths | ⏳ Phase 2 |
| 5 | Aggregations (count complex) | ⏳ Phase 2 |
| 6 | Aggregations by relation_type | ✅ Implemented |
| 7 | Multi-hop paths | ⏳ Phase 2 |
| 8 | Basic nodes | ✅ Implemented |
| 9 | Edge filtering by date | ⏳ Phase 2 |
| 10 | Edge filtering | ⏳ Phase 2 |
| 11 | Multi-hop paths | ⏳ Phase 2 |
| 12 | Basic nodes | ✅ Implemented |
| 13 | Hypothesis entities + paths | ⏳ Phase 3 |
| 14 | Study design filtering | ⏳ Phase 3 |
| 15 | Statistical methods | ⏳ Phase 3 |
| 23 | Edge queries | ⏳ Phase 2 |
| 24 | Multi-hop paths | ⏳ Phase 2 |
| 25 | Paper filtering | ⏳ Phase 2 |
| 26 | Multi-hop paths | ⏳ Phase 2 |

## 🧪 Testing Notes

The integration test (`test_query_execution` in `tests/test_curl_examples.py`) automatically skips validation for Phase 2/3 features:

- Queries with `path_pattern` (multi-hop)
- Queries with `find: "edges"`
- Queries with `hypothesis` entities

Expected responses are documented for ALL examples in EXAMPLES.md, serving as specifications for future implementation.

## 📝 Documentation Files

- **README.md** - Project overview and getting started
- **QUERY_LANGUAGE.md** - Complete query language specification
- **EXAMPLES.md** - All curl examples with expected responses
- **tests/mini_server/QUERY_EXECUTOR_ROADMAP.md** - Detailed Phase 2/3 implementation notes
- **DESIGN_DECISIONS.md** - Architecture decisions and rationale

## 🚀 Getting Started with Phase 2

To implement Phase 2 features:

1. Pick a feature from the Phase 2 list above
2. Review `tests/mini_server/QUERY_EXECUTOR_ROADMAP.md` for implementation details
3. Update `tests/mini_server/query_executor.py`
4. Run tests: `uv run pytest tests/test_curl_examples.py`
5. Update this TODO.md to mark items complete
