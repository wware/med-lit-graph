# Medical Knowledge Graph API - curl Examples

Complete set of curl examples for querying the medical knowledge graph API.

## Setup

```bash
# Set your API endpoint and key
export MEDGRAPH_SERVER="${MEDGRAPH_SERVER:-https://api.medgraph.example.com}"
export API_KEY="your-api-key-here"

# Helper function for authenticated requests
function mgraph() {
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        "$MEDGRAPH_SERVER/api/v1/query" \
        -d "$1"
}
```

---

## Example 1: Find Treatments for a Disease

**Find drugs that treat breast cancer:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug",
    "var": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "direction": "outgoing",
    "min_confidence": 0.7,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "target.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "breast cancer"
    }
  ],
  "aggregate": {
    "group_by": ["drug.name"],
    "aggregations": {
      "paper_count": ["count", "treatment.evidence.paper_id"],
      "avg_confidence": ["avg", "treatment.confidence"],
      "total_evidence": ["count", "treatment.evidence"]
    }
  },
  "order_by": [
    ["paper_count", "desc"],
    ["avg_confidence", "desc"]
  ],
  "limit": 20
}'
```

**Expected response:**
```json
{
  "results": [
    {
      "drug.name": "tamoxifen",
      "paper_count": 234,
      "avg_confidence": 0.89,
      "total_evidence": 456
    },
    {
      "drug.name": "trastuzumab",
      "paper_count": 189,
      "avg_confidence": 0.92,
      "total_evidence": 312
    }
  ],
  "metadata": {
    "total_results": 15,
    "query_time_ms": 45
  }
}
```

---

## Example 2: Find Genes Associated with Disease

**Find genes linked to Alzheimer's disease:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {
    "node_type": "gene",
    "var": "gene"
  },
  "edge_pattern": {
    "relation_types": ["associated_with", "causes", "increases_risk"],
    "direction": "incoming",
    "min_confidence": 0.6,
    "var": "association"
  },
  "filters": [
    {
      "field": "source.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "source.name",
      "operator": "eq",
      "value": "Alzheimer disease"
    }
  ],
  "return_fields": [
    "gene.name",
    "gene.external_ids.hgnc",
    "gene.external_ids.entrez",
    "association.relation_type",
    "association.confidence",
    "association.evidence.paper_id"
  ],
  "order_by": [["association.confidence", "desc"]],
  "limit": 50
}'
```

---

## Example 3: Multi-Hop Query - Drug Mechanism of Action

**How does metformin work to lower blood sugar?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "name": "metformin",
      "var": "drug"
    },
    "edges": [
      [
        {
          "relation_types": ["binds_to", "inhibits", "activates"],
          "var": "drug_target"
        },
        {
          "node_types": ["protein", "gene"],
          "var": "target"
        }
      ],
      [
        {
          "relation_types": ["inhibits", "activates", "upregulates", "downregulates"],
          "var": "target_effect"
        },
        {
          "node_type": "biomarker",
          "var": "biomarker"
        }
      ]
    ],
    "max_hops": 2,
    "avoid_cycles": true
  },
  "filters": [
    {
      "field": "biomarker.name_pattern",
      "operator": "regex",
      "value": ".*(glucose|blood sugar|glyc).*"
    }
  ],
  "return_fields": [
    "drug.name",
    "target.name",
    "target.node_type",
    "drug_target.relation_type",
    "biomarker.name",
    "target_effect.relation_type",
    "path.confidence_score"
  ]
}'
```

---

## Example 4: Drug Repurposing Discovery

**Find FDA-approved drugs that target Alzheimer's-associated proteins but are used for other conditions:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "disease",
      "name": "Alzheimer disease",
      "var": "alzheimers"
    },
    "edges": [
      [
        {
          "relation_types": ["associated_with", "causes"],
          "min_confidence": 0.6,
          "var": "disease_gene"
        },
        {
          "node_type": "gene",
          "var": "gene"
        }
      ],
      [
        {
          "relation_type": "encodes",
          "var": "gene_protein"
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
          "var": "drug_protein"
        },
        {
          "node_type": "drug",
          "property_filters": [
            {
              "field": "properties.fda_approved",
              "operator": "eq",
              "value": true
            }
          ],
          "var": "drug"
        }
      ],
      [
        {
          "relation_type": "treats",
          "direction": "outgoing",
          "var": "drug_indication"
        },
        {
          "node_type": "disease",
          "var": "current_indication"
        }
      ]
    ],
    "max_hops": 4
  },
  "filters": [
    {
      "field": "current_indication.name",
      "operator": "ne",
      "value": "Alzheimer disease"
    }
  ],
  "aggregate": {
    "group_by": ["drug.name", "current_indication.name"],
    "aggregations": {
      "protein_targets": ["count", "protein.name"],
      "evidence_strength": ["avg", "disease_gene.confidence"]
    }
  },
  "order_by": [
    ["protein_targets", "desc"],
    ["evidence_strength", "desc"]
  ],
  "limit": 10
}'
```

