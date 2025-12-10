# Tests for med-lit-graph

This directory contains the test suite for the medical literature knowledge graph project.  The tests validate core functionality across multiple layers of the system.

## Test Coverage

### Core Components Tested

1. **Schema & Data Models** (`test_schema_entity.py`, `test_relationship.py`)
   - Entity models (Disease, Gene, Drug) with validation
   - Relationship types (Treats, Causes, Cites)
   - Entity collections with CRUD operations
   - Embedding generation and similarity search

2. **Client Library** (`test_client.py`, `test_query_engine.py`)
   - `MedicalGraphClient` API methods
   - `QueryBuilder` fluent interface
   - Query serialization and execution
   - Convenience methods (e.g., `find_treatments`)

3. **MCP Server** (`test_mcp_server.py`)
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
2. **The query interface is production-ready** – clients can build, execute, and parse complex graph queries
3. **The system is maintainable** – comprehensive mocking allows fast, reliable testing without external dependencies
4. **Integration points work** – MCP server, OpenSearch, and HTTP APIs are properly connected

This test suite provides confidence that the medical literature graph system can correctly: 
- Store and retrieve biomedical entities with embeddings
- Express and execute complex relationship queries
- Serve as a queryable knowledge base through multiple interfaces (direct client, MCP server)
