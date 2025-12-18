# Query Tools for Medical Literature Knowledge Graph

This directory contains several tools for querying the medical literature knowledge graph stored in PostgreSQL/AGE.

## Tools Overview

### 1. `query_examples.py` - Pre-built Example Queries

Run pre-defined queries against the graph to explore common patterns.

**Usage:**
```bash
# In Docker
docker-compose run --rm pipeline python query_examples.py [query_name]

# Examples
docker-compose run --rm pipeline python query_examples.py stats
docker-compose run --rm pipeline python query_examples.py hiv_claims
docker-compose run --rm pipeline python query_examples.py evidence_chains
```

**Available Queries:**
- `stats` - Show graph statistics (default)
- `all_claims` - List all claims in the database
- `hiv_claims` - Find claims mentioning HIV
- `evidence_chains` - Find claims with supporting evidence
- `paper_claims` - Show papers and their claims
- `entity_mentions` - Find entities and where they're mentioned
- `causal_claims` - Find claims about causation (CAUSES, PREVENTS, etc.)
- `high_confidence` - Find high-confidence claims (>= 0.8)
- `contradictions` - Find potentially contradictory claims
- `paper_network` - Show relationships between papers
- `entity_cooccurrence` - Find entities that appear together

### 2. `interactive_query.py` - Interactive REPL

An interactive command-line interface for writing and executing custom Cypher queries.

**Usage:**
```bash
# In Docker (interactive mode)
docker-compose run --rm pipeline python interactive_query.py
```

**Commands:**
- `/help` - Show help message
- `/examples` - Show example queries
- `/stats` - Show graph statistics
- `/clear` - Clear screen
- `/quit` - Exit

**Example Session:**
```
cypher> MATCH (c:Claim) WHERE c.confidence >= 0.8 RETURN c.predicate, c.text LIMIT 5

cypher> MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim) RETURN p.title, count(c) as claim_count ORDER BY claim_count DESC

cypher> /stats

cypher> /quit
```

### 3. `query_api.py` - REST API

A FastAPI web service providing REST endpoints for querying the graph.

**Usage:**
```bash
# Start the API server
docker-compose run --rm -p 8000:8000 pipeline uvicorn query_api:app --host 0.0.0.0 --port 8000
```

**Endpoints:**

- `GET /` - API information
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /stats` - Graph statistics
- `POST /query` - Execute custom Cypher query
- `GET /papers` - List all papers
- `GET /papers/{paper_id}` - Get paper details with claims
- `GET /claims` - List claims (with filters)
- `GET /entities` - List entities
- `GET /evidence` - List evidence items

**Example API Calls:**

```bash
# Get graph statistics
curl http://localhost:8000/stats

# List papers
curl http://localhost:8000/papers?limit=5

# Get specific paper
curl http://localhost:8000/papers/PMC1307740

# Search claims about HIV
curl "http://localhost:8000/claims?search=HIV&limit=10"

# Filter claims by predicate and confidence
curl "http://localhost:8000/claims?predicate=CAUSES&min_confidence=0.7"

# Execute custom query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (c:Claim) WHERE c.confidence > 0.8 RETURN c LIMIT 5"}'
```

**Interactive API Documentation:**

Visit http://localhost:8000/docs in your browser to see interactive API documentation with a built-in query interface.

## Common Cypher Query Patterns

### Find Claims by Type

```cypher
MATCH (c:Claim)
WHERE c.predicate = 'CAUSES'
RETURN c.text, c.confidence
ORDER BY c.confidence DESC
LIMIT 10
```

### Find Papers Making Specific Claims

```cypher
MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim)
WHERE c.predicate IN ['CAUSES', 'PREVENTS']
RETURN p.title, c.predicate, c.text, c.confidence
ORDER BY c.confidence DESC
```

### Find Claims with Strong Evidence

```cypher
MATCH (e:Evidence)-[:SUPPORTS]->(c:Claim)
WHERE e.strength = 'high' OR e.strength = 'medium'
RETURN c.predicate, c.text, e.type, e.strength
ORDER BY e.strength DESC
```

### Find Entity Relationships

```cypher
MATCH (c:Claim)-[:HAS_SUBJECT]->(s:Entity),
      (c:Claim)-[:HAS_OBJECT]->(o:Entity)