---

## Example 5: Compare Treatment Evidence Quality

**Compare statins vs PCSK9 inhibitors for treating high cholesterol:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "edges",
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.5,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "source.node_type",
      "operator": "eq",
      "value": "drug"
    },
    {
      "field": "source.name",
      "operator": "in",
      "value": ["atorvastatin", "simvastatin", "evolocumab", "alirocumab"]
    },
    {
      "field": "target.name_pattern",
      "operator": "regex",
      "value": ".*(hypercholesterolemia|high cholesterol).*"
    }
  ],
  "aggregate": {
    "group_by": ["source.name", "target.name"],
    "aggregations": {
      "total_papers": ["count", "treatment.evidence.paper_id"],
      "rct_count": ["count", "treatment.evidence[study_type='rct'].paper_id"],
      "meta_analysis_count": ["count", "treatment.evidence[study_type='meta_analysis'].paper_id"],
      "avg_confidence": ["avg", "treatment.confidence"],
      "avg_sample_size": ["avg", "treatment.evidence.sample_size"],
      "significant_results": ["count", "treatment.measurement[p_value<0.05]"]
    }
  },
  "order_by": [
    ["rct_count", "desc"],
    ["meta_analysis_count", "desc"]
  ]
}'
```

---

## Example 6: Identify Contradictory Evidence

**Are there conflicting studies about aspirin preventing heart attacks?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "edges",
  "edge_pattern": {
    "relation_types": ["prevents", "increases_risk", "decreases_risk", "associated_with"],
    "var": "relationship"
  },
  "filters": [
    {
      "field": "source.name",
      "operator": "eq",
      "value": "aspirin"
    },
    {
      "field": "target.name_pattern",
      "operator": "regex",
      "value": ".*(heart attack|myocardial infarction|MI).*"
    }
  ],
  "aggregate": {
    "group_by": ["relationship.relation_type"],
    "aggregations": {
      "paper_count": ["count", "relationship.evidence.paper_id"],
      "avg_confidence": ["avg", "relationship.confidence"],
      "latest_paper_date": ["max", "relationship.evidence.paper_publication_date"],
      "avg_sample_size": ["avg", "relationship.evidence.sample_size"]
    }
  },
  "order_by": [["relationship.relation_type", "asc"]]
}'
```

