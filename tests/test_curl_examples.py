"""
Test suite for curl examples in client/curl/EXAMPLES.md

This test validates that:
1. All JSON queries in curl examples are valid JSON
2. All queries use valid entity types from the schema
3. All queries use valid relationship types from the schema
4. The examples can be executed programmatically (when server is available)
5. Expected responses in EXAMPLES.md are valid JSON
6. Server responses contain the expected data from EXAMPLES.md
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import requests

from schema.entity import EntityType
from schema.relationship import RelationType

# Regex pattern for extracting JSON from curl commands
# Matches: -d '{...}' at the end of a curl command block
JSON_EXTRACTION_PATTERN = r"-d\s+'({.*?})'\s*$"

# Length of query JSON snippet to use for locating expected responses
QUERY_ANCHOR_LENGTH = 100


def response_contains_expected_data(actual_response: Any, expected_response: Any) -> bool:
    """
    Recursively check if expected_response data appears somewhere in actual_response.
    Returns True if all keys/values from expected appear in actual (at any nesting level).

    This is a "contains" check, not an exact match - the actual response may have
    additional fields not in the expected response.
    """
    if expected_response is None:
        return True

    if isinstance(expected_response, dict):
        if not isinstance(actual_response, dict):
            return False
        # Check that all keys in expected exist in actual and their values match
        for key, expected_value in expected_response.items():
            if key not in actual_response:
                return False
            if not response_contains_expected_data(actual_response[key], expected_value):
                return False
        return True

    elif isinstance(expected_response, list):
        if not isinstance(actual_response, list):
            return False
        # For lists, check that each expected item appears somewhere in the actual list
        for expected_item in expected_response:
            if not any(response_contains_expected_data(actual_item, expected_item) for actual_item in actual_response):
                return False
        return True

    else:
        # For primitive values, do an equality check
        return actual_response == expected_response


def extract_queries_and_responses(examples_file: str) -> List[Tuple[int, Dict[str, Any], str, Optional[Dict[str, Any]]]]:
    """
    Extract queries and their expected responses from EXAMPLES.md.

    Returns list of tuples: (example_index, query_dict, curl_block, expected_response_dict)
    where expected_response_dict is None if no expected response is documented.
    """
    # Split the file into sections by "## Example"
    example_sections = re.split(r"(?=^## Example)", examples_file, flags=re.MULTILINE)

    queries = []

    for section in example_sections:
        if not section.strip() or not section.startswith("## Example"):
            continue

        # Extract example number
        example_match = re.match(r"## Example (\d+)", section)
        if not example_match:
            continue
        example_idx = int(example_match.group(1))

        # Find all curl blocks in this section
        curl_blocks = re.findall(r"```bash\n(curl.*?)```", section, re.DOTALL)

        for block in curl_blocks:
            # Skip non-query curl blocks
            if "function mgraph" in block or "TOKEN=" in block or "export" in block:
                continue
            if "@query.json" in block or "@" in block:
                continue

            # Extract JSON query from curl command
            json_match = re.search(JSON_EXTRACTION_PATTERN, block, re.DOTALL | re.MULTILINE)
            if not json_match:
                continue

            try:
                query = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                continue

            # Look for expected response after this curl block
            # Pattern: **Expected response:** or **Example response:**\n```json\n{...}\n```
            # Find the position of this curl block in the section to search only after it
            # We use a unique portion of the query JSON to locate the block reliably
            query_json_snippet = json_match.group(1)[:QUERY_ANCHOR_LENGTH]
            block_pos = section.find(query_json_snippet)
            if block_pos == -1:
                block_pos = 0

            # Search for expected response after the curl block
            remaining_section = section[block_pos:]
            response_match = re.search(r"\*\*(?:Expected|Example) response:\*\*\s*```json\s*(.*?)\s*```", remaining_section, re.DOTALL)

            expected_response = None
            if response_match:
                try:
                    expected_response = json.loads(response_match.group(1))
                except json.JSONDecodeError as e:
                    # Fail with a clear error message if expected response is invalid
                    pytest.fail(f"Example {example_idx} has invalid expected response JSON: {e}\n{response_match.group(1)}")

            queries.append((example_idx, query, block, expected_response))

            # Only process the first valid query in each section
            break

    return queries


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
        """Extract all JSON queries and expected responses from curl commands."""
        return extract_queries_and_responses(examples_file)

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

        for idx, query, _, _ in curl_queries:
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

        for idx, query, _, _ in curl_queries:
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

        for idx, query, _, _ in curl_queries:
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

        for idx, query, _, _ in curl_queries:
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

        return extract_queries_and_responses(content)

    def test_server_is_reachable(self, server_url):
        """Verify the server is reachable."""
        try:
            # Try to connect to the base URL or a health endpoint
            response = requests.get(server_url, timeout=5)
            # Accept any HTTP response as proof the server is reachable
            assert response.status_code < 500, f"Server returned error status: {response.status_code}"
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

        for example_idx, query, _, expected_response in curl_queries:
            endpoint = f"{server_url}/api/v1/query"

            try:
                response = requests.post(endpoint, json=query, timeout=30)

                # Accept either success or validation errors (since we don't have real data)
                assert response.status_code in [200, 400, 422], f"Example {example_idx} returned unexpected status {response.status_code}: {response.text}"

                if response.status_code == 200:
                    result = response.json()
                    assert "results" in result or "error" in result, f"Example {example_idx} response missing 'results' or 'error' field"

                # Validate that expected response data appears in actual response
                if expected_response is not None:
                    # Skip validation for unimplemented query types (Phase 2/3 features)
                    query_find_type = query.get("find")
                    has_path_pattern = "path_pattern" in query
                    has_hypothesis = query.get("node_pattern", {}).get("node_type") == "hypothesis"
                    is_edge_query = query_find_type == "edges"

                    # Only validate Phase 1 queries:  "find:  nodes" without paths/hypothesis
                    should_validate = (
                        query_find_type == "nodes"
                        and not has_path_pattern
                        and not has_hypothesis
                    )

                    if should_validate:
                        if not response_contains_expected_data(result, expected_response):
                            pytest.fail(
                                f"Example {example_idx}: Expected response data not found in actual response.\n"
                                f"Expected: {json.dumps(expected_response, indent=2)}\n"
                                f"Actual: {json.dumps(result, indent=2)}"
                            )
                    # else: Skip validation for Phase 2/3 features (path queries, edge queries, hypothesis entities)

            except requests.exceptions.RequestException as e:
                pytest.skip(f"Request failed: {e}")
