import pytest
from datetime import datetime
from uuid import uuid4

from tests.mini_server.query_executor import SQLQueryExecutor


def test_sql_query_executor(postgres_container):
    """Tests the SQLQueryExecutor directly against the test database."""
    # Use the ephemeral DB URL provided by the fixture
    db_url = postgres_container
    executor = SQLQueryExecutor(db_url)

    # 1. Manually insert some data
    with executor.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO entities (id, entity_type, name, mentions, source) VALUES (%s, %s, %s, %s, %s)", ("DRUG:aspirin", "drug", "Aspirin", 0, "extracted"))
            cur.execute("INSERT INTO entities (id, entity_type, name, mentions, source) VALUES (%s, %s, %s, %s, %s)", ("DISEASE:headache", "disease", "Headache", 0, "extracted"))
            now = datetime.utcnow()
            cur.execute("INSERT INTO relationships (id, subject_id, object_id, predicate, confidence, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)", (uuid4(), "DRUG:aspirin", "DISEASE:headache", "TREATS", 0.9, now, now))
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


def test_aggregation_query(postgres_container):
    """Tests aggregation queries in SQL."""
    db_url = postgres_container
    executor = SQLQueryExecutor(db_url)

    query = {"find": "nodes", "node_pattern": {"node_type": "drug", "var": "drug"}, "aggregate": {"group_by": ["drug.entity_type"], "aggregations": {"drug_count": ["count", "drug.id"]}}}

    result = executor.execute(query)
    assert len(result["results"]) == 1
    assert result["results"][0]["drug_count"] >= 1


def test_vector_search(postgres_container):
    """Tests semantic search using pgvector."""
    db_url = postgres_container
    executor = SQLQueryExecutor(db_url)

    # 1. Insert entities with embeddings
    # 768-dimensional unit vectors
    v1 = [0.0] * 768
    v1[0] = 1.0
    v2 = [0.0] * 768
    v2[1] = 1.0

    with executor.get_connection() as conn:
        with conn.cursor() as cur:
            # Check if vector extension is enabled (should be by docker image)
            try:
                # Format vectors as PostgreSQL vector strings: '[1,2,3]'
                v1_str = "[" + ",".join(str(x) for x in v1) + "]"
                v2_str = "[" + ",".join(str(x) for x in v2) + "]"
                # Cast to vector type during insert
                cur.execute("INSERT INTO entities (id, entity_type, name, embedding, mentions, source) VALUES (%s, %s, %s, %s::vector(768), %s, %s)", ("DRUG:v1", "drug", "Vector 1", v1_str, 0, "extracted"))
                cur.execute("INSERT INTO entities (id, entity_type, name, embedding, mentions, source) VALUES (%s, %s, %s, %s::vector(768), %s, %s)", ("DRUG:v2", "drug", "Vector 2", v2_str, 0, "extracted"))
                conn.commit()
            except Exception as e:
                if 'extension "vector"' in str(e):
                    pytest.fail("pgvector extension not installed in Postgres container")
                raise e

    # 2. Search for nearest neighbor to v1
    # Use a vector very close to v1
    search_vector = [0.0] * 768
    search_vector[0] = 0.9

    query = {"find": "nodes", "node_pattern": {"node_type": "drug", "vector_search": search_vector, "similarity_threshold": 0.8, "var": "drug"}}

    # Mock access to the embeddings model since we can't easily mock the internal call
    # But wait, SQLQueryExecutor.execute handles the query structure.
    # The original test logic called executor.execute(query).
    # However, SQLQueryExecutor makes a call to get specific embeddings if the text is provided.
    # Here we are passing the vector DIRECTLY in `vector_search`.
    # Let's double check SQLQueryExecutor implementation.

    # Looking at SQLQueryExecutor.execute_node_query:
    # if node_pattern.get("vector_search"):
    #    vector = node_pattern["vector_search"]
    #    ... uses vector directly.

    # So this test is correct as is, passing a raw vector.

    result = executor.execute(query)
    assert len(result["results"]) >= 1
    assert result["results"][0]["drug.name"] == "Vector 1"
    assert "similarity" in result["results"][0]


def test_path_query(postgres_container):
    """Tests multi-hop path queries in SQL."""
    db_url = postgres_container
    executor = SQLQueryExecutor(db_url)

    # 1. Insert chain: drug -> protein -> gene
    with executor.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO entities (id, entity_type, name, mentions, source) VALUES (%s, %s, %s, %s, %s)", ("DRUG:metformin", "drug", "Metformin", 0, "extracted"))
            cur.execute("INSERT INTO entities (id, entity_type, name, mentions, source) VALUES (%s, %s, %s, %s, %s)", ("PROTEIN:ampk", "protein", "AMPK", 0, "extracted"))
            cur.execute("INSERT INTO entities (id, entity_type, name, mentions, source) VALUES (%s, %s, %s, %s, %s)", ("GENE:prkaa1", "gene", "PRKAA1", 0, "extracted"))

            now = datetime.utcnow()
            cur.execute("INSERT INTO relationships (id, subject_id, object_id, predicate, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)", (uuid4(), "DRUG:metformin", "PROTEIN:ampk", "activates", now, now))
            cur.execute("INSERT INTO relationships (id, subject_id, object_id, predicate, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)", (uuid4(), "PROTEIN:ampk", "GENE:prkaa1", "encoded_by", now, now))
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
def test_ingestion_to_postgresql(postgres_container):
    """Tests the ingestion pipeline's ability to save to PostgreSQL."""
    # This would mock the LLM and PMC fetcher
    pass