**Get detailed evidence:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "subgraph",
  "filters": [
    {
      "field": "edge.source.name",
      "operator": "eq",
      "value": "aspirin"
    },
    {
      "field": "edge.target.name_pattern",
      "operator": "regex",
      "value": ".*(heart attack|myocardial infarction).*"
    }
  ],
  "return_fields": [
    "edge.relation_type",
    "edge.confidence",
    "edge.evidence.paper_id",
    "edge.evidence.study_type",
    "edge.evidence.sample_size",
    "edge.evidence.temporal_context",
    "edge.measurement.value",
    "edge.measurement.p_value"
  ]
}'
```

---

## Example 7: Differential Diagnosis from Symptoms

**What diseases present with fatigue, joint pain, and butterfly rash?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "symptom",
      "name": ["fatigue", "joint pain", "butterfly rash"],
      "var": "symptom"
    },
    "edges": [
      [
        {
          "relation_type": "causes",
          "direction": "incoming",
          "var": "symptom_disease"
        },
        {
          "node_type": "disease",
          "var": "disease"
        }
      ]
    ],
    "max_hops": 1
  },
  "aggregate": {
    "group_by": ["disease.name"],
    "aggregations": {
      "symptom_count": ["count", "symptom.name"],
      "specificity_score": ["avg", "symptom_disease.confidence"],
      "supporting_papers": ["count", "symptom_disease.evidence.paper_id"]
    }
  },
  "order_by": [
    ["symptom_count", "desc"],
    ["specificity_score", "desc"]
  ]
}'
```

---

## Example 8: Find Diagnostic Tests

**What tests diagnose systemic lupus erythematosus?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {
    "node_types": ["test", "biomarker"],
    "var": "diagnostic"
  },
  "edge_pattern": {
    "relation_types": ["diagnoses", "indicates"],
    "direction": "outgoing",
    "min_confidence": 0.6,
    "var": "diagnostic_rel"
  },
  "filters": [
    {
      "field": "target.node_type",
      "operator": "eq",
      "value": "disease"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "systemic lupus erythematosus"
    }
  ],
  "aggregate": {
    "group_by": ["diagnostic.name", "diagnostic.node_type"],
    "aggregations": {
      "sensitivity": ["avg", "diagnostic_rel.measurement[value_type='sensitivity'].value"],
      "specificity": ["avg", "diagnostic_rel.measurement[value_type='specificity'].value"],
      "paper_count": ["count", "diagnostic_rel.evidence.paper_id"]
    }
  },
  "return_fields": [
    "diagnostic.name",
    "diagnostic.node_type",
    "sensitivity",
    "specificity",
    "paper_count",
    "diagnostic_rel.evidence.study_type"
  ],
  "order_by": [
    ["sensitivity", "desc"],
    ["specificity", "desc"]
  ]
}'
```

---

## Example 9: Recent Discoveries

**What new treatments for multiple sclerosis were discovered in the last 2 years?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "edges",
  "edge_pattern": {
    "relation_types": ["treats", "manages"],
    "min_confidence": 0.6,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "source.node_type",
      "operator": "eq",
      "value": "drug"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "multiple sclerosis"
    },
    {
      "field": "treatment.evidence.paper_publication_date",
      "operator": "gte",
      "value": "2023-01-01"
    }
  ],
  "aggregate": {
    "group_by": ["source.name"],
    "aggregations": {
      "paper_count": ["count", "treatment.evidence.paper_id"],
      "latest_evidence": ["max", "treatment.evidence.paper_publication_date"],
      "avg_confidence": ["avg", "treatment.confidence"]
    }
  },
  "order_by": [
    ["latest_evidence", "desc"],
    ["paper_count", "desc"]
  ]
}'
```

---

## Example 10: Population-Specific Treatment

