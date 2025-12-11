from client.python.client import QueryBuilder, EntityType

# This test set targets the client QueryBuilder/GraphQuery and MedicalGraphClient.
# It uses the monkeypatch-based mocked_medical_graph_client fixture provided by
# tests/conftest_monkeypatch.py so no network is needed.


def test_query_builder_serialization_and_execute(mocked_medical_graph_client):
    qb = (
        QueryBuilder()
        .find_nodes(EntityType.DRUG)
        .with_edge("treats", min_confidence=0.7)
        .filter_target(EntityType.DISEASE, name="Breast Cancer")
        .order_by("paper_count", "desc")
        .limit(5)
        .build()
    )

    # Ensure GraphQuery serializes via pydantic model_dump (v2)
    dumped = qb.model_dump(exclude_none=True)
    assert isinstance(dumped, dict)
    assert dumped.get("find") == "nodes"

    # Execute typed query via the patched client.session
    res = mocked_medical_graph_client.execute(qb)
    assert isinstance(res, dict)
    assert "results" in res
    assert isinstance(res["results"], list)


def test_execute_raw_paths_returns_path_structure(mocked_medical_graph_client):
    raw_query = {
        "find": "paths",
        "path_pattern": {
            "start": {"node_type": "drug", "name": "Drug X", "var": "drug"},
            "edges": [[{"relation_types": ["binds_to"], "var": "interaction"}, {"node_types": ["protein"], "var": "target"}]],
            "max_hops": 1,
        },
        "return_fields": ["drug.name", "target.name", "interaction.relation_type"],
    }

    res = mocked_medical_graph_client.execute_raw(raw_query)
    assert isinstance(res, dict)
    assert "results" in res
    assert isinstance(res["results"], list)
    # For our fake session we return at least one result; verify it's path-shaped or paper-shaped
    first = res["results"][0]
    assert "path" in first or "pmc_id" in first


def test_find_treatments_convenience_uses_execute(mocked_medical_graph_client):
    res = mocked_medical_graph_client.find_treatments("breast cancer", min_confidence=0.5, limit=3)
    assert isinstance(res, dict)
    assert "results" in res
    if res["results"]:
        item = res["results"][0]
        assert "title" in item or "pmc_id" in item


def test_unhandled_payload_returns_empty_results(mocked_medical_graph_client):
    # Send a payload our fake session doesn't match -> fallback returns {"results": []}
    res = mocked_medical_graph_client.execute_raw({"not_a_valid_query_key": True})
    assert isinstance(res, dict)
    assert "results" in res
    assert res["results"] == []
