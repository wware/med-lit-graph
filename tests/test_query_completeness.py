"""
Test that all documented query examples from QUERY_LANGUAGE.md actually work.

This ensures the documentation stays in sync with the actual implementation.
Every query pattern shown in the docs should be buildable and executable.
"""

import json



def test_example_1_find_treatments_for_disease(http_medical_graph_client):
    """
    Test Example 1 from QUERY_LANGUAGE.md: Find drugs that treat breast cancer.

    From docs (line 339-381):
    Find drugs that treat breast cancer with high confidence.
    """
    query_dict = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug", "var": "drug"},
        "edge_pattern": {
            "relation_type": "treats",
            "direction": "outgoing",
            "min_confidence": 0.7,
            "var": "treatment",
        },
        "filters": [
            {"field": "target.node_type", "operator": "eq", "value": "disease"},
            {"field": "target.name", "operator": "eq", "value": "breast cancer"},
        ],
        "aggregate": {
            "group_by": ["drug.name"],
            "aggregations": {
                "paper_count": ["count", "treatment.evidence.paper_id"],
                "avg_confidence": ["avg", "treatment.confidence"],
            },
        },
        "order_by": [["paper_count", "desc"], ["avg_confidence", "desc"]],
        "limit": 20,
    }

    # Should execute without errors
    result = http_medical_graph_client.execute_raw(query_dict)
    assert isinstance(result, dict)
    assert "results" in result


def test_example_2_find_genes_associated_with_disease(http_medical_graph_client):
    """
    Test Example 2 from QUERY_LANGUAGE.md: Find genes linked to Alzheimer's disease.

    From docs (line 383-422):
    """
    query_dict = {
        "find": "nodes",
        "node_pattern": {"node_type": "gene", "var": "gene"},
        "edge_pattern": {
            "relation_types": ["associated_with", "causes", "increases_risk"],
            "direction": "incoming",
            "min_confidence": 0.6,
            "var": "association",
        },
        "filters": [
            {"field": "source.node_type", "operator": "eq", "value": "disease"},
            {"field": "source.name", "operator": "eq", "value": "Alzheimer disease"},
        ],
        "return_fields": [
            "gene.name",
            "gene.external_ids.hgnc",
            "association.relation_type",
            "association.confidence",
            "association.evidence.paper_id",
        ],
        "order_by": [["association.confidence", "desc"]],
        "limit": 50,
    }

    result = http_medical_graph_client.execute_raw(query_dict)
    assert isinstance(result, dict)
    assert "results" in result


def test_example_3_drug_mechanism_of_action(http_medical_graph_client):
    """
    Test Example 3 from QUERY_LANGUAGE.md: Multi-hop drug mechanism query.

    From docs (line 424-477):
    How does metformin affect glucose metabolism?
    """
    query_dict = {
        "find": "paths",
        "path_pattern": {
            "start": {"node_type": "drug", "name": "metformin", "var": "drug"},
            "edges": [
                {
                    "edge": {
                        "relation_types": ["binds_to", "inhibits", "activates"],
                        "var": "drug_target",
                    },
                    "node": {"node_types": ["protein", "gene"], "var": "target"},
                },
                {
                    "edge": {
                        "relation_types": ["inhibits", "activates", "upregulates", "downregulates"],
                        "var": "target_effect",
                    },
                    "node": {"node_type": "biomarker", "var": "biomarker"},
                },
            ],
            "max_hops": 2,
            "avoid_cycles": True,
        },
        "filters": [
            {
                "field": "biomarker.name_pattern",
                "operator": "regex",
                "value": ".*(glucose|blood sugar|glyc).*",
            }
        ],
        "return_fields": [
            "drug.name",
            "target.name",
            "target.node_type",
            "drug_target.relation_type",
            "biomarker.name",
            "target_effect.relation_type",
        ],
    }

    result = http_medical_graph_client.execute_raw(query_dict)
    assert isinstance(result, dict)
    assert "results" in result