**Effectiveness of ACE inhibitors for hypertension in elderly patients:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "edges",
  "edge_pattern": {
    "relation_type": "treats",
    "var": "treatment"
  },
  "filters": [
    {
      "field": "source.properties.drug_class",
      "operator": "eq",
      "value": "ACE inhibitor"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "hypertension"
    },
    {
      "field": "treatment.evidence.study_population",
      "operator": "regex",
      "value": ".*(elderly|geriatric|age>65|older adult).*"
    }
  ],
  "return_fields": [
    "source.name",
    "treatment.measurement.value",
    "treatment.measurement.unit",
    "treatment.measurement.value_type",
    "treatment.evidence.paper_id",
    "treatment.evidence.sample_size",
    "treatment.evidence.study_type"
  ],
  "aggregate": {
    "group_by": ["source.name"],
    "aggregations": {
      "avg_effect_size": ["avg", "treatment.measurement[value_type='effect_size'].value"],
      "study_count": ["count", "treatment.evidence.paper_id"],
      "total_sample_size": ["sum", "treatment.evidence.sample_size"]
    }
  },
  "order_by": [["avg_effect_size", "desc"]]
}'
```

---

## Example 11: Drug-Drug Interactions

**Interactions between warfarin and NSAIDs:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "name": "warfarin",
      "var": "drug1"
    },
    "edges": [
      [
        {
          "relation_type": "interacts_with",
          "var": "interaction"
        },
        {
          "node_type": "drug",
          "property_filters": [
            {
              "field": "properties.drug_class",
              "operator": "eq",
              "value": "NSAID"
            }
          ],
          "var": "drug2"
        }
      ]
    ],
    "max_hops": 1
  },
  "return_fields": [
    "drug1.name",
    "drug2.name",
    "interaction.relation_type",
    "interaction.properties.severity",
    "interaction.properties.mechanism",
    "interaction.evidence.paper_id",
    "interaction.evidence.case_count"
  ],
  "order_by": [["interaction.properties.severity", "desc"]]
}'
```

---

## Example 12: Get Paper Details

**Retrieve details about a specific paper:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {
    "node_type": "paper",
    "id": "PMC12345678"
  },
  "return_fields": [
    "properties.title",
    "properties.abstract",
    "properties.authors",
    "properties.journal",
    "properties.publication_date",
    "properties.mesh_terms",
    "properties.doi",
    "properties.citation_count"
  ]
}'
```

---

## Pagination Example

**Retrieve results in pages:**

```bash
# Page 1 (results 0-19)
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "limit": 20,
  "offset": 0
}'

# Page 2 (results 20-39)
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "limit": 20,
  "offset": 20
}'
```

---

## Batch Queries (Multiple Queries in One Request)

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "queries": [
    {
      "id": "treatments",
      "query": {
        "find": "nodes",
        "node_pattern": {"node_type": "drug"},
        "edge_pattern": {"relation_type": "treats"},
        "filters": [{"field": "target.name", "operator": "eq", "value": "diabetes"}],
        "limit": 10
      }
    },
    {
      "id": "genes",
      "query": {
        "find": "nodes",
        "node_pattern": {"node_type": "gene"},
        "edge_pattern": {"relation_type": "associated_with", "direction": "incoming"},
        "filters": [{"field": "source.name", "operator": "eq", "value": "diabetes"}],
        "limit": 10
      }
    }
  ]
}'
```

---

## Error Handling

```bash
# Query with invalid field
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {"invalid_field": "value"}
}' | jq

# Expected error response:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid field: invalid_field",
    "details": {
      "field": "node_pattern.invalid_field",
      "allowed_fields": ["node_type", "node_types", "id", "name", "name_pattern", ...]
    }
  }
}
```

---

## Example 13: Track Hypothesis Evolution (PR #3 Feature)

