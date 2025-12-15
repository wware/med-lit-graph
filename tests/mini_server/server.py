#!/usr/bin/env python4
"""
Simple FastAPI server for med-lit-graph frontend development.

Provides synthetic graph data for testing without requiring:
- Full AWS infrastructure
- Neptune database
- Pipeline processing

Usage:
    pip install fastapi uvicorn
    python server.py
    # Server runs on http://localhost:8000
    # API docs at http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Add the mini_server directory to sys.path to allow imports
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# ruff: noqa: E402
# Imports after sys.path modification to allow local module imports
from datetime import datetime  # noqa: E402
from typing import Any, Dict, List, Optional  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import time  # noqa: E402
import uvicorn  # noqa: E402

from fastapi import APIRouter, FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

# Import query executor at module level for better performance
from query_executor import execute_query  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


class Entity(BaseModel):
    """A medical entity (gene, protein, disease, drug, etc.)"""

    id: str
    type: str  # "gene", "protein", "disease", "drug", "organism", etc.
    name: str
    canonical_id: str  # UMLS, SNOMED, etc.
    mentions: int  # number of papers mentioning this


class Relationship(BaseModel):
    """A relationship between two entities"""

    id: str
    subject_id: str
    predicate: str  # "treats", "causes", "interacts_with", etc.
    object_id: str
    confidence: float
    evidence_count: int  # number of papers supporting this
    papers: List[str]  # PMC IDs


class Paper(BaseModel):
    """A research paper in the graph"""

    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: str
    journal: str
    entity_count: int
    relationship_count: int


class GraphQuery(BaseModel):
    """Request for graph traversal"""

    start_entity: str
    max_depth: int = 2
    relationship_types: Optional[List[str]] = None


class GraphResult(BaseModel):
    """Graph traversal result"""

    nodes: List[Entity]
    edges: List[Relationship]
    papers: List[Paper]


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="Medical Literature Graph API", description="Synthetic data server for frontend development", version="0.1.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api/v1 prefix
api_router = APIRouter(prefix="/api/v1")

# ============================================================================
# Synthetic Data (TODO: Replace with realistic data)
# ============================================================================

# This will be populated with synthetic data
ENTITIES: Dict[str, Entity] = {}
RELATIONSHIPS: List[Relationship] = []
PAPERS: Dict[str, Paper] = {}


def load_synthetic_data():
    """Load synthetic data"""
    global ENTITIES, RELATIONSHIPS, PAPERS
    from synthetic_data import load_all_synthetic_data

    data = load_all_synthetic_data()
    # Convert to the format expected by the server
    ENTITIES = data["entities"]
    RELATIONSHIPS = data["relationships"]
    PAPERS = data["papers"]

    logger.info(f"Loaded {len(ENTITIES)} entities, {len(RELATIONSHIPS)} relationships, {len(PAPERS)} papers")


# Load data at module import time so it's available when uvicorn imports
load_synthetic_data()


# ============================================================================
# Static Files Setup
# ============================================================================

# Mount static files directory
static_path = SCRIPT_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============================================================================
# API Endpoints
# ============================================================================


# ============================================================================
# Helper Functions
# ============================================================================


def create_response_metadata(total_results: int, query_time_ms: int) -> Dict[str, Any]:
    """Create standard metadata for query responses."""
    return {"total_results": total_results, "query_time_ms": query_time_ms}


# ============================================================================
# Root and Static File Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Serve the demo UI homepage"""
    return FileResponse(str(static_path / "index.html"))


