# Medical Knowledge Graph Schema & Query Language

## Complete Graph Schema

### Node Types

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal

class EntityType(str, Enum):
    # Core medical entities
    DISEASE = "disease"
    SYMPTOM = "symptom"
    DRUG = "drug"
    GENE = "gene"
    PROTEIN = "protein"
    ANATOMICAL_STRUCTURE = "anatomical_structure"
    PROCEDURE = "procedure"
    TEST = "test"

    # Meta entities
    PAPER = "paper"
    AUTHOR = "author"
    INSTITUTION = "institution"
    CLINICAL_TRIAL = "clinical_trial"

    # Measurement/observation entities
    MEASUREMENT = "measurement"
    BIOMARKER = "biomarker"

    # Scientific method entities (ontology-based)
    HYPOTHESIS = "hypothesis"  # IAO:0000018
    STUDY_DESIGN = "study_design"  # OBI study designs
    STATISTICAL_METHOD = "statistical_method"  # STATO methods
    EVIDENCE_LINE = "evidence_line"  # SEPIO evidence structures

class PredicateType(str, Enum):
    # Causal relationships
    CAUSES = "causes"
    PREVENTS = "prevents"
    INCREASES_RISK = "increases_risk"
    DECREASES_RISK = "decreases_risk"

    # Treatment relationships
    TREATS = "treats"
    MANAGES = "manages"
    CONTRAINDICATES = "contraindicates"

    # Biological relationships
    BINDS_TO = "binds_to"
    INHIBITS = "inhibits"
    ACTIVATES = "activates"
    UPREGULATES = "upregulates"
    DOWNREGULATES = "downregulates"
    ENCODES = "encodes"
    METABOLIZES = "metabolizes"

    # Clinical relationships
    DIAGNOSES = "diagnoses"
    INDICATES = "indicates"
    PRECEDES = "precedes"
    CO_OCCURS_WITH = "co_occurs_with"
    ASSOCIATED_WITH = "associated_with"

    # Location relationships
    LOCATED_IN = "located_in"
    AFFECTS = "affects"

    # Authorship/provenance
    AUTHORED_BY = "authored_by"
    CITES = "cites"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"

    # Hypothesis and evidence relationships
    PREDICTS = "predicts"
    REFUTES = "refutes"
    TESTED_BY = "tested_by"
    GENERATES = "generates"
```

### Complete Node Schema

```python
class GraphNode(BaseModel):
    """Base node structure"""
    id: str  # Unique canonical ID
    node_type: EntityType
    name: str  # Preferred/canonical name

    # Identifiers for external ontologies
    external_ids: dict[str, str] = Field(default_factory=dict)  # {ontology: id}
    # Examples:
    # - {"umls": "C0010054", "mesh": "D003324", "snomed": "53741008"}
    # - {"hgnc": "1100", "entrez": "672"}

    # Alternative names
    synonyms: set[str] = Field(default_factory=set)
    abbreviations: set[str] = Field(default_factory=set)

    # Type-specific properties
    properties: dict = Field(default_factory=dict)

class DiseaseNode(GraphNode):
    """Disease-specific properties"""
    node_type: Literal[EntityType.DISEASE] = EntityType.DISEASE
    properties: dict = Field(default_factory=lambda: {
        "icd10_code": None,
        "disease_category": None,  # "autoimmune", "infectious", etc.
        "prevalence": None,
        "age_of_onset_range": None,
    })

class DrugNode(GraphNode):
    """Drug-specific properties"""
    node_type: Literal[EntityType.DRUG] = EntityType.DRUG
    properties: dict = Field(default_factory=lambda: {
        "rxnorm_code": None,
        "drug_class": None,
        "mechanism_of_action": None,
        "fda_approved": None,
        "indication": None,
    })

class GeneNode(GraphNode):
    """Gene-specific properties"""
    node_type: Literal[EntityType.GENE] = EntityType.GENE
    properties: dict = Field(default_factory=lambda: {
        "hgnc_id": None,
        "entrez_id": None,
        "chromosome": None,
        "gene_type": None,  # "protein_coding", "RNA", etc.
    })

class PaperNode(GraphNode):
    """Paper metadata"""
    node_type: Literal[EntityType.PAPER] = EntityType.PAPER
    properties: dict = Field(default_factory=lambda: {
        "pmc_id": None,
        "pmid": None,
        "doi": None,
        "title": None,
        "abstract": None,
        "journal": None,
        "publication_date": None,
        "authors": [],
        "mesh_terms": [],
        "citation_count": 0,
        "status": "active",  # "active", "corrected", "retracted"
    })
```

### Complete Edge Schema

```python
class GraphEdge(BaseModel):
    """Base edge structure"""
    edge_id: str  # Unique edge ID
    source_id: str  # Source node ID
    target_id: str  # Target node ID
    relation_type: PredicateType

    # Evidence and provenance
    confidence: float = Field(ge=0.0, le=1.0)  # 0-1 confidence score
    evidence: list["Evidence"] = Field(default_factory=list)

    # Quantitative data if applicable
    measurement: "Measurement | None" = None

    # Directionality
    directed: bool = True

    # Temporal context
    temporal_context: str | None = None  # "chronic", "acute", "onset_at_age_50"