**Find papers testing the amyloid cascade hypothesis for Alzheimer's:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "hypothesis",
      "name": "Amyloid Cascade Hypothesis",
      "var": "hypothesis"
    },
    "edges": [
      [
        {
          "relation_type": "tested_by",
          "var": "test_relationship"
        },
        {
          "node_type": "paper",
          "var": "paper"
        }
      ]
    ],
    "max_hops": 1
  },
  "return_fields": [
    "hypothesis.name",
    "hypothesis.status",
    "hypothesis.proposed_date",
    "paper.pmc_id",
    "paper.title",
    "paper.publication_date",
    "test_relationship.test_outcome",
    "test_relationship.study_design_id"
  ],
  "order_by": [["paper.publication_date", "desc"]],
  "limit": 20
}'
```

**Expected response:**
```json
{
  "results": [
    {
      "hypothesis.name": "Amyloid Cascade Hypothesis",
      "hypothesis.status": "controversial",
      "paper.pmc_id": "PMC9876543",
      "paper.title": "Aducanumab fails to meet primary endpoints",
      "test_relationship.test_outcome": "refuted",
      "test_relationship.study_design_id": "OBI:0000008"
    }
  ]
}
```

---

## Example 14: Query by Study Design Quality (PR #3 Feature)

**Find RCT evidence for treatments with high-quality study designs:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "edges",
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.7,
    "var": "treatment"
  },
  "filters": [
    {
      "field": "source.node_type",
      "operator": "eq",
      "value": "drug"
    },
    {
      "field": "target.name",
      "operator": "eq",
      "value": "breast cancer"
    },
    {
      "field": "treatment.evidence.obi_study_design",
      "operator": "eq",
      "value": "OBI:0000008"
    },
    {
      "field": "treatment.evidence.eco_type",
      "operator": "eq",
      "value": "ECO:0007673"
    }
  ],
  "return_fields": [
    "source.name",
    "treatment.confidence",
    "treatment.evidence.paper_id",
    "treatment.evidence.study_type",
    "treatment.evidence.sample_size",
    "treatment.evidence.obi_study_design",
    "treatment.evidence.eco_type"
  ],
  "aggregate": {
    "group_by": ["source.name"],
    "aggregations": {
      "rct_count": ["count", "treatment.evidence.paper_id"],
      "avg_sample_size": ["avg", "treatment.evidence.sample_size"],
      "avg_confidence": ["avg", "treatment.confidence"]
    }
  },
  "order_by": [
    ["rct_count", "desc"],
    ["avg_confidence", "desc"]
  ]
}'
```

---

## Example 15: Statistical Methods Analysis (PR #3 Feature)

**What statistical methods are used in studies of a specific treatment?**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "name": "pembrolizumab",
      "var": "drug"
    },
    "edges": [
      [
        {
          "relation_type": "treats",
          "var": "treatment"
        },
        {
          "node_type": "disease",
          "var": "disease"
        }
      ]
    ],
    "max_hops": 1
  },
  "return_fields": [
    "drug.name",
    "disease.name",
    "treatment.evidence.paper_id",
    "treatment.evidence.stato_methods",
    "treatment.confidence"
  ],
  "filters": [
    {
      "field": "treatment.evidence.stato_methods",
      "operator": "contains",
      "value": "STATO:0000304"
    }
  ]
}'
```

**Expected response:**
```json
{
  "results": [
    {
      "drug.name": "pembrolizumab",
      "disease.name": "melanoma",
      "treatment.evidence.paper_id": "PMC7654321",
      "treatment.evidence.stato_methods": ["STATO:0000304", "STATO:0000376"],
      "treatment.confidence": 0.92
    }
  ]
}
```

---

## Example 16: Evidence Line Tracking (PR #3 Feature)

**Find evidence lines supporting a specific therapeutic assertion:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "evidence_line",
      "var": "evidence_line"
    },
    "edges": [
      [
        {
          "relation_type": "supports",
          "var": "support_rel"
        },
        {
          "node_type": "hypothesis",
          "var": "hypothesis"
        }
      ]
    ],
    "max_hops": 1
  },
  "filters": [
    {
      "field": "hypothesis.name",
      "operator": "contains",
      "value": "PARP inhibitor"
    }
  ],
  "return_fields": [
    "evidence_line.name",
    "evidence_line.strength",
    "evidence_line.sepio_type",
    "evidence_line.eco_type",
    "evidence_line.evidence_items",
    "hypothesis.name",
    "hypothesis.status"
  ],
  "order_by": [["evidence_line.strength", "desc"]]
}'
```

---

## Example 17: Hypothesis Predictions (PR #3 Feature)