@api_router.post("/query")
async def query_endpoint(query: Dict[str, Any]):
    """
    Main query endpoint for graph queries.

    Accepts queries in the format shown in EXAMPLES.md and returns results.
    """
    try:
        logger.info(f"Query received: {query}")
        logger.info(f"ENTITIES count: {len(ENTITIES)}, RELATIONSHIPS count: {len(RELATIONSHIPS)}")

        logger.info("query_executor already imported at module level")

        start_time = time.time()
        result = execute_query(query, ENTITIES, RELATIONSHIPS)
        execution_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Query executed successfully, results: {len(result['results'])} rows")

        return {
            "status": "success",
            "query": query,
            "results": result["results"],
            "total_results": len(result["results"]),
            "execution_time_ms": execution_time_ms,
            "metadata": create_response_metadata(len(result["results"]), execution_time_ms),
        }
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        return {"status": "error", "query": query, "error": str(e), "results": [], "total_results": 0, "execution_time_ms": 0, "metadata": create_response_metadata(0, 0)}


@api_router.get("/entities", response_model=List[Entity])
async def get_entities(entity_type: Optional[str] = None, limit: int = Query(50, le=1000), offset: int = 0):
    """Get entities, optionally filtered by type"""
    # TODO: Implement with synthetic data
    return []


@api_router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(entity_id: str):
    """Get a specific entity by ID"""
    if entity_id not in ENTITIES:
        raise HTTPException(status_code=404, detail="Entity not found")
    return ENTITIES[entity_id]


@api_router.get("/relationships", response_model=List[Relationship])
async def get_relationships(subject_id: Optional[str] = None, object_id: Optional[str] = None, predicate: Optional[str] = None, limit: int = Query(50, le=1000), offset: int = 0):
    """Get relationships, optionally filtered"""
    # TODO: Implement filtering with synthetic data
    return []


@api_router.get("/papers", response_model=List[Paper])
async def get_papers(limit: int = Query(50, le=1000), offset: int = 0):
    """Get papers in the knowledge graph"""
    # TODO: Implement with synthetic data
    return []


@api_router.get("/papers/{paper_id}", response_model=Paper)
async def get_paper(paper_id: str):
    """Get a specific paper by PMC ID"""
    if paper_id not in PAPERS:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PAPERS[paper_id]


@api_router.post("/graph/traverse", response_model=GraphResult)
async def traverse_graph(query: GraphQuery):
    """
    Traverse the knowledge graph from a starting entity.

    This is the main query endpoint for exploring relationships.
    Returns subgraph centered on the starting entity.
    """
    # TODO: Implement graph traversal with synthetic data
    return GraphResult(nodes=[], edges=[], papers=[])


@api_router.get("/search")
async def search(q: str = Query(..., min_length=2), entity_types: Optional[List[str]] = Query(None), limit: int = Query(20, le=100)):
    """
    Search for entities and papers.

    Returns combined results from entities and papers that match the query.
    """
    # TODO: Implement search with synthetic data
    return {"query": q, "entities": [], "papers": [], "total_results": 0}


@api_router.get("/stats")
async def get_stats():
    """Get statistics about the knowledge graph"""
    return {
        "total_entities": len(ENTITIES),
        "total_relationships": len(RELATIONSHIPS),
        "total_papers": len(PAPERS),
        "entity_types": {},  # TODO: Count by type
        "relationship_types": {},  # TODO: Count by type
        "last_updated": datetime.now().isoformat(),
    }


@api_router.get("/examples")
async def get_examples():
    """Get parsed examples from EXAMPLES.md"""
    examples_file = static_path / "examples.json"

    if not examples_file.exists():
        raise HTTPException(status_code=404, detail="Examples file not found")

    with open(examples_file, "r", encoding="utf-8") as f:
        examples = json.load(f)

    return {"examples": examples, "total": len(examples)}


# IMPORTANT: Include the router!
app.include_router(api_router)

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Loading synthetic data...")
    load_synthetic_data()

    print("\n" + "=" * 60)
    print("🧬 Medical Literature Graph API - Development Server")
    print("=" * 60)
    print("Demo UI:          http://localhost:8000/")
    print("API Docs:         http://localhost:8000/docs")
    print("Interactive API:  http://localhost:8000/redoc")
    print("Query Endpoint:   http://localhost:8000/api/v1/query")
    print("Examples:         http://localhost:8000/api/v1/examples")
    print("=" * 60 + "\n")

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
