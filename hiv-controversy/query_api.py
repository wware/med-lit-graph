#!/usr/bin/env python3
"""
REST API for Medical Literature Knowledge Graph

This FastAPI application provides REST endpoints for querying the
PostgreSQL/AGE knowledge graph.

Usage:
    uvicorn query_api:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    GET  /                    - API documentation (interactive Swagger UI)
    GET  /stats               - Get graph statistics
    POST /query               - Execute a Cypher query
    GET  /papers              - List all papers
    GET  /papers/{paper_id}   - Get paper details
    GET  /claims              - List claims (with filters)
    GET  /entities            - List entities
    GET  /evidence            - List evidence items
"""

import os
import re
from pathlib import Path
from typing import Any, Optional, List
from enum import Enum

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import json


# ============================================================================
# Configuration
# ============================================================================

AGE_HOST = os.getenv("AGE_HOST", "localhost")
AGE_PORT = int(os.getenv("AGE_PORT", "5432"))
AGE_DB = os.getenv("AGE_DB", "age")
AGE_USER = os.getenv("AGE_USER", "age")
AGE_PASSWORD = os.getenv("AGE_PASSWORD", "agepassword")
GRAPH_NAME = "medical_literature_graph"


# ============================================================================
# Pydantic Models
# ============================================================================


class QueryRequest(BaseModel):
    """Request model for Cypher query."""

    query: str = Field(..., description="Cypher query to execute")
    limit: Optional[int] = Field(None, description="Maximum number of results to return")


class QueryResponse(BaseModel):
    """Response model for query results."""

    results: List[Any] = Field(..., description="Query results")
    count: int = Field(..., description="Number of results")
    error: Optional[str] = Field(None, description="Error message if query failed")


class GraphStats(BaseModel):
    """Graph statistics model."""

    papers: int = Field(0, description="Number of paper nodes")
    entities: int = Field(0, description="Number of entity nodes")
    paragraphs: int = Field(0, description="Number of paragraph nodes")
    claims: int = Field(0, description="Number of claim nodes")
    evidence: int = Field(0, description="Number of evidence nodes")
    total_edges: int = Field(0, description="Total number of edges")
    edge_types: dict = Field(default_factory=dict, description="Count by edge type")


class PredicateType(str, Enum):
    """Claim predicate types."""

    CAUSES = "CAUSES"
    PREVENTS = "PREVENTS"
    INHIBITS = "INHIBITS"
    DETECTED_IN = "DETECTED_IN"
    ISOLATED_FROM = "ISOLATED_FROM"
    CORRELATES_WITH = "CORRELATES_WITH"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    INFECTS = "INFECTS"
    BINDS_TO = "BINDS_TO"
    REPLICATES_IN = "REPLICATES_IN"
    TREATS = "TREATS"
    DIAGNOSED_BY = "DIAGNOSED_BY"
    PROGRESSES_TO = "PROGRESSES_TO"
    INDICATES = "INDICATES"


# ============================================================================
# Database Connection
# ============================================================================


def init_age_session(cursor: Any) -> None:
    """
    EVERY db connection using AGE should use this init function.

    IMPORTANT: This must be called for EVERY cursor/session that uses AGE.
    AGE requires both LOAD and search_path to be set per session.

    Args:
        cursor: PostgreSQL cursor

    Usage:
        with conn.cursor() as cur:
            init_age_session(cur)
            cur.execute(...)
    """
    cursor.execute("LOAD 'age';")
    cursor.execute('SET search_path = ag_catalog, "$user", public;')


class DatabaseConnection:
    """Singleton database connection manager."""

    _conn: Optional[psycopg2.extensions.connection] = None

    @classmethod
    def get_connection(cls) -> psycopg2.extensions.connection:
        """Get or create database connection."""
        if cls._conn is None or cls._conn.closed:
            cls._conn = psycopg2.connect(host=AGE_HOST, port=AGE_PORT, database=AGE_DB, user=AGE_USER, password=AGE_PASSWORD)
            cls._conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        return cls._conn

    @classmethod
    def close(cls) -> None:
        """Close database connection."""
        if cls._conn is not None:
            cls._conn.close()
            cls._conn = None


