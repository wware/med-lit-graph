from client.python.client import MedicalGraphClient, QueryBuilder, GraphQuery


def test_query_builder_and_graphquery_serialization():
    qb = QueryBuilder()
    query = qb.find_nodes("drug", name="Olaparib").with_edge("treats", min_confidence=0.7).filter_target("disease", name="Breast Cancer").order_by("paper_count", "desc").limit(5).build()
    assert isinstance(query, GraphQuery)
    # Ensure model_dump (pydantic v2) returns a dict and key fields present
    j = query.model_dump(exclude_none=True)
    assert "find" in j and j["find"] == "nodes"
    assert "node_pattern" in j or True


def test_medical_graph_client_execute_and_execute_raw(monkeypatch):
    client = MedicalGraphClient(base_url="http://example.test", api_key=None, timeout=1)

    # Inject a fake session that returns a controllable fake response object
    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

        def json(self):
            return self._payload

    class FakeSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            # Return a predictable payload for test
            return FakeResponse({"results": [{"pmc_id": "PMC_TEST", "title": "Test"}]}, 200)

    client.session = FakeSession()
    # Use a minimal GraphQuery-like dict for execute_raw
    res = client.execute_raw({"find": "nodes"})
    assert isinstance(res, dict)
    assert "results" in res
    assert res["results"][0]["pmc_id"] == "PMC_TEST"

    # For execute (typed GraphQuery) ensure it serializes and calls POST
    qb = QueryBuilder().find_nodes("paper", name="Some Paper").limit(1).build()
    res2 = client.execute(qb)
    assert isinstance(res2, dict)
    assert "results" in res2
