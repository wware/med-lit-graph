# Medical Knowledge Graph API - curl Examples

Complete set of curl examples for querying the medical knowledge graph API.

## Setup

```bash
# Set your API endpoint and key
export API_BASE="https://api.medgraph.example.com"
export API_KEY="your-api-key-here"

# Helper function for authenticated requests
function mgraph() {
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        "$API_BASE/api/v1/query" \
        -d "$1"
}
```

---

## Example 1: Find Treatments for a Disease

**Find drugs that treat breast cancer:**

```bash
curl -X POST https://api.medgraph.example.com/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
          "relation_type": "symptom_of",
          "direction": "outgoing",
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
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
          "relation_types": ["interacts_with", "potentiates", "antagonizes"],
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "limit": 20,
  "offset": 0
}'

# Page 2 (results 20-39)
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/batch \
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
curl -X POST $API_BASE/api/v1/query \
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
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json
```

### Pretty-print results with jq

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json | jq '.results[] | {name: .["drug.name"], papers: .paper_count}'
```

### Extract specific fields

```bash
# Extract just drug names
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json | jq -r '.results[].["drug.name"]'
```

### Export to CSV

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json | \
  jq -r '.results[] | [.["drug.name"], .paper_count, .avg_confidence] | @csv' > results.csv
```

---

## Authentication Examples

### Using API key in header (recommended)

```bash
curl -X POST $API_BASE/api/v1/query \
  -H "Authorization: Bearer $API_KEY" \
  -d @query.json
```

### Using Basic Auth

```bash
curl -X POST $API_BASE/api/v1/query \
  -u username:password \
  -d @query.json
```

### Using OAuth token

```bash
# Get token
TOKEN=$(curl -X POST $API_BASE/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  | jq -r '.access_token')

# Use token
curl -X POST $API_BASE/api/v1/query \
  -H "Authorization: Bearer $TOKEN" \
  -d @query.json
```