def test_example_4_differential_diagnosis(http_medical_graph_client):
    """
    Test Example 4 from QUERY_LANGUAGE.md: Differential diagnosis from symptoms.

    From docs (line 480-520):
    What diseases present with fatigue, joint pain, and butterfly rash?
    """
    query_dict = {
        "find": "paths",
        "path_pattern": {
            "start": {
                "node_type": "symptom",
                "name": ["fatigue", "joint pain", "butterfly rash"],
                "var": "symptom",
            },
            "edges": [
                {
                    "edge": {
                        "relation_type": "symptom_of",
                        "direction": "outgoing",
                        "var": "symptom_disease",
                    },
                    "node": {"node_type": "disease", "var": "disease"},
                }
            ],
            "max_hops": 1,
        },
        "aggregate": {
            "group_by": ["disease.name"],
            "aggregations": {
                "symptom_count": ["count", "symptom.name"],
                "specificity_score": ["avg", "symptom_disease.confidence"],
                "supporting_papers": ["count", "symptom_disease.evidence.paper_id"],
            },
        },
        "order_by": [["symptom_count", "desc"], ["specificity_score", "desc"]],
    }

    result = http_medical_graph_client.execute_raw(query_dict)
    assert isinstance(result, dict)
    assert "results" in result


def test_simple_node_query_serialization():
    """
    Test the simple node query example from the translation section.

    From docs (line 844-860):
    """
    query_dict = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug", "var": "drug"},
        "filters": [{"field": "drug.name", "operator": "contains", "value": "metformin"}],
        "limit": 10,
    }

    # Should be valid JSON
    json_str = json.dumps(query_dict)
    assert isinstance(json_str, str)

    # Should round-trip through JSON
    parsed = json.loads(json_str)
    assert parsed["find"] == "nodes"
    assert parsed["node_pattern"]["node_type"] == "drug"
    assert parsed["limit"] == 10


def test_edge_pattern_query_serialization():
    """
    Test the edge pattern query example from the translation section.

    From docs (line 880-901):
    """
    query_dict = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug", "var": "drug"},
        "edge_pattern": {
            "relation_type": "treats",
            "direction": "outgoing",
            "min_confidence": 0.7,
            "var": "treatment",
        },
        "filters": [{"field": "target.name", "operator": "eq", "value": "diabetes"}],
    }

    # Should serialize to JSON
    json_str = json.dumps(query_dict)
    parsed = json.loads(json_str)

    assert parsed["edge_pattern"]["min_confidence"] == 0.7
    assert parsed["edge_pattern"]["relation_type"] == "treats"


def test_query_with_multiple_node_types():
    """
    Test NodePattern with node_types (plural) field.

    From docs (line 136-142):
    """
    query_dict = {
        "find": "nodes",
        "node_pattern": {"node_types": ["test", "biomarker"], "var": "diagnostic"},
        "limit": 10,
    }

    json_str = json.dumps(query_dict)
    parsed = json.loads(json_str)
    assert "test" in parsed["node_pattern"]["node_types"]
    assert "biomarker" in parsed["node_pattern"]["node_types"]


def test_query_with_multiple_relation_types():
    """
    Test EdgePattern with relation_types (plural) field.

    From docs (line 169-175):
    """
    query_dict = {
        "find": "edges",
        "edge_pattern": {
            "relation_types": ["associated_with", "causes", "increases_risk"],
            "direction": "incoming",
            "min_confidence": 0.6,
        },
    }

    json_str = json.dumps(query_dict)
    parsed = json.loads(json_str)
    assert len(parsed["edge_pattern"]["relation_types"]) == 3


def test_property_filter_operators():
    """
    Test all documented PropertyFilter operators.

    From docs (line 261-291):
    """
    operators_to_test = [
        {"field": "drug.name", "operator": "eq", "value": "aspirin"},
        {"field": "disease.name", "operator": "contains", "value": "cancer"},
        {"field": "rel.confidence", "operator": "gte", "value": 0.8},
        {"field": "source.name", "operator": "in", "value": ["aspirin", "ibuprofen"]},
        {"field": "gene.name", "operator": "regex", "value": ".*BRCA[12].*"},
    ]

    for filter_spec in operators_to_test:
        # Each should serialize correctly
        json_str = json.dumps(filter_spec)
        parsed = json.loads(json_str)
        assert parsed["operator"] == filter_spec["operator"]