**What does a hypothesis predict and what evidence supports/refutes it?**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "hypothesis",
      "entity_id": "HYPOTHESIS:parp_inhibitor_synthetic_lethality",
      "var": "hypothesis"
    },
    "edges": [
      [
        {
          "relation_type": "predicts",
          "var": "prediction"
        },
        {
          "node_type": "disease",
          "var": "disease"
        }
      ]
    ],
    "max_hops": 1
  },
  "return_fields": [
    "hypothesis.name",
    "hypothesis.description",
    "hypothesis.status",
    "disease.name",
    "prediction.prediction_type",
    "prediction.testable",
    "prediction.confidence"
  ]
}'
```

---

## Example 18: Find Papers that Generate Evidence (PR #3 Feature)

**Which papers generate evidence lines for a specific disease?**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "paper",
      "var": "paper"
    },
    "edges": [
      [
        {
          "relation_type": "generates",
          "var": "generation"
        },
        {
          "node_type": "evidence_line",
          "var": "evidence"
        }
      ]
    ],
    "max_hops": 1
  },
  "filters": [
    {
      "field": "paper.study_type",
      "operator": "eq",
      "value": "rct"
    },
    {
      "field": "generation.quality_score",
      "operator": "gte",
      "value": 0.8
    }
  ],
  "return_fields": [
    "paper.pmc_id",
    "paper.title",
    "paper.study_type",
    "evidence.name",
    "evidence.strength",
    "generation.quality_score",
    "generation.eco_type"
  ],
  "order_by": [["generation.quality_score", "desc"]],
  "limit": 20
}'
```

---

## Example 19: Protein-Centric Query (Coverage for Protein Entity)

**Find proteins targeted by FDA-approved drugs:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "var": "drug"
    },
    "edges": [
      [
        {
          "relation_types": ["binds_to", "inhibits", "activates"],
          "var": "drug_target"
        },
        {
          "node_type": "protein",
          "var": "protein"
        }
      ]
    ],
    "max_hops": 1
  },
  "filters": [
    {
      "field": "drug.properties.fda_approved",
      "operator": "eq",
      "value": true
    }
  ],
  "return_fields": [
    "drug.name",
    "drug.drug_class",
    "protein.name",
    "protein.uniprot_id",
    "protein.function",
    "drug_target.relation_type",
    "drug_target.confidence"
  ],
  "aggregate": {
    "group_by": ["protein.name", "protein.uniprot_id"],
    "aggregations": {
      "drug_count": ["count", "drug.name"],
      "avg_confidence": ["avg", "drug_target.confidence"]
    }
  },
  "order_by": [
    ["drug_count", "desc"],
    ["avg_confidence", "desc"]
  ],
  "limit": 50
}'
```

---

## Example 20: Study Design Quality Filter (PR #3 Feature)

**Query studies by their formal study design classification:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {
    "node_type": "study_design",
    "var": "design"
  },
  "filters": [
    {
      "field": "design.evidence_level",
      "operator": "lte",
      "value": 2
    }
  ],
  "return_fields": [
    "design.name",
    "design.obi_id",
    "design.design_type",
    "design.evidence_level",
    "design.description"
  ],
  "order_by": [["design.evidence_level", "asc"]]
}'
```

---

## Example 21: Statistical Method Classification (PR #3 Feature)

**Find papers using specific statistical methods:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {
    "node_type": "statistical_method",
    "var": "method"
  },
  "filters": [
    {
      "field": "method.method_type",
      "operator": "eq",
      "value": "hypothesis_test"
    }
  ],
  "return_fields": [
    "method.name",
    "method.stato_id",
    "method.method_type",
    "method.description",
    "method.assumptions"
  ],
  "limit": 20
}'
```

---

## Example 22: Evidence Refuting Hypotheses (PR #3 Feature)

**Find papers that refute a specific hypothesis:**

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "paper",
      "var": "paper"
    },
    "edges": [
      [
        {
          "relation_type": "refutes",
          "var": "refutation"
        },
        {
          "node_type": "hypothesis",
          "var": "hypothesis"
        }
      ]
    ],
    "max_hops": 1
  },
  "filters": [
    {
      "field": "hypothesis.name",
      "operator": "contains",
      "value": "Amyloid"
    }
  ],
  "return_fields": [
    "paper.pmc_id",
    "paper.title",
    "paper.publication_date",
    "paper.study_type",
    "hypothesis.name",
    "hypothesis.status",
    "refutation.refutation_strength",
    "refutation.alternative_explanation"
  ],
  "order_by": [
    ["paper.publication_date", "desc"],
    ["refutation.refutation_strength", "desc"]
  ]
}'
```