def execute_cypher(query: str) -> tuple[List[Any], Optional[str]]:
    # 1. Improved Regex: Wrap only the variables between RETURN and the next keyword
    # This finds RETURN, captures everything until it hits ORDER BY, LIMIT, or end of string
    pattern = r"(RETURN\s+)(.*?)(?=\s+ORDER BY|\s+LIMIT|$)"
    wrapped_query = re.sub(pattern, r"\1 [\2]", query, flags=re.IGNORECASE | re.DOTALL)

    try:
        conn = DatabaseConnection.get_connection()
        with conn.cursor() as cursor:
            init_age_session(cursor)
            cursor.execute(
                "SELECT * FROM cypher('medical_literature_graph', $$ " +
                wrapped_query +
                " $$) AS (result agtype);"
            )
            results = cursor.fetchall()
            
            # Parse the results (each row is a list containing one agtype-list)
            parsed_results = []
            for row in results:
                # row[0] is the agtype list: "[val1, val2, val3...]"
                parsed_row = parse_agtype(str(row[0]))
                parsed_results.append(parsed_row)

            return parsed_results, None

    except Exception as e:
        return [], str(e)


def parse_agtype(value: str) -> Any:
    """Parse AGE's agtype format to Python objects."""
    try:
        # Remove the ::vertex or ::edge annotations
        if "::" in value:
            value = value.split("::")[0]

        # Try to parse as JSON
        return json.loads(value)
    except Exception:
        return value


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Medical Literature Knowledge Graph API",
    description="REST API for querying medical literature knowledge graph stored in PostgreSQL/AGE",
    version="1.0.0",
)