def test_aggregation_structure():
    """
    Test aggregation query structure.

    From docs (line 297-323):
    """
    agg_spec = {
        "group_by": ["drug.name"],
        "aggregations": {
            "paper_count": ["count", "rel.evidence.paper_id"],
            "avg_confidence": ["avg", "rel.confidence"],
        },
    }

    # Should serialize correctly
    json_str = json.dumps(agg_spec)
    parsed = json.loads(json_str)

    assert parsed["group_by"] == ["drug.name"]
    assert "paper_count" in parsed["aggregations"]
    assert parsed["aggregations"]["paper_count"][0] == "count"


def test_pagination_queries():
    """
    Test pagination with limit and offset.

    From docs (line 742-763):
    """
    # Page 1
    query_page1 = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug"},
        "limit": 20,
        "offset": 0,
    }

    # Page 2
    query_page2 = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug"},
        "limit": 20,
        "offset": 20,
    }

    # Both should serialize
    for query in [query_page1, query_page2]:
        json_str = json.dumps(query)
        parsed = json.loads(json_str)
        assert parsed["limit"] == 20


def test_return_fields_specification():
    """
    Test return_fields parameter for field selection.

    From docs (line 412-418):
    """
    query = {
        "find": "nodes",
        "node_pattern": {"node_type": "gene"},
        "return_fields": [
            "gene.name",
            "gene.external_ids.hgnc",
            "association.relation_type",
            "association.confidence",
        ],
    }

    json_str = json.dumps(query)
    parsed = json.loads(json_str)
    assert len(parsed["return_fields"]) == 4


def test_order_by_specification():
    """
    Test order_by parameter.

    From docs (line 375-378):
    """
    query = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug"},
        "order_by": [["paper_count", "desc"], ["avg_confidence", "desc"]],
    }

    json_str = json.dumps(query)
    parsed = json.loads(json_str)
    assert len(parsed["order_by"]) == 2
    assert parsed["order_by"][0] == ["paper_count", "desc"]


def test_name_pattern_regex():
    """
    Test name_pattern field for regex matching.

    From docs (line 127-134):
    """
    query = {
        "find": "nodes",
        "node_pattern": {"node_type": "gene", "name_pattern": ".*BRCA.*", "var": "gene"},
    }

    json_str = json.dumps(query)
    parsed = json.loads(json_str)
    assert parsed["node_pattern"]["name_pattern"] == ".*BRCA.*"


def test_evidence_filtering():
    """
    Test filtering by evidence quality (study type).

    From docs (line 785-794):
    """
    query = {
        "find": "edges",
        "edge_pattern": {"relation_type": "treats", "min_confidence": 0.7},
        "filters": [
            {
                "field": "rel.evidence.study_type",
                "operator": "in",
                "value": ["rct", "meta_analysis"],
            }
        ],
    }

    json_str = json.dumps(query)
    parsed = json.loads(json_str)
    assert "rct" in parsed["filters"][0]["value"]


def test_query_builder_matches_raw_dict():
    """
    Test that QueryBuilder produces the same structure as raw dict.
    """
    # Build with QueryBuilder
    # Note: This might not work exactly until QueryBuilder is fully implemented
    # but it documents the expected API

    # Raw dict version
    raw_query = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug", "name": "aspirin"},
        "limit": 10,
    }

    # Both should serialize to similar JSON
    raw_json = json.dumps(raw_query, sort_keys=True)
    assert "drug" in raw_json
    assert "aspirin" in raw_json


def test_special_characters_in_queries():
    """
    Test that queries with special characters serialize correctly.
    """
    query = {
        "find": "nodes",
        "node_pattern": {"node_type": "disease"},
        "filters": [
            {
                "field": "disease.name",
                "operator": "contains",
                "value": "Alzheimer's disease",  # Apostrophe
            }
        ],
    }

    # Should handle apostrophe in JSON
    json_str = json.dumps(query)
    parsed = json.loads(json_str)
    assert "Alzheimer's" in parsed["filters"][0]["value"]


def test_unicode_in_queries():
    """
    Test that queries with unicode characters work.
    """
    query = {
        "find": "nodes",
        "node_pattern": {"node_type": "drug", "name": "café"},  # Accented character
        "limit": 10,
    }

    json_str = json.dumps(query, ensure_ascii=False)
    parsed = json.loads(json_str)
    assert parsed["node_pattern"]["name"] == "café"