RETURN s.name, c.predicate, o.name, c.confidence
ORDER BY c.confidence DESC
LIMIT 10
```

### Count Claims by Predicate

```cypher
MATCH (c:Claim)
RETURN c.predicate, count(*) as count, avg(c.confidence) as avg_confidence
ORDER BY count DESC
```

### Find Papers Citing Similar Evidence

```cypher
MATCH (p1:Paper)-[:MAKES_CLAIM]->(c1:Claim)<-[:SUPPORTS]-(e:Evidence)-[:SUPPORTS]->(c2:Claim)<-[:MAKES_CLAIM]-(p2:Paper)
WHERE p1.paper_id < p2.paper_id
RETURN p1.title, p2.title, e.type, count(*) as shared_evidence
ORDER BY shared_evidence DESC
LIMIT 10
```

### Find Contradictory Claims

```cypher
MATCH (p1:Paper)-[:MAKES_CLAIM]->(c1:Claim),
      (p2:Paper)-[:MAKES_CLAIM]->(c2:Claim)
WHERE p1.paper_id < p2.paper_id
  AND c1.predicate = 'CAUSES'
  AND c2.predicate = 'PREVENTS'
  AND c1.text =~ '.*HIV.*'
  AND c2.text =~ '.*HIV.*'
RETURN p1.title, c1.text, p2.title, c2.text
LIMIT 5
```

## Graph Schema

### Node Types

- **Paper**: Research papers
  - Properties: `paper_id`, `title`, `journal`, `pub_date`, `pmid`

- **Entity**: Biomedical entities (diseases, genes, etc.)
  - Properties: `id`, `entity_id`, `name`, `type`

- **Paragraph**: Text paragraphs from papers
  - Properties: `paragraph_id`, `section_id`, `section_type`, `text`

- **Claim**: Extracted semantic relationships
  - Properties: `claim_id`, `predicate`, `text`, `confidence`, `evidence_type`

- **Evidence**: Evidence supporting claims
  - Properties: `evidence_id`, `type`, `strength`, `supports`

### Edge Types

- **CONTAINS**: Paper → Paragraph
- **MAKES_CLAIM**: Paper → Claim
- **CONTAINS_CLAIM**: Paragraph → Claim
- **SUPPORTS**: Evidence → Claim
- **HAS_SUBJECT**: Claim → Entity
- **HAS_OBJECT**: Claim → Entity

## Tips for Writing Queries

1. **Use LIMIT** to avoid overwhelming results:
   ```cypher
   MATCH (n) RETURN n LIMIT 10
   ```

2. **Filter with WHERE clauses**:
   ```cypher
   MATCH (c:Claim)
   WHERE c.confidence >= 0.7
   RETURN c
   ```

3. **Use pattern matching for relationships**:
   ```cypher
   MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim)
   RETURN p, c
   ```

4. **Regular expressions for text search**:
   ```cypher
   MATCH (c:Claim)
   WHERE c.text =~ '.*HIV.*'
   RETURN c
   ```

5. **Aggregate functions**:
   ```cypher
   MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim)
   RETURN p.title, count(c) as num_claims
   ORDER BY num_claims DESC
   ```

## Troubleshooting

### Connection Issues

If you can't connect to the database:

1. Make sure the AGE database container is running:
   ```bash
   docker-compose ps
   ```

2. Check that environment variables are set correctly (in `docker-compose.yml`)

3. Verify the database is healthy:
   ```bash
   docker-compose logs age-db
   ```

### Query Errors

- **Syntax errors**: Check that your Cypher syntax is correct
- **Property not found**: Verify property names match the schema
- **Timeout**: Add LIMIT to large queries

### Empty Results

If queries return no results:
1. Run `/stats` to verify data was loaded
2. Check that stage 6 completed successfully
3. Verify your WHERE conditions aren't too restrictive

## Further Resources

- [Apache AGE Documentation](https://age.apache.org/age-manual/master/intro/overview.html)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