class Evidence(BaseModel):
    """Evidence supporting an edge"""
    paper_id: str
    section_type: Literal["abstract", "introduction", "methods", "results", "discussion"]
    paragraph_idx: int
    sentence_idx: int
    text_span: str
    extraction_method: Literal["scispacy_ner", "llm", "table_parser", "pattern_match"]
    extraction_confidence: float

    # Context from the paper
    study_type: Literal["observational", "rct", "meta_analysis", "case_report", "review"] | None = None
    sample_size: int | None = None

class Measurement(BaseModel):
    """Quantitative measurement associated with an edge"""
    value: float
    unit: str
    value_type: Literal["effect_size", "odds_ratio", "hazard_ratio", "p_value", "ci", "correlation"]

    # Statistical significance
    p_value: float | None = None
    confidence_interval: tuple[float, float] | None = None

    # Context
    study_population: str | None = None
    measurement_context: str | None = None

class ConflictingEvidence(BaseModel):
    """Track contradictory relationships"""
    edge1_id: str
    edge2_id: str
    conflict_type: Literal["opposite_relation", "different_outcome", "different_magnitude"]
    resolution_status: Literal["unresolved", "newer_evidence_preferred", "context_dependent"]
    notes: str | None = None
```

---

## JSON Query Language for PostgreSQL

### Design Principles

1. **Declarative**: Describe what you want, not how to get it
2. **Translatable**: Maps cleanly to PostgreSQL SQL (using CTEs for paths)
3. **Composable**: Support complex multi-hop queries
4. **Filterable**: Rich filtering on node/edge properties
5. **Aggregatable**: Support counts, grouping, statistics

### Query Structure

```python
from typing import Literal
from pydantic import BaseModel, Field

class NodePattern(BaseModel):
    """Pattern for matching nodes"""
    # Matching criteria
    node_type: EntityType | None = None
    node_types: list[EntityType] | None = None  # Match any of these types
    id: str | None = None
    name: str | None = None
    name_pattern: str | None = None  # Regex pattern

    # Property filters
    properties: dict | None = None  # Exact match on properties
    property_filters: list["PropertyFilter"] | None = None  # Complex filters

    # External ID lookup
    external_id: dict[str, str] | None = None  # {ontology: id}

    # Variable name for this node (for multi-hop queries)
    var: str | None = None

class PropertyFilter(BaseModel):
    """Filter on node/edge properties"""
    field: str
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains", "regex"]
    value: any

class EdgePattern(BaseModel):
    """Pattern for matching edges"""
    relation_type: PredicateType | None = None
    relation_types: list[PredicateType] | None = None

    # Direction
    direction: Literal["outgoing", "incoming", "both"] = "outgoing"

    # Filters
    min_confidence: float | None = None
    property_filters: list[PropertyFilter] | None = None

    # Evidence requirements
    require_evidence_from: list[str] | None = None  # Specific paper IDs
    min_evidence_count: int | None = None

    # Variable name
    var: str | None = None

class PathPattern(BaseModel):
    """Pattern for multi-hop paths"""
    start: NodePattern
    edges: list[tuple[EdgePattern, NodePattern]]  # Sequence of (edge, node) pairs
    max_hops: int = 3

    # Path constraints
    avoid_cycles: bool = True
    shortest_path: bool = False
    all_paths: bool = False

class GraphQuery(BaseModel):
    """Complete graph query"""
    # What to find
    find: Literal["nodes", "edges", "paths", "subgraph"] = "nodes"

    # Patterns
    node_pattern: NodePattern | None = None
    edge_pattern: EdgePattern | None = None
    path_pattern: PathPattern | None = None

    # Filters
    filters: list[PropertyFilter] | None = None

    # Aggregation
    aggregate: "AggregationSpec | None" = None

    # Ordering and pagination
    order_by: list[tuple[str, Literal["asc", "desc"]]] | None = None
    limit: int | None = None
    offset: int | None = None

    # Return fields
    return_fields: list[str] | None = None  # If None, return all

class AggregationSpec(BaseModel):
    """Aggregation specification"""
    group_by: list[str] | None = None
    aggregations: dict[str, tuple[Literal["count", "sum", "avg", "min", "max"], str]]
    # Examples:
    # {"paper_count": ("count", "paper_id"), "avg_confidence": ("avg", "confidence")}
```

---

## Query Examples

### Example 1: Find all drugs that treat a specific disease

```json
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "direction": "incoming"
  },
  "filters": [
    {
      "field": "target.name",
      "operator": "eq",
      "value": "breast cancer"
    },
    {
      "field": "confidence",
      "operator": "gte",
      "value": 0.7
    }
  ],
  "order_by": [["confidence", "desc"]],
  "limit": 10
}
```

**Translation to SQL (PostgreSQL):**
```sql
SELECT drug.*
FROM entities AS drug
JOIN relationships AS r ON drug.id = r.subject_id
JOIN entities AS disease ON r.object_id = disease.id
WHERE disease.name = 'breast cancer'
  AND r.predicate = 'treats'
  AND r.confidence >= 0.7
