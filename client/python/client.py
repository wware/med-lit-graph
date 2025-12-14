"""
Medical Knowledge Graph Query Client

Python client library for querying the medical knowledge graph using the JSON-based
graph query language that translates to Neptune (Gremlin/openCypher).

Usage:
    from medical_graph_client import MedicalGraphClient, QueryBuilder

    client = MedicalGraphClient("https://api.medgraph.example.com")

    # Simple query
    results = client.find_treatments("breast cancer")

    # Complex query using builder
    query = (QueryBuilder()
        .find_nodes("drug")
        .with_edge("treats", min_confidence=0.7)
        .filter_target("disease", name="diabetes")
        .limit(10)
        .build())

    results = client.execute(query)
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict
import requests
from enum import Enum
import os


class EntityType(str, Enum):
    """Medical entity types"""

    DISEASE = "disease"
    SYMPTOM = "symptom"
    DRUG = "drug"
    GENE = "gene"
    PROTEIN = "protein"
    ANATOMICAL_STRUCTURE = "anatomical_structure"
    PROCEDURE = "procedure"
    TEST = "test"
    BIOMARKER = "biomarker"
    PAPER = "paper"
    AUTHOR = "author"


class RelationType(str, Enum):
    """Relationship types between entities"""

    # Causal
    CAUSES = "causes"
    PREVENTS = "prevents"
    INCREASES_RISK = "increases_risk"
    DECREASES_RISK = "decreases_risk"

    # Treatment
    TREATS = "treats"
    MANAGES = "manages"
    CONTRAINDICATES = "contraindicates"

    # Biological
    BINDS_TO = "binds_to"
    INHIBITS = "inhibits"
    ACTIVATES = "activates"
    UPREGULATES = "upregulates"
    DOWNREGULATES = "downregulates"
    ENCODES = "encodes"

    # Clinical
    DIAGNOSES = "diagnoses"
    INDICATES = "indicates"
    ASSOCIATED_WITH = "associated_with"

    # Provenance
    CITES = "cites"


class PropertyFilter(BaseModel):
    """Filter on node/edge properties"""

    field: str
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains", "regex"]
    value: Any


class NodePattern(BaseModel):
    """Pattern for matching nodes"""

    node_type: Optional[EntityType] = None
    node_types: Optional[list[EntityType]] = None
    id: Optional[str] = None
    name: Optional[str] = None
    name_pattern: Optional[str] = None
    properties: Optional[dict] = None
    property_filters: Optional[list[PropertyFilter]] = None
    external_id: Optional[dict[str, str]] = None
    var: Optional[str] = None


class EdgePattern(BaseModel):
    """Pattern for matching edges"""

    relation_type: Optional[RelationType] = None
    relation_types: Optional[list[RelationType]] = None
    direction: Literal["outgoing", "incoming", "both"] = "outgoing"
    min_confidence: Optional[float] = None
    property_filters: Optional[list[PropertyFilter]] = None
    require_evidence_from: Optional[list[str]] = None
    min_evidence_count: Optional[int] = None
    var: Optional[str] = None


class AggregationSpec(BaseModel):
    """Aggregation specification"""

    group_by: Optional[list[str]] = None
    aggregations: dict[str, tuple[Literal["count", "sum", "avg", "min", "max"], str]]


class GraphQuery(BaseModel):
    """Complete graph query"""

    model_config = ConfigDict(use_enum_values=True)

    find: Literal["nodes", "edges", "paths", "subgraph"] = "nodes"
    node_pattern: Optional[NodePattern] = None
    edge_pattern: Optional[EdgePattern] = None
    filters: Optional[list[PropertyFilter]] = None
    aggregate: Optional[AggregationSpec] = None
    order_by: Optional[list[tuple[str, Literal["asc", "desc"]]]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    return_fields: Optional[list[str]] = None


class QueryBuilder:
    """
    Fluent builder for constructing graph queries

    Example:
        query = (QueryBuilder()
            .find_nodes("drug")
            .with_edge("treats", min_confidence=0.7)
            .filter_target("disease", name="diabetes")
            .order_by("confidence", "desc")
            .limit(10)
            .build())
    """

    def __init__(self):
        self._query = GraphQuery()
        self._filters = []

    def find_nodes(self, node_type: str | EntityType, name: Optional[str] = None, name_pattern: Optional[str] = None, var: str = "n") -> "QueryBuilder":
        """Find nodes of a specific type"""
        self._query.find = "nodes"
        self._query.node_pattern = NodePattern(node_type=EntityType(node_type) if isinstance(node_type, str) else node_type, name=name, name_pattern=name_pattern, var=var)
        return self

    def find_edges(self, relation_type: Optional[str | RelationType] = None, var: str = "r") -> "QueryBuilder":
        """Find edges/relationships"""
        self._query.find = "edges"
        self._query.edge_pattern = EdgePattern(relation_type=RelationType(relation_type) if isinstance(relation_type, str) and relation_type else None, var=var)
        return self

    def with_edge(self, relation_type: str | RelationType, direction: Literal["outgoing", "incoming", "both"] = "outgoing", min_confidence: Optional[float] = None, var: str = "r") -> "QueryBuilder":
        """Add edge pattern to node query"""
        self._query.edge_pattern = EdgePattern(
            relation_type=RelationType(relation_type) if isinstance(relation_type, str) else relation_type, direction=direction, min_confidence=min_confidence, var=var
        )
        return self

    def filter_target(self, node_type: str | EntityType, name: Optional[str] = None, name_pattern: Optional[str] = None) -> "QueryBuilder":
        """Filter on target node (when using with_edge)"""
        if name:
            self._filters.append(PropertyFilter(field="target.name", operator="eq", value=name))
        if name_pattern:
            self._filters.append(PropertyFilter(field="target.name_pattern", operator="regex", value=name_pattern))
        self._filters.append(PropertyFilter(field="target.node_type", operator="eq", value=node_type if isinstance(node_type, str) else node_type.value))
        return self

    def filter(self, field: str, operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains", "regex"], value: Any) -> "QueryBuilder":
        """Add custom filter"""
        self._filters.append(PropertyFilter(field=field, operator=operator, value=value))
        return self

    def aggregate(
        self,
        group_by: list[str],
        **aggregations: tuple[Literal["count", "sum", "avg", "min", "max"], str],
    ) -> "QueryBuilder":
        """
        Add aggregation

        Example:
            .aggregate(
                ["drug.name"],
                paper_count=("count", "rel.evidence.paper_id"),
                avg_confidence=("avg", "rel.confidence")
            )
        """
        self._query.aggregate = AggregationSpec(group_by=group_by, aggregations=aggregations)
        return self

    def order_by(self, field: str, direction: Literal["asc", "desc"] = "desc") -> "QueryBuilder":
        """Add ordering"""
        if self._query.order_by is None:
            self._query.order_by = []
        self._query.order_by.append((field, direction))
        return self

    def limit(self, n: int) -> "QueryBuilder":
        """Limit results"""
        self._query.limit = n
        return self

    def offset(self, n: int) -> "QueryBuilder":
        """Offset results (for pagination)"""
        self._query.offset = n
        return self

    def return_fields(self, *fields: str) -> "QueryBuilder":
        """Specify which fields to return"""
        self._query.return_fields = list(fields)
        return self

    def build(self) -> GraphQuery:
        """Build the final query"""
        if self._filters:
            self._query.filters = self._filters
        return self._query


class MedicalGraphClient:
    """
    Client for querying the medical knowledge graph API

    Args:
        base_url: Base URL of the API (e.g., "https://api.medgraph.example.com")
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds (default: 30)

    Example:
        client = MedicalGraphClient(os.getenv("MEDGRAPH_SERVER", "https://api.medgraph.example.com"))
        results = client.find_treatments("diabetes")
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

        self.session.headers["Content-Type"] = "application/json"

    def execute(self, query: GraphQuery) -> dict[str, Any]:
        """
        Execute a graph query

        Args:
            query: GraphQuery object

        Returns:
            Dictionary with results and metadata

        Raises:
            requests.HTTPError: If the API returns an error
        """
        response = self.session.post(f"{self.base_url}/api/v1/query", json=query.model_dump(exclude_none=True), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def execute_raw(self, query_dict: dict) -> dict[str, Any]:
        """Execute a raw query dictionary (for custom queries)"""
        response = self.session.post(f"{self.base_url}/api/v1/query", json=query_dict, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    # Convenience methods for common queries

    def find_treatments(self, disease: str, min_confidence: float = 0.6, limit: int = 20) -> dict[str, Any]:
        """
        Find drugs that treat a specific disease

        Args:
            disease: Disease name
            min_confidence: Minimum confidence threshold (0-1)
            limit: Maximum number of results

        Returns:
            Query results with drugs and evidence
        """
        query = (
            QueryBuilder()
            .find_nodes(EntityType.DRUG)
            .with_edge(RelationType.TREATS, min_confidence=min_confidence)
            .filter_target(EntityType.DISEASE, name=disease)
            .aggregate(["drug.name"], paper_count=("count", "treatment_rel.evidence.paper_id"), avg_confidence=("avg", "treatment_rel.confidence"))
            .order_by("paper_count", "desc")
            .limit(limit)
            .build()
        )

        return self.execute(query)

    def find_disease_genes(self, disease: str, min_confidence: float = 0.5, limit: int = 50) -> dict[str, Any]:
        """
        Find genes associated with a disease

        Args:
            disease: Disease name or pattern
            min_confidence: Minimum confidence threshold
            limit: Maximum number of results
        """
        query = (
            QueryBuilder()
            .find_nodes(EntityType.GENE)
            .with_edge("associated_with", direction="incoming", min_confidence=min_confidence)
            .filter_target(EntityType.DISEASE, name_pattern=f".*{disease}.*")
            .return_fields("gene.name", "gene.external_ids.hgnc", "rel.confidence", "rel.evidence.paper_id")
            .order_by("rel.confidence", "desc")
            .limit(limit)
            .build()
        )

        return self.execute(query)

    def find_diagnostic_tests(self, disease: str, min_confidence: float = 0.6) -> dict[str, Any]:
        """
        Find diagnostic tests/biomarkers for a disease

        Args:
            disease: Disease name
            min_confidence: Minimum confidence threshold
        """
        query = GraphQuery(
            find="nodes",
            node_pattern=NodePattern(node_types=[EntityType.TEST, EntityType.BIOMARKER], var="diagnostic"),
            edge_pattern=EdgePattern(relation_types=[RelationType.DIAGNOSES, RelationType.INDICATES], direction="outgoing", min_confidence=min_confidence),
            filters=[PropertyFilter(field="target.name", operator="eq", value=disease)],
            aggregate=AggregationSpec(
                group_by=["diagnostic.name", "diagnostic.node_type"], aggregations={"paper_count": ("count", "rel.evidence.paper_id"), "avg_confidence": ("avg", "rel.confidence")}
            ),
            order_by=[("avg_confidence", "desc")],
        )

        return self.execute(query)

    def find_drug_mechanisms(self, drug_name: str) -> dict[str, Any]:
        """
        Find mechanism of action for a drug (what proteins/genes it affects)

        Args:
            drug_name: Drug name
        """
        # This would need path_pattern implementation
        # Simplified for now

        # For multi-hop paths, construct raw query
        raw_query = {
            "find": "paths",
            "path_pattern": {
                "start": {"node_type": "drug", "name": drug_name, "var": "drug"},
                "edges": [[{"relation_types": ["binds_to", "inhibits", "activates"], "var": "interaction"}, {"node_types": ["protein", "gene"], "var": "target"}]],
                "max_hops": 1,
            },
            "return_fields": ["drug.name", "target.name", "target.node_type", "interaction.relation_type", "interaction.confidence"],
        }

        return self.execute_raw(raw_query)

    def compare_treatment_evidence(self, disease: str, drugs: list[str]) -> dict[str, Any]:
        """
        Compare evidence quality for different treatments

        Args:
            disease: Disease name
            drugs: List of drug names to compare
        """
        query = GraphQuery(
            find="edges",
            edge_pattern=EdgePattern(relation_type=RelationType.TREATS, min_confidence=0.5),
            filters=[PropertyFilter(field="source.name", operator="in", value=drugs), PropertyFilter(field="target.name", operator="eq", value=disease)],
            aggregate=AggregationSpec(
                group_by=["source.name"],
                aggregations={"total_papers": ("count", "rel.evidence.paper_id"), "rct_count": ("count", "rel.evidence[study_type='rct'].paper_id"), "avg_confidence": ("avg", "rel.confidence")},
            ),
            order_by=[("rct_count", "desc")],
        )

        return self.execute(query)

    def search_by_symptoms(self, symptoms: list[str], min_symptom_matches: int = 2) -> dict[str, Any]:
        """
        Find diseases matching a set of symptoms (differential diagnosis)

        Args:
            symptoms: List of symptom names
            min_symptom_matches: Minimum number of symptoms that must match
        """
        # This requires a more complex query structure
        raw_query = {
            "find": "nodes",
            "node_pattern": {"node_type": "disease", "var": "disease"},
            "filters": [{"field": "incoming_edges[relation_type='symptom_of'].source.name", "operator": "in", "value": symptoms}],
            "aggregate": {
                "group_by": ["disease.name"],
                "aggregations": {"symptom_match_count": ("count", "incoming_edges[relation_type='symptom_of']"), "total_papers": ("count", "incoming_edges.evidence.paper_id")},
            },
            "order_by": [["symptom_match_count", "desc"], ["total_papers", "desc"]],
            "limit": 10,
        }

        return self.execute_raw(raw_query)

    def get_paper_details(self, paper_id: str) -> dict[str, Any]:
        """
        Get details about a specific paper

        Args:
            paper_id: PMC ID or paper identifier
        """
        query = QueryBuilder().find_nodes(EntityType.PAPER).filter("id", "eq", paper_id).build()

        return self.execute(query)

    def find_contradictory_evidence(self, drug: str, disease: str) -> dict[str, Any]:
        """
        Find contradictory relationships (e.g., some studies say drug treats disease,
        others say it contraindicates)

        Args:
            drug: Drug name
            disease: Disease name
        """
        query = GraphQuery(
            find="edges",
            edge_pattern=EdgePattern(relation_types=[RelationType.TREATS, RelationType.CONTRAINDICATES, RelationType.INCREASES_RISK]),
            filters=[PropertyFilter(field="source.name", operator="eq", value=drug), PropertyFilter(field="target.name", operator="eq", value=disease)],
            aggregate=AggregationSpec(group_by=["rel.relation_type"], aggregations={"paper_count": ("count", "rel.evidence.paper_id"), "avg_confidence": ("avg", "rel.confidence")}),
        )

        return self.execute(query)


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = MedicalGraphClient(base_url=os.getenv("MEDGRAPH_SERVER", "https://api.medgraph.example.com"), api_key="your-api-key")  # Optional

    # Example 1: Find treatments
    print("=== Finding treatments for diabetes ===")
    results = client.find_treatments("type 2 diabetes", min_confidence=0.7)
    print(results)

    # Example 2: Custom query using builder
    print("\n=== Custom query: genes associated with breast cancer ===")
    query = (
        QueryBuilder()
        .find_nodes(EntityType.GENE)
        .with_edge(RelationType.ASSOCIATED_WITH, direction="incoming", min_confidence=0.6)
        .filter_target(EntityType.DISEASE, name_pattern=".*breast cancer.*")
        .aggregate(["gene.name"], paper_count=("count", "rel.evidence.paper_id"), avg_confidence=("avg", "rel.confidence"))
        .order_by("paper_count", "desc")
        .limit(20)
        .build()
    )

    results = client.execute(query)
    print(results)

    # Example 3: Drug mechanism
    print("\n=== Finding mechanism for metformin ===")
    results = client.find_drug_mechanisms("metformin")
    print(results)