---

## Utility Scripts

### Save query to file and execute

```bash
# Save query
cat > query.json << 'EOF'
{
  "find": "nodes",
  "node_pattern": {
    "node_type": "drug"
  },
  "edge_pattern": {
    "relation_type": "treats",
    "min_confidence": 0.7
  },
  "filters": [
    {
      "field": "target.name",
      "operator": "eq",
      "value": "diabetes"
    }
  ],
  "limit": 20
}
EOF

# Execute
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json
```

### Pretty-print results with jq

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json | jq '.results[] | {name: .["drug.name"], papers: .paper_count}'
```

### Extract specific fields

```bash
# Extract just drug names
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json | jq -r '.results[].["drug.name"]'
```

### Export to CSV

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json | \
  jq -r '.results[] | [.["drug.name"], .paper_count, .avg_confidence] | @csv' > results.csv
```

---

## Authentication Examples

### Using API key in header (recommended)

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json
```

### Using Basic Auth

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -u username:password \
  -d @query.json
```

### Using OAuth token

```bash
# Get token
TOKEN=$(curl -X POST $MEDGRAPH_SERVER/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  | jq -r '.access_token')

# Use token
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Authorization: Bearer $TOKEN" \
  -d @query.json
```

## Example 23: Find Drugs that Treat Breast Cancer

**Which drugs treat breast cancer and what's the evidence?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "relationships",
  "filters": [
    {
      "field": "object.name",
      "operator": "eq",
      "value": "Breast Cancer"
    },
    {
      "field": "predicate",
      "operator": "eq",
      "value": "TREATS"
    }
  ],
  "return_fields": [
    "subject.name",
    "subject.type",
    "predicate",
    "confidence",
    "evidence_count",
    "papers"
  ],
  "order_by": [["confidence", "desc"]]
}'
```

**Example response:**

```json
{
  "status": "success",
  "results": [
    {
      "subject.name": "Olaparib",
      "subject.type": "drug",
      "predicate": "TREATS",
      "confidence": 0.92,
      "evidence_count": 1,
      "papers": ["PMC123456"]
    }
  ]
}
```

---

## Example 24: Trace Metformin's Mechanism of Action

**How does metformin lower blood sugar?**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "filters": [{"field": "name", "operator": "eq", "value": "Metformin"}],
      "var": "drug"
    },
    "edges": [
      [
        {"relation_type": "activates", "var": "activation"},
        {"node_type": "protein", "var": "protein"}
      ],
      [
        {"relation_type": "downregulates", "var": "downreg"},
        {"node_type": "biomarker", "var": "marker"}
      ]
    ],
    "max_hops": 2
  },
  "return_fields": [
    "drug.name",
    "protein.name",
    "marker.name",
    "activation.confidence",
    "downreg.confidence"
  ]
}'
```

**Example response:**

```json
{
  "status": "success",
  "results": [
    {
      "drug.name": "Metformin",
      "protein.name": "AMPK",
      "marker.name": "Glycated Hemoglobin",
      "activation.confidence": 0.90,
      "downreg.confidence": 0.88,
      "path": [
        "Metformin -> ACTIVATES -> AMPK -> DOWNREGULATES -> HbA1c"
      ]
    }
  ]
}
```

---

## Example 25: Find Papers Supporting a Relationship

