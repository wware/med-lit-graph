import os

import psycopg2
import pytest

from ingestion.init_db import init_db
from tests.mini_server.query_executor import SQLQueryExecutor

# Use a test database if available, otherwise fallback to medgraph
# Use a test database if available, otherwise fallback to medgraph
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medgraph_test")


@pytest.fixture(scope="module")
def setup_database():
    """Initializes the test database."""
    # Override DATABASE_URL for init_db
    os.environ["DATABASE_URL"] = DATABASE_URL

    # Extract connection info for the admin database
    parsed_url = DATABASE_URL.split("/")
    base_url = "/".join(parsed_url[:-1]) + "/postgres"

    try:
        # Create database if it doesn't exist (might need superuser)
        conn = psycopg2.connect(base_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS medgraph_test")
            cur.execute("CREATE DATABASE medgraph_test")
        conn.close()
    except Exception as e:
        print(f"Warning: Could not recreate test database: {e}")
        # Try to proceed if it already exists or if we should just use DEFAULT_DB_URL

    init_db()
    yield
    # Cleanup: DROP DATABASE medgraph_test (optional)


def test_sql_query_executor(setup_database):
    """Tests the SQLQueryExecutor directly against the test database."""
    executor = SQLQueryExecutor(DATABASE_URL)

    # 1. Manually insert some data
    with executor.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO entities (id, entity_type, name) VALUES (%s, %s, %s)", ("DRUG:aspirin", "drug", "Aspirin"))
            cur.execute("INSERT INTO entities (id, entity_type, name) VALUES (%s, %s, %s)", ("DISEASE:headache", "disease", "Headache"))
            cur.execute("INSERT INTO relationships (subject_id, object_id, predicate, confidence) VALUES (%s, %s, %s, %s)", ("DRUG:aspirin", "DISEASE:headache", "TREATS", 0.9))
        conn.commit()

    # 2. Run a node query
    query = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug", "var": "drug"},
        "edge_pattern": {"relation_type": "TREATS"},
        "filters": [{"field": "target.name", "operator": "eq", "value": "Headache"}],
    }

    result = executor.execute(query)
    assert len(result["results"]) == 1
    assert result["results"][0]["drug.name"] == "Aspirin"


def test_aggregation_query(setup_database):
    """Tests aggregation queries in SQL."""
    executor = SQLQueryExecutor(DATABASE_URL)

    query = {"find": "nodes", "node_pattern": {"node_type": "drug", "var": "drug"}, "aggregate": {"group_by": ["drug.entity_type"], "aggregations": {"drug_count": ["count", "drug.id"]}}}

    result = executor.execute(query)
    assert len(result["results"]) == 1
    assert result["results"][0]["drug_count"] >= 1


@pytest.mark.skipif(os.getenv("PGVECTOR_AVAILABLE") == "false", reason="pgvector extension not available")
def test_vector_search(setup_database):
    """Tests semantic search using pgvector."""
    executor = SQLQueryExecutor(DATABASE_URL)

    # 1. Insert entities with embeddings
    # 768-dimensional unit vectors
    v1 = [0.0] * 768
    v1[0] = 1.0
    v2 = [0.0] * 768
    v2[1] = 1.0

    with executor.get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO entities (id, entity_type, name, embedding) VALUES (%s, %s, %s, %s)", ("DRUG:v1", "drug", "Vector 1", v1))
                cur.execute("INSERT INTO entities (id, entity_type, name, embedding) VALUES (%s, %s, %s, %s)", ("DRUG:v2", "drug", "Vector 2", v2))
                conn.commit()
            except Exception as e:
                if 'extension "vector"' in str(e):
                    pytest.skip("pgvector extension not installed in Postgres")
                raise e

    # 2. Search for nearest neighbor to v1
    # Use a vector very close to v1
    search_vector = [0.0] * 768
    search_vector[0] = 0.9

    query = {"find": "nodes", "node_pattern": {"node_type": "drug", "vector_search": search_vector, "similarity_threshold": 0.8, "var": "drug"}}

    result = executor.execute(query)
    assert len(result["results"]) >= 1
    assert result["results"][0]["drug.name"] == "Vector 1"
    assert "similarity" in result["results"][0]


def test_path_query(setup_database):
    """Tests multi-hop path queries in SQL."""
    executor = SQLQueryExecutor(DATABASE_URL)

    # 1. Insert chain: drug -> protein -> gene
    with executor.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO entities (id, entity_type, name) VALUES (%s, %s, %s)", ("DRUG:metformin", "drug", "Metformin"))
            cur.execute("INSERT INTO entities (id, entity_type, name) VALUES (%s, %s, %s)", ("PROTEIN:ampk", "protein", "AMPK"))
            cur.execute("INSERT INTO entities (id, entity_type, name) VALUES (%s, %s, %s)", ("GENE:prkaa1", "gene", "PRKAA1"))

            cur.execute("INSERT INTO relationships (subject_id, object_id, predicate) VALUES (%s, %s, %s)", ("DRUG:metformin", "PROTEIN:ampk", "activates"))
            cur.execute("INSERT INTO relationships (subject_id, object_id, predicate) VALUES (%s, %s, %s)", ("PROTEIN:ampk", "GENE:prkaa1", "encoded_by"))
            conn.commit()

    # 2. Execute path query
    query = {
        "find": "paths",
        "path_pattern": {
            "start": {"node_type": "drug", "name": "metformin", "var": "drug"},
            "edges": [
                {"edge": {"relation_type": "activates", "var": "rel1"}, "node": {"node_type": "protein", "var": "protein"}},
                {"edge": {"relation_type": "encoded_by", "var": "rel2"}, "node": {"node_type": "gene", "var": "gene"}},
            ],
        },
    }

    result = executor.execute(query)
    assert len(result["results"]) >= 1
    row = result["results"][0]
    assert row["drug.name"] == "Metformin"
    assert row["protein.name"] == "AMPK"
    assert row["gene.name"] == "PRKAA1"


@pytest.mark.skip(reason="Requires live Ollama and PMC access")
def test_ingestion_to_postgresql(setup_database):
    """Tests the ingestion pipeline's ability to save to PostgreSQL."""
    # This would mock the LLM and PMC fetcher
    pass
