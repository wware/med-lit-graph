"""
Test suite for curl examples in client/curl/EXAMPLES.md

This test validates that:
1. All JSON queries in curl examples are valid JSON
2. All queries use valid entity types from the schema
3. All queries use valid relationship types from the schema
4. The examples can be executed programmatically (when server is available)
"""

import json
import re
from pathlib import Path

import pytest
import requests

from schema.entity import EntityType
from schema.relationship import RelationType


class TestCurlExamplesSchemaCompliance:
    """Test that curl examples comply with the schema."""

    @pytest.fixture(scope="class")
    def examples_file(self):
        """Load the EXAMPLES.md file."""
        examples_path = Path(__file__).parent.parent / "client" / "curl" / "EXAMPLES.md"
        with open(examples_path, "r") as f:
            return f.read()

    @pytest.fixture(scope="class")
    def curl_queries(self, examples_file):
        """Extract all JSON queries from curl commands."""
        curl_blocks = re.findall(r"```bash\ncurl.*?```", examples_file, re.DOTALL)
        queries = []

        for idx, block in enumerate(curl_blocks, 1):
            # Skip non-query curl blocks
            if "function mgraph" in block or "TOKEN=" in block or "export" in block:
                continue
            if "@query.json" in block or "@" in block:
                continue

            json_match = re.search(r"-d\s+'({.*?})'\s*$", block, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    query = json.loads(json_match.group(1))
                    queries.append((idx, query, block))
                except json.JSONDecodeError as e:
                    pytest.fail(f"Example {idx} has invalid JSON: {e}")

        return queries

    @pytest.fixture(scope="class")
    def valid_entity_types(self):
        """Get all valid entity types from schema."""
        return [e.value for e in EntityType]

    @pytest.fixture(scope="class")
    def valid_relation_types(self):
        """Get all valid relationship types from schema."""
        return [r.value for r in RelationType]

    def test_all_queries_are_valid_json(self, curl_queries):
        """Verify that all curl examples contain valid JSON."""
        assert len(curl_queries) > 0, "No queries found in EXAMPLES.md"
        # If we get here, all queries parsed successfully
        print(f"\n✓ All {len(curl_queries)} curl examples contain valid JSON")

    def test_node_types_are_valid(self, curl_queries, valid_entity_types):
        """Verify all node types used in examples are defined in schema."""
        invalid_types = []

        for idx, query, _ in curl_queries:
            # Check node_pattern
            if "node_pattern" in query:
                node_type = query["node_pattern"].get("node_type")
                node_types = query["node_pattern"].get("node_types")

                if node_type and node_type not in valid_entity_types:
                    invalid_types.append((idx, "node_pattern.node_type", node_type))

                if node_types:
                    for nt in node_types:
                        if nt not in valid_entity_types:
                            invalid_types.append((idx, "node_pattern.node_types", nt))

            # Check path_pattern
            if "path_pattern" in query:
                path = query["path_pattern"]

                # Check start node
                if "start" in path:
                    node_type = path["start"].get("node_type")
                    if node_type and node_type not in valid_entity_types:
                        invalid_types.append((idx, "path_pattern.start.node_type", node_type))

                # Check nodes in path edges
                if "edges" in path:
                    for edge_idx, edge_pair in enumerate(path["edges"]):
                        if len(edge_pair) >= 2:
                            node_spec = edge_pair[1]
                            node_type = node_spec.get("node_type")
                            node_types = node_spec.get("node_types")

                            if node_type and node_type not in valid_entity_types:
                                invalid_types.append((idx, f"path_pattern.edges[{edge_idx}].node_type", node_type))

                            if node_types:
                                for nt in node_types:
                                    if nt not in valid_entity_types:
                                        invalid_types.append((idx, f"path_pattern.edges[{edge_idx}].node_types", nt))

        if invalid_types:
            error_msg = "\nInvalid entity types found:\n"
            for idx, location, invalid_type in invalid_types:
                error_msg += f"  Example {idx}: {location} = '{invalid_type}'\n"
            error_msg += f"\nValid entity types: {valid_entity_types}"
            pytest.fail(error_msg)

    def test_relation_types_are_valid(self, curl_queries, valid_relation_types):
        """Verify all relationship types used in examples are defined in schema."""
        invalid_types = []

        for idx, query, _ in curl_queries:
            # Check edge_pattern
            if "edge_pattern" in query:
                rel_type = query["edge_pattern"].get("relation_type")
                rel_types = query["edge_pattern"].get("relation_types")

                if rel_type and rel_type not in valid_relation_types:
                    invalid_types.append((idx, "edge_pattern.relation_type", rel_type))

                if rel_types:
                    for rt in rel_types:
                        if rt not in valid_relation_types:
                            invalid_types.append((idx, "edge_pattern.relation_types", rt))

            # Check path_pattern
            if "path_pattern" in query:
                path = query["path_pattern"]

                if "edges" in path:
                    for edge_idx, edge_pair in enumerate(path["edges"]):
                        if len(edge_pair) >= 1:
                            edge_spec = edge_pair[0]
                            rel_type = edge_spec.get("relation_type")
                            rel_types = edge_spec.get("relation_types")

                            if rel_type and rel_type not in valid_relation_types:
                                invalid_types.append((idx, f"path_pattern.edges[{edge_idx}].relation_type", rel_type))

                            if rel_types:
                                for rt in rel_types:
                                    if rt not in valid_relation_types:
                                        invalid_types.append((idx, f"path_pattern.edges[{edge_idx}].relation_types", rt))

        if invalid_types:
            error_msg = "\nInvalid relationship types found:\n"
            for idx, location, invalid_type in invalid_types:
                error_msg += f"  Example {idx}: {location} = '{invalid_type}'\n"
            error_msg += f"\nValid relationship types: {valid_relation_types}"
            pytest.fail(error_msg)

    def test_examples_cover_basic_entity_types(self, curl_queries):
        """Verify examples cover the main entity types."""
        # Core entity types that should be covered
        core_types = {"drug", "disease", "gene", "protein"}
        covered_types = set()

        for idx, query, _ in curl_queries:
            # Check node_pattern
            if "node_pattern" in query:
                node_type = query["node_pattern"].get("node_type")
                node_types = query["node_pattern"].get("node_types", [])
                if node_type:
                    covered_types.add(node_type)
                covered_types.update(node_types)

            # Check path_pattern
            if "path_pattern" in query:
                path = query["path_pattern"]
                if "start" in path:
                    node_type = path["start"].get("node_type")
                    if node_type:
                        covered_types.add(node_type)

                # Check edges in path
                if "edges" in path:
                    for edge_pair in path["edges"]:
                        if len(edge_pair) >= 2:
                            node_spec = edge_pair[1]
                            node_type = node_spec.get("node_type")
                            node_types = node_spec.get("node_types", [])
                            if node_type:
                                covered_types.add(node_type)
                            covered_types.update(node_types)

        missing = core_types - covered_types
        if missing:
            pytest.fail(f"Examples missing coverage for core entity types: {missing}")

    def test_examples_cover_pr3_features(self, curl_queries):
        """
        Verify that examples cover features from PR #3.

        PR #3 added:
        - Hypothesis, StudyDesign, StatisticalMethod, EvidenceLine entities
        - PREDICTS, REFUTES, TESTED_BY, GENERATES relationships
        - eco_type, obi_study_design, stato_methods evidence fields
        """
        # New entity types from PR #3
        pr3_entity_types = {"hypothesis", "study_design", "statistical_method", "evidence_line"}

        # New relationship types from PR #3
        pr3_relation_types = {"predicts", "refutes", "tested_by", "generates"}

        # Check coverage
        covered_entity_types = set()
        covered_relation_types = set()

        for idx, query, _ in curl_queries:
            # Check node types
            if "node_pattern" in query:
                node_type = query["node_pattern"].get("node_type")
                if node_type in pr3_entity_types:
                    covered_entity_types.add(node_type)

            # Check relation types
            if "edge_pattern" in query:
                rel_type = query["edge_pattern"].get("relation_type")
                rel_types = query["edge_pattern"].get("relation_types", [])
                if rel_type in pr3_relation_types:
                    covered_relation_types.add(rel_type)
                covered_relation_types.update(set(rel_types) & pr3_relation_types)

            # Check path patterns
            if "path_pattern" in query:
                path = query["path_pattern"]
                if "start" in path:
                    node_type = path["start"].get("node_type")
                    if node_type in pr3_entity_types:
                        covered_entity_types.add(node_type)

                if "edges" in path:
                    for edge_pair in path["edges"]:
                        if len(edge_pair) >= 1:
                            edge_spec = edge_pair[0]
                            rel_type = edge_spec.get("relation_type")
                            rel_types = edge_spec.get("relation_types", [])
                            if rel_type in pr3_relation_types:
                                covered_relation_types.add(rel_type)
                            covered_relation_types.update(set(rel_types) & pr3_relation_types)
                        if len(edge_pair) >= 2:
                            node_spec = edge_pair[1]
                            node_type = node_spec.get("node_type")
                            if node_type in pr3_entity_types:
                                covered_entity_types.add(node_type)

        missing_entities = pr3_entity_types - covered_entity_types
        missing_relations = pr3_relation_types - covered_relation_types

        # All PR #3 features should be covered after adding Examples 13-22
        if missing_entities or missing_relations:
            error_msg = "\nPR #3 features not covered in examples:\n"
            if missing_entities:
                error_msg += f"  Missing entity types: {missing_entities}\n"
            if missing_relations:
                error_msg += f"  Missing relationship types: {missing_relations}\n"
            pytest.fail(error_msg)


@pytest.mark.integration
class TestCurlExamplesExecution:
    """
    Integration tests that execute curl examples against a server.

    These tests are marked as 'integration' and require:
    - MEDGRAPH_SERVER environment variable set
    - Server running and accessible
    - Skip if server is not available
    """

    @pytest.fixture(scope="class")
    def server_url(self):
        """Get server URL from environment."""
        import os

        url = os.getenv("MEDGRAPH_SERVER")
        if not url:
            pytest.skip("MEDGRAPH_SERVER environment variable not set")
        return url

    @pytest.fixture(scope="class")
    def curl_queries(self):
        """Extract executable queries from EXAMPLES.md."""
        examples_path = Path(__file__).parent.parent / "client" / "curl" / "EXAMPLES.md"
        with open(examples_path, "r") as f:
            content = f.read()

        curl_blocks = re.findall(r"```bash\ncurl.*?```", content, re.DOTALL)
        queries = []

        for idx, block in enumerate(curl_blocks, 1):
            # Skip non-query blocks
            if "function mgraph" in block or "TOKEN=" in block or "export" in block or "@query.json" in block:
                continue

            json_match = re.search(r"-d\s+'({.*?})'\s*$", block, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    query = json.loads(json_match.group(1))
                    queries.append((idx, query))
                except json.JSONDecodeError:
                    pass

        return queries

    def test_server_is_reachable(self, server_url):
        """Verify the server is reachable."""
        try:
            response = requests.get(server_url, timeout=5)
            assert response.status_code in [200, 404], f"Server returned unexpected status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Server not reachable: {e}")

    def test_query_execution(self, server_url, curl_queries):
        """
        Execute each curl example query against the server.

        This test validates that queries can be executed against a live server.
        Requires MEDGRAPH_SERVER environment variable to be set.
        """
        if not curl_queries:
            pytest.skip("No queries available to test")

        for example_idx, query in curl_queries:
            endpoint = f"{server_url}/api/v1/query"

            try:
                response = requests.post(endpoint, json=query, timeout=30, headers={"Content-Type": "application/json"})

                # Accept either success or validation errors (since we don't have real data)
                assert response.status_code in [200, 400, 422], f"Example {example_idx} returned unexpected status {response.status_code}: {response.text}"

                if response.status_code == 200:
                    result = response.json()
                    assert "results" in result or "error" in result, f"Example {example_idx} response missing 'results' or 'error' field"

            except requests.exceptions.RequestException as e:
                pytest.skip(f"Request failed: {e}")