ORDER BY r.confidence DESC
LIMIT 10;
```

### Example 2: Find genes associated with a disease through any mechanism

```json
{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "disease",
      "name": "coronary artery disease",
      "var": "disease"
    },
    "edges": [
      [
        {
          "relation_types": ["associated_with", "causes", "increases_risk"],
          "min_confidence": 0.5,
          "var": "rel"
        },
        {
          "node_type": "gene",
          "var": "gene"
        }
      ]
    ],
    "max_hops": 1
  },
  "aggregate": {
    "group_by": ["gene.name"],
    "aggregations": {
      "paper_count": ["count", "rel.evidence.paper_id"],
      "avg_confidence": ["avg", "rel.confidence"]
    }
  },
  "order_by": [["paper_count", "desc"]],
  "limit": 20
}
```

### Example 3: Multi-hop - Drugs that target proteins encoded by disease-associated genes

```json
{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "disease",
      "name_pattern": ".*diabetes.*",
      "var": "disease"
    },
    "edges": [
      [
        {
          "relation_type": "associated_with",
          "var": "disease_gene_rel"
        },
        {
          "node_type": "gene",
          "var": "gene"
        }
      ],
      [
        {
          "relation_type": "encodes",
          "var": "gene_protein_rel"
        },
        {
          "node_type": "protein",
          "var": "protein"
        }
      ],
      [
        {
          "relation_types": ["binds_to", "inhibits", "activates"],
          "direction": "incoming",
          "var": "drug_protein_rel"
        },
        {
          "node_type": "drug",
          "var": "drug"
        }
      ]
    ],
    "max_hops": 3
  },
  "return_fields": [
    "disease.name",
    "gene.name",
    "protein.name",
    "drug.name",
    "drug_protein_rel.relation_type",
    "drug_protein_rel.confidence"
  ]
}
```

### Example 4: Find contradictory evidence

```json
{
  "find": "edges",
  "edge_pattern": {
    "relation_types": ["treats", "contraindicates"],
    "var": "rel"
  },
  "filters": [
    {
      "field": "source.name",
      "operator": "eq",
      "value": "aspirin"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "heart attack"
    }
  ],
  "aggregate": {
    "group_by": ["rel.relation_type"],
    "aggregations": {
      "evidence_count": ["count", "rel.evidence"],
      "avg_confidence": ["avg", "rel.confidence"],
      "paper_count": ["count", "rel.evidence.paper_id"]
    }
  }
}
```

### Example 5: Papers that support a specific claim

```json
{
  "find": "edges",
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.8,
    "var": "rel"
  },
  "node_pattern": {
    "node_type": "drug",
    "name": "metformin"
  },
  "filters": [
    {
      "field": "target.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "target.name_pattern",
      "operator": "regex",
      "value": ".*(diabetes|glycemic).*"
    },
    {
      "field": "rel.evidence.study_type",
      "operator": "in",
      "value": ["rct", "meta_analysis"]
    }
  ],
  "return_fields": [
    "target.name",
    "rel.confidence",
    "rel.evidence.paper_id",
    "rel.evidence.study_type",
    "rel.measurement.value",
    "rel.measurement.p_value"
  ]
}
```

---

## Query Translator Implementation

```python
class SQLQueryExecutor:
    """Translate JSON queries to PostgreSQL SQL"""

    def execute(self, query: GraphQuery) -> dict:
        """Translate and execute against PostgreSQL"""
        sql = self.translate(query)
        # execute sql...

    def _nodes_to_cypher(self, query: GraphQuery) -> str:
        """Generate Cypher for node queries"""
        parts = []

        # MATCH clause
        match_parts = []
        if query.node_pattern:
            node_var = query.node_pattern.var or "n"
            node_label = f":{query.node_pattern.node_type.value}" if query.node_pattern.node_type else ""
            match_parts.append(f"({node_var}{node_label})")

        if query.edge_pattern:
            edge_var = query.edge_pattern.var or "r"
            rel_type = f":{query.edge_pattern.relation_type.value}" if query.edge_pattern.relation_type else ""

            if query.edge_pattern.direction == "outgoing":
                match_parts.append(f"-[{edge_var}{rel_type}]->")
            elif query.edge_pattern.direction == "incoming":
                match_parts.append(f"<-[{edge_var}{rel_type}]-")
            else:
                match_parts.append(f"-[{edge_var}{rel_type}]-")

            match_parts.append("(target)")
## Usage Example: End-to-End

```python
# 1. User asks a question
user_question = "What drugs have been shown to effectively treat type 2 diabetes in randomized controlled trials?"

# 2. Parse to structured query
parser = NaturalLanguageQueryParser(llm_client)
structured_query = parser.parse(user_question)

# 3. Translate and execute against PostgreSQL
executor = SQLQueryExecutor("postgresql://postgres:postgres@localhost:5432/medgraph")
results = executor.execute(structured_query)

# 4. Format results for user
for record in results["results"]:
    drug_name = record["drug.name"]
    paper_count = record["paper_count"]
    print(f"{drug_name}: supported by {paper_count} RCTs")
```
