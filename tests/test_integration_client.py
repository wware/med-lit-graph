def test_find_treatments_against_mock_server(http_medical_graph_client):
    # This calls the client's high-level convenience method which will POST to the
    # mock server started by the mock_med_graph_server fixture.
    res = http_medical_graph_client.find_treatments("breast cancer", min_confidence=0.5, limit=3)
    # The mock server returns {"results": [...]}
    assert isinstance(res, dict)
    assert "results" in res
    assert isinstance(res["results"], list)
    # Basic content sanity checks
    if res["results"]:
        first = res["results"][0]
        assert "pmc_id" in first or "title" in first


def test_execute_raw_returns_paths(http_medical_graph_client):
    # direct raw paths query (the mock server responds with plausible path results)
    raw_query = {
        "find": "paths",
        "path_pattern": {
            "start": {"node_type": "drug", "name": "Drug X", "var": "drug"},
            "edges": [[{"relation_types": ["binds_to"], "var": "interaction"}, {"node_types": ["protein"], "var": "target"}]],
            "max_hops": 1,
        },
        "return_fields": ["drug.name", "target.name", "interaction.relation_type"],
    }
    res = http_medical_graph_client.execute_raw(raw_query)
    assert isinstance(res, dict)
    assert "results" in res
    # For mock server we return at least one result
    assert len(res["results"]) >= 1
    first = res["results"][0]
    # If it's a path result we expect a 'path' key
    assert "path" in first or "pmc_id" in first