# Add CORS middleware to allow requests from web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
SCRIPT_DIR = Path(__file__).parent
static_path = SCRIPT_DIR / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        DatabaseConnection.get_connection()
        print(f"Connected to PostgreSQL/AGE at {AGE_HOST}:{AGE_PORT}")
    except Exception as e:
        print(f"Error connecting to database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    DatabaseConnection.close()


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/", tags=["General"])
async def root():
    """Serve the query interface homepage."""
    if static_path.exists():
        return FileResponse(str(static_path / "index.html"))
    else:
        return {
            "name": "Medical Literature Knowledge Graph API",
            "version": "1.0.0",
            "description": "REST API for querying medical literature knowledge graph",
            "endpoints": {
                "docs": "/docs",
                "stats": "/stats",
                "query": "/query (POST)",
                "papers": "/papers",
                "claims": "/claims",
                "entities": "/entities",
                "evidence": "/evidence",
            },
        }


@app.get("/stats", response_model=GraphStats, tags=["Statistics"])
async def get_stats():
    """Get overall graph statistics."""
    stats = GraphStats()

    # Count nodes
    node_types = {"Paper": "papers", "Entity": "entities", "Paragraph": "paragraphs", "Claim": "claims", "Evidence": "evidence"}

    for node_type, field_name in node_types.items():
        query = f"MATCH (n:{node_type}) RETURN count(n)"
        results, error = execute_cypher(query)
        if not error and results:
            count = results[0][0] if results else 0
            setattr(stats, field_name, count)

    # Count total edges
    query = "MATCH ()-[r]->() RETURN count(r)"
    results, error = execute_cypher(query)
    if not error and results:
        stats.total_edges = results[0][0] if results else 0

    # Count edges by type
    edge_types = ["CONTAINS", "MAKES_CLAIM", "CONTAINS_CLAIM", "SUPPORTS", "HAS_SUBJECT", "HAS_OBJECT"]
    for edge_type in edge_types:
        query = f"MATCH ()-[r:{edge_type}]->() RETURN count(r)"
        results, error = execute_cypher(query)
        if not error and results:
            count = results[0][0] if results else 0
            if count > 0:
                stats.edge_types[edge_type] = count

    return stats


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def execute_query(request: QueryRequest):
    """Execute a custom Cypher query."""
    query = request.query

    # Apply limit if specified
    if request.limit and "LIMIT" not in query.upper():
        query += f" LIMIT {request.limit}"

    results, error = execute_cypher(query)

    return QueryResponse(results=results, count=len(results), error=error)


@app.get("/papers", tags=["Papers"])
async def list_papers(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of papers to return"),
    offset: int = Query(0, ge=0, description="Number of papers to skip"),
):
    """List all papers in the graph."""
    query = f"""
    MATCH (p:Paper)
    RETURN p.paper_id, p.title, p.journal, p.pub_date
    ORDER BY p.paper_id
    SKIP {offset}
    LIMIT {limit}
    """

    results, error = execute_cypher(query)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {"papers": results, "count": len(results)}


@app.get("/papers/{paper_id}", tags=["Papers"])
async def get_paper(paper_id: str):
    """Get details for a specific paper including its claims."""
    # Get paper details
    paper_query = f"""
    MATCH (p:Paper {{paper_id: '{paper_id}'}})
    RETURN p
    """

    paper_results, error = execute_cypher(paper_query)
    if error:
        raise HTTPException(status_code=500, detail=error)

    if not paper_results:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

    # Get paper claims
    claims_query = f"""
    MATCH (p:Paper {{paper_id: '{paper_id}'}})-[:MAKES_CLAIM]->(c:Claim)
    RETURN c.claim_id, c.predicate, c.confidence, c.text, c.evidence_type
    ORDER BY c.confidence DESC
    """

    claims_results, error = execute_cypher(claims_query)

    return {"paper": paper_results[0], "claims": claims_results if not error else [], "claim_count": len(claims_results) if not error else 0}


@app.get("/claims", tags=["Claims"])
async def list_claims(
    predicate: Optional[PredicateType] = Query(None, description="Filter by predicate type"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    search: Optional[str] = Query(None, description="Search text in claim"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of claims to return"),
):
    """List claims with optional filters."""
    where_clauses = []

    if predicate:
        where_clauses.append(f"c.predicate = '{predicate.value}'")

    if min_confidence > 0:
        where_clauses.append(f"c.confidence >= {min_confidence}")

    if search:
        # Escape single quotes in search term
        search_escaped = search.replace("'", "\\'")
        where_clauses.append(f"c.text =~ '.*{search_escaped}.*'")

    where_clause = " AND ".join(where_clauses) if where_clauses else "true"

    query = f"""
    MATCH (c:Claim)
    WHERE {where_clause}
    RETURN c.claim_id, c.predicate, c.confidence, c.text, c.evidence_type
    ORDER BY c.confidence DESC
    LIMIT {limit}
    """

    results, error = execute_cypher(query)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {"claims": results, "count": len(results)}


@app.get("/entities", tags=["Entities"])
async def list_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of entities to return"),
):
    """List entities in the graph."""
    where_clause = f"e.type = '{entity_type}'" if entity_type else "true"

    query = f"""
    MATCH (e:Entity)
    WHERE {where_clause}
    RETURN e.entity_id, e.name, e.type
    ORDER BY e.name
    LIMIT {limit}
    """

    results, error = execute_cypher(query)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {"entities": results, "count": len(results)}


@app.get("/evidence", tags=["Evidence"])
async def list_evidence(
    strength: Optional[str] = Query(None, description="Filter by evidence strength (high, medium, low)"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of evidence items to return"),
):
    """List evidence items."""
    where_clauses = []

    if strength:
        where_clauses.append(f"e.strength = '{strength}'")

    if evidence_type:
        where_clauses.append(f"e.type = '{evidence_type}'")

    where_clause = " AND ".join(where_clauses) if where_clauses else "true"

    query = f"""
    MATCH (e:Evidence)-[:SUPPORTS]->(c:Claim)
    WHERE {where_clause}
    RETURN e.evidence_id, e.type, e.strength, e.supports, c.claim_id, c.text
    ORDER BY e.strength DESC
    LIMIT {limit}
    """

    results, error = execute_cypher(query)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {"evidence": results, "count": len(results)}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