**Get the actual papers that show metformin treats diabetes:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "papers",
  "filters": [
    {
      "field": "relationships.subject.name",
      "operator": "eq",
      "value": "Metformin"
    },
    {
      "field": "relationships.object.name",
      "operator": "eq",
      "value": "Type 2 Diabetes"
    },
    {
      "field": "relationships.predicate",
      "operator": "eq",
      "value": "TREATS"
    }
  ],
  "return_fields": [
    "paper_id",
    "title",
    "authors",
    "publication_date",
    "journal"
  ]
}'
```

**Example response:**

```json
{
  "status": "success",
  "results": [
    {
      "paper_id": "PMC234567",
      "title": "Metformin Activation of AMPK and Effects on Glycemic Control",
      "authors": ["Zhou G", "Myers R", "Li Y", "Chen Y", "Shen X"],
      "publication_date": "2018-03-15",
      "journal": "Journal of Clinical Investigation"
    },
    {
      "paper_id": "PMC345678",
      "title": "Long-term Metformin Use in Type 2 Diabetes: A Cohort Study",
      "authors": ["Turner RC", "Holman RR", "Cull CA", "Stratton IM"],
      "publication_date": "2019-06-22",
      "journal": "Diabetes Care"
    }
  ]
}
```

---

## Example 26: Multi-hop Query - Aspirin Prevention Path

**Find what aspirin prevents and the evidence quality:**

```bash
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "paths",
  "path_pattern": {
    "start": {
      "node_type": "drug",
      "filters": [{"field": "name", "operator": "eq", "value": "Aspirin"}],
      "var": "drug"
    },
    "edges": [
      [
        {"relation_type": "prevents", "var": "prevention"},
        {"node_type": "disease", "var": "disease"}
      ]
    ],
    "max_hops": 1
  },
  "return_fields": [
    "drug.name",
    "disease.name",
    "prevention.confidence",
    "prevention.evidence_count",
    "prevention.metadata.risk_reduction",
    "prevention.metadata.study_type"
  ]
}'
```

**Example response:**

```json
{
  "status": "success",
  "results": [
    {
      "drug.name": "Aspirin",
      "disease.name": "Myocardial Infarction",
      "prevention.confidence": 0.82,
      "prevention.evidence_count": 2,
      "prevention.metadata": {
        "risk_reduction": 0.25,
        "study_type": "meta_analysis"
      }
    }
  ]
}
```

---

## Example 27: Entity Search by Type

**List all drugs in the knowledge graph:**

```bash
curl -X GET "$MEDGRAPH_SERVER/api/v1/entities?entity_type=drug&limit=10" \
  -H "Authorization: Bearer $API_KEY"
```

**Example response:**

```json
{
  "entities": [
    {
      "id": "RxNorm:1187832",
      "type": "drug",
      "name": "Olaparib",
      "canonical_id": "RxNorm:1187832",
      "mentions": 342
    },
    {
      "id": "RxNorm:860975",
      "type": "drug",
      "name": "Metformin",
      "canonical_id": "RxNorm:860975",
      "mentions": 2847
    },
    {
      "id": "RxNorm:1191",
      "type": "drug",
      "name": "Aspirin",
      "canonical_id": "RxNorm:1191",
      "mentions": 4123
    }
  ],
  "total": 3
}
```

---

## Example 28: Get Knowledge Graph Statistics

**What's in the graph?**

```bash
curl -X GET "$MEDGRAPH_SERVER/api/v1/stats" \
  -H "Authorization: Bearer $API_KEY"
```

**Example response:**

```json
{
  "total_entities": 8,
  "total_relationships": 5,
  "total_papers": 4,
  "entity_types": {
    "disease": 3,
    "drug": 3,
    "protein": 1,
    "biomarker": 1
  },
  "relationship_types": {
    "TREATS": 2,
    "ACTIVATES": 1,
    "DOWNREGULATES": 1,
    "PREVENTS": 1
  },
  "last_updated": "2025-12-08T23:30:00"
}
```

---

## Testing the Mini Server

To test these examples against the synthetic data server:

```bash
# Start the mini server
cd tests/mini_server
python server.py

# In another terminal, run the curl commands
export MEDGRAPH_SERVER="http://localhost:8000"
export API_KEY="test-key"  # Not validated in dev server

# Try a simple query
curl -X POST $MEDGRAPH_SERVER/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"find": "entities", "limit": 5}'
```
