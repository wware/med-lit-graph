# Tests for med-lit-graph

This directory contains the test suite for the medical literature knowledge graph project.  The tests validate core functionality across multiple layers of the system.

## Test Coverage

### Core Components Tested

1. **Schema & Data Models** (`test_schema_entity.py`, `test_relationship.py`)
   - Entity models (Disease, Gene, Drug) with validation
   - Relationship types (Treats, Causes, Cites)
   - Entity collections with CRUD operations
   - Embedding generation and similarity search

2. **Provenance Enforcement** (`test_provenance_enforcement.py`) **NEW**
   - Evidence requirements and validation
   - Confidence score bounds checking
   - Lightweight vs. rich provenance support
   - Multiple evidence aggregation
   - Contradictory evidence tracking

3. **Client Library** (`test_client.py`, `test_query_engine.py`, `test_integration_client.py`)
   - `MedicalGraphClient` API methods
   - `QueryBuilder` fluent interface
   - Query serialization and execution
   - Convenience methods (e.g., `find_treatments`)

4. **Query Language Completeness** (`test_query_completeness.py`) **NEW**
   - All 7 documented examples from QUERY_LANGUAGE.md
   - Query serialization and JSON roundtrips
   - Property filters and operators
   - Aggregations and pagination
   - Special characters and unicode handling

5. **Client Error Handling** (`test_client_error_handling.py`) **NEW**
   - HTTP error responses (400, 401, 404, 429, 500, 503)
   - Network errors (timeout, connection failure, DNS)
   - Malformed responses
   - Empty responses
   - Serialization errors

6. **MCP Server** (`test_mcp_server.py`)
   - Tool listing and initialization
   - Search result formatting
   - OpenSearch integration setup

## What We've Proven (When All Tests Pass)

### ✅ **Data Model Integrity**
- Entity types (Disease, Gene, Drug) properly validate and store metadata
- Relationships between entities are correctly typed and instantiated
- Collections can add, retrieve, and persist entities to disk
- Embedding-based similarity search functions correctly

### ✅ **Query Interface Works End-to-End**
- The `QueryBuilder` provides a type-safe, fluent API for constructing graph queries
- Queries serialize correctly to JSON for API transmission
- The `MedicalGraphClient` can execute both typed (`GraphQuery`) and raw dictionary queries
- Convenience methods like `find_treatments()` correctly wrap the underlying query engine

### ✅ **API Contract Compliance**
- Client correctly handles HTTP POST to `/api/v1/query` endpoint
- Response parsing and error handling work as expected
- Session management and headers are properly configured

### ✅ **MCP Server Integration**
- The MCP (Model Context Protocol) server initializes correctly
- Tool discovery mechanism works
- Search result formatting produces human-readable output
- OpenSearch client integration is properly configured

### ✅ **Provenance & Trustability** **NEW**
- Evidence validation enforces mandatory paper_id field
- Confidence scores are properly bounded (0.0-1.0)
- Both lightweight (paper IDs only) and rich (full Evidence objects) provenance work
- Multiple evidence sources can be aggregated
- Contradictory evidence is properly tracked

### ✅ **Query Language Documentation Accuracy** **NEW**
- All 7 examples from QUERY_LANGUAGE.md are tested and work
- Complex multi-hop queries serialize correctly
- Filters, aggregations, and pagination work as documented
- Special characters and unicode are handled properly
- Query structure matches documented specification

### ✅ **Client Robustness** **NEW**
- Client handles all HTTP error codes gracefully (4xx, 5xx)
- Network failures (timeout, connection error, DNS failure) raise clear exceptions
- Malformed JSON responses are detected
- Empty or unexpected response structures are handled
- Timeout parameter is properly passed through to requests

### ✅ **Testability & Mocking**
- The architecture supports testing without live dependencies
- Mock HTTP servers and monkeypatched sessions work correctly
- Fixtures provide reusable test data (small graphs, sample entities)

## Running the Tests

```bash
uv run pytest tests/
```

For verbose output: 
```bash
uv run pytest tests/ -v
```

For coverage report:
```bash
uv run pytest tests/ --cov=client --cov=schema --cov=mcp
```

## Test Fixtures

The `conftest.py` file provides shared fixtures:
- `small_graph`: A minimal in-memory knowledge graph with papers, authors, venues, and concepts
- Mock HTTP server for testing the client without network calls

## What Success Means

Passing all tests demonstrates that:
1. **The data schema is sound** – entities and relationships model biomedical knowledge correctly
2. **Provenance is enforced** – evidence requirements match documentation, confidence scores are validated
3. **The query interface is production-ready** – clients can build, execute, and parse complex graph queries
4. **Documentation is accurate** – all query examples from docs actually work
5. **Client is robust** – gracefully handles service errors, network failures, and malformed responses
6. **The system is maintainable** – comprehensive mocking allows fast, reliable testing without external dependencies
7. **Integration points work** – MCP server, OpenSearch, and HTTP APIs are properly connected

This test suite provides confidence that the medical literature graph system can correctly:
- Store and retrieve biomedical entities with embeddings
- Enforce evidence-based provenance for all medical relationships
- Express and execute complex relationship queries that match documented examples
- Handle errors and edge cases gracefully
- Serve as a queryable knowledge base through multiple interfaces (direct client, MCP server)

## Test Statistics

**Total Tests**: 63
- Provenance enforcement: 11 tests
- Query completeness: 18 tests
- Client error handling: 19 tests
- Schema & entities: 3 tests
- Relationships: 2 tests
- Client library: 6 tests
- Integration: 2 tests
- MCP server: 2 tests
