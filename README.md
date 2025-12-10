# Medical Knowledge Graph

> **A provenance-first knowledge graph for medical research built on PubMed/PMC literature**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

Transform millions of medical research papers into a queryable knowledge graph with full citation traceability. Every relationship is backed by specific evidence from peer-reviewed literature, enabling doctors and researchers to verify every claim.

**🔬 Try it**: [Demo](https://demo.medgraph.example.com) | [API Docs](https://api.medgraph.example.com/docs) | [Examples](examples/)

---

## Why This Project Exists

My partner's doctor spent weeks being a diagnostic detective—correlating obscure symptoms across dozens of medical papers to find the right diagnosis. Most doctors don't have that time or tenacity, so patients suffer with wrong diagnoses for years.

**This project makes every doctor that kind of bloodhound.**

---

## Quick Example

**Question**: "What drugs treat BRCA-mutated breast cancer?"

**Python**:
```python
from medgraph import MedicalGraphClient

client = MedicalGraphClient("https://api.medgraph.com")
results = client.find_treatments("BRCA-mutated breast cancer")

for drug in results.results:
    print(f"{drug['name']}: {drug['paper_count']} papers, {drug['avg_confidence']:.2f} confidence")
    print(f"  Evidence: {drug['source_papers'][0]}")  # PMC ID with full trace
```

**curl**:
```bash
curl -X POST https://api.medgraph.com/api/v1/query -d '{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "edge_pattern": {"relation_type": "treats", "min_confidence": 0.7},
  "filters": [{"field": "target.name", "operator": "contains", "value": "BRCA"}]
}'
```

Every result includes PMC paper IDs, section locations, and extraction methods so doctors can verify the claims.

---

## Key Features

🔍 **Provenance-First**: Every relationship traceable to specific papers, sections, and paragraphs  
🔗 **Graph-Native**: Multi-hop queries across millions of relationships  
📊 **Evidence-Weighted**: Automatic quality scoring (RCT > meta-analysis > case report)  
🌐 **Vendor-Neutral**: JSON query language works with any graph database  
🔓 **Open Source**: Schema, query language, and client libraries all public  
🤖 **LLM-Ready**: MCP server for Claude, ChatGPT, and other AI assistants  

---

## Architecture

```
User Interfaces
├── Python Client Library
├── TypeScript/JavaScript Client
├── REST API (curl)
└── MCP Server (for LLMs)
         │
    Query API (FastAPI)
         │
    ┌────┴────┬──────────┬────────┐
OpenSearch  Neptune     S3
(Vector)    (Graph)   (JSON Source)
```

**Data Flow**:
```
PubMed/PMC → Ingestion Pipeline → Per-Paper JSON (Source of Truth)
                                         │
                         ┌───────────────┴───────────────┐
                   OpenSearch                        Neptune
                  (Semantic Search)              (Graph Queries)
```

[Full architecture docs →](docs/architecture.md)

---

## Design Principles

### 1. Provenance is Mandatory

**Every medical claim must be traceable.**

```python
# ❌ This FAILS validation - no evidence
treats = Treats(
    subject_id="RxNorm:1187832",  # Olaparib
    object_id="UMLS:C0006142",    # Breast Cancer
    response_rate=0.59
)

# ✅ This WORKS - evidence required
treats = Treats(
    subject_id="RxNorm:1187832",
    object_id="UMLS:C0006142",
    evidence=[
        Evidence(
            paper_id="PMC999888",
            section_type="results",
            paragraph_idx=8,
            extraction_method="table_parser",
            confidence=0.92,
            study_type="rct",
            sample_size=302
        )
    ],
    response_rate=0.59
)
```

**Why this matters**:
- Doctors can click through to verify claims
- Researchers can audit data quality
- System filters by study quality (RCTs vs case reports)
- Confidence scores are evidence-based, not arbitrary

### 2. Immutable JSON Source of Truth

Graph databases can corrupt. Algorithms improve. Papers get retracted.

**Solution**: Per-paper JSON files are immutable source of truth.
- Graph database regenerates from JSON
- Paper retracted? Remove JSON, rebuild graph
- Better NER model? Re-process, regenerate graph

**Trade-off**: Extra storage (~1-5MB per paper) for complete reproducibility.

### 3. Vendor-Neutral Query Language

Different graph databases use different query languages (Cypher, Gremlin, SPARQL).

**Solution**: JSON query language that translates to any backend.

```json
{
  "find": "paths",
  "path_pattern": {
    "start": {"node_type": "disease", "name": "Alzheimer disease"},
    "edges": [
      {"edge": {"relation_type": "associated_with"}, "node": {"node_type": "gene"}},
      {"edge": {"relation_type": "encodes"}, "node": {"node_type": "protein"}},
      {"edge": {"relation_type": "binds_to", "direction": "incoming"}, 
       "node": {"node_type": "drug"}}
    ]
  }
}
```

Translates to openCypher (Neptune), Cypher (Neo4j), or Gremlin.

**Benefits**:
- LLM-friendly (JSON is easy for AI to generate)
- Database-agnostic (switch backends without rewriting queries)
- Human-readable
- Programmatically composable

### 4. Evidence Quality Weighting

Not all studies are equal. RCTs > observational studies > case reports.

**Automatic quality weighting**:
```python
study_weights = {
    'rct': 1.0,              # Gold standard
    'meta_analysis': 0.95,
    'cohort': 0.8,
    'observational': 0.6,
    'case_report': 0.4
}
```

Confidence scores = weighted average of evidence quality.

### 5. Graph RAG (Not Just Vector Search)

Pure vector search misses multi-hop connections. Pure graph misses semantic similarity.

**Hybrid approach**:
1. **Vector search**: Find relevant papers semantically
2. **Graph traversal**: Discover multi-hop relationships
3. **Combine**: Rank by both relevance and graph structure

**Example**: "Drugs for BRCA-mutated breast cancer"
- Vector: Find papers about BRCA, breast cancer, treatments
- Graph: BRCA1 → increases_risk → breast cancer → treated_by → olaparib
- Result: Drugs with evidence for BRCA-mutated subtype specifically

[Complete design decisions →](docs/design-principles.md)

---

## Schema

### Entity Types
- **Medical**: disease, symptom, drug, gene, protein, pathway, biomarker, test, procedure
- **Research**: paper, author, institution, clinical_trial

### Relationship Types
- **Causal**: causes, prevents, increases_risk, decreases_risk
- **Treatment**: treats, manages, contraindicates, side_effect
- **Biological**: encodes, binds_to, inhibits, activates, upregulates, downregulates
- **Clinical**: diagnoses, indicates, precedes, associated_with
- **Provenance**: cites, studied_in, authored_by

Every medical relationship includes:
```python
class MedicalRelationship:
    evidence: list[Evidence]  # MANDATORY, min_length=1
    confidence: float          # Auto-calculated from evidence
    source_papers: list[str]   # Auto-populated
    contradicted_by: list[str] # Track conflicts
```

[Full schema documentation →](schema/unified_schema.py)

---

## Query Language

### Simple Node Query
```json
{
  "find": "nodes",
  "node_pattern": {"node_type": "drug"},
  "edge_pattern": {"relation_type": "treats"},
  "filters": [{"field": "target.name", "operator": "eq", "value": "diabetes"}]
}
```

### Multi-Hop Path Query
```json
{
  "find": "paths",
  "path_pattern": {
    "start": {"node_type": "symptom", "name": ["fatigue", "joint pain"]},
    "edges": [
      {"edge": {"relation_type": "symptom_of"}, "node": {"node_type": "disease"}}
    ]
  },
  "aggregate": {
    "group_by": ["disease.name"],
    "aggregations": {"symptom_count": ["count", "symptom.name"]}
  }
}
```

### Evidence Quality Filtering
```json
{
  "edge_pattern": {"relation_type": "treats", "min_confidence": 0.8},
  "filters": [
    {"field": "edge.evidence.study_type", "operator": "in", "value": ["rct", "meta_analysis"]}
  ]
}
```

[Query language specification →](docs/query-language.md) | [More examples →](docs/query-examples.md)

---

## Client Libraries

### Python
```bash
pip install medgraph-client
```

```python
from medgraph import MedicalGraphClient, QueryBuilder

client = MedicalGraphClient("https://api.medgraph.com")

# High-level convenience methods
treatments = client.find_treatments("diabetes")
genes = client.find_disease_genes("Alzheimer disease")
tests = client.find_diagnostic_tests("lupus")

# Custom queries with builder
query = (QueryBuilder()
    .find_nodes("gene")
    .with_edge("associated_with", min_confidence=0.7)
    .filter_target("disease", name="breast cancer")
    .aggregate(["gene.name"], paper_count=("count", "rel.evidence.paper_id"))
    .limit(20)
    .build())

results = client.execute(query)
```

[Python docs →](clients/python/) | [API reference →](clients/python/api.md)

### TypeScript/JavaScript
```bash
npm install @medgraph/client
```

```typescript
import { MedicalGraphClient, QueryBuilder, EntityType, RelationType } from '@medgraph/client';

const client = new MedicalGraphClient('https://api.medgraph.com');

const treatments = await client.findTreatments('diabetes');

const query = new QueryBuilder()
  .findNodes(EntityType.GENE)
  .withEdge(RelationType.ASSOCIATED_WITH, { minConfidence: 0.7 })
  .filterTarget(EntityType.DISEASE, { name: 'breast cancer' })
  .build();

const results = await client.execute(query);
```

[TypeScript docs →](clients/typescript/) | [API reference →](clients/typescript/api.md)

### MCP Server (for LLMs)

Enable Claude, ChatGPT, or other AI assistants to query medical knowledge:

```bash
npm install -g @medgraph/mcp-server
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "medgraph": {
      "command": "npx",
      "args": ["@medgraph/mcp-server"],
      "env": {
        "MEDGRAPH_API_URL": "https://api.medgraph.com"
      }
    }
  }
}
```

Now ask Claude:
> "What drugs treat BRCA-mutated breast cancer? Show me the evidence."

Claude will query the graph and cite specific papers.

[MCP server docs →](mcp-server/)

---

## Use Cases

### 1. Clinical Decision Support
**Differential diagnosis from symptoms**
```python
diseases = client.search_by_symptoms(["fatigue", "joint pain", "butterfly rash"])
# Returns: systemic lupus erythematosus, rheumatoid arthritis, ...
```

### 2. Drug Repurposing
**Find FDA-approved drugs targeting Alzheimer's-associated proteins**
```python
query = multi_hop_query(
    start="Alzheimer disease",
    path="disease → gene → protein → drug"
)
```

### 3. Evidence Synthesis
**Compare treatment evidence quality**
```python
comparison = client.compare_treatment_evidence(
    "hypertension",
    ["lisinopril", "losartan", "amlodipine"]
)
# Shows: RCT count, meta-analysis count, sample sizes
```

### 4. Literature Review Automation
**Generate systematic review of gene-disease associations**
```python
genes = client.find_disease_genes("breast cancer", min_confidence=0.8)
# Export to citation manager, generate report
```

### 5. Pharmacovigilance
**Identify drug-drug interactions**
```python
interactions = client.find_drug_interactions("warfarin", severity=["major"])
```

[More use cases →](docs/use-cases.md)

---

## Deployment

### Local Development
```bash
git clone https://github.com/yourusername/medical-knowledge-graph.git
cd medical-knowledge-graph
docker-compose up -d
```

Services:
- OpenSearch: http://localhost:9200
- API: http://localhost:8000
- Dashboards: http://localhost:5601

### AWS Budget Deployment (~$50/month)
```bash
cd infrastructure/cdk
cdk bootstrap
cdk deploy MedicalKgBudgetStack
```

Components:
- Single OpenSearch t3.small instance
- S3 for paper storage
- Lambda for ingestion
- VPC endpoints (no NAT)

### AWS Production (~$1000-1500/month)
```bash
cdk deploy MedicalKgProductionStack
```

Components:
- Multi-AZ OpenSearch cluster
- Neptune graph database
- ECS Fargate services
- Application Load Balancer
- Auto-scaling + monitoring

[Deployment guide →](docs/deployment.md)

---

## Roadmap

**Phase 1 (Current)**: Core Infrastructure
- [x] Schema with mandatory provenance
- [x] JSON query language
- [x] Python + TypeScript clients
- [ ] AWS deployment scripts

**Phase 2 (Q1 2026)**: Data & Quality
- [ ] Ingest 10,000 papers (POC)
- [ ] Entity resolution & deduplication
- [ ] Contradiction detection
- [ ] Quality metrics dashboard

**Phase 3 (Q2 2026)**: Query Capabilities
- [ ] Multi-hop path queries
- [ ] Temporal queries
- [ ] Aggregation & analytics
- [ ] RDF export

**Phase 4 (Q3 2026)**: User Interfaces
- [ ] Web query interface
- [ ] Visualization dashboard
- [ ] MCP server
- [ ] Example notebooks

**Phase 5 (Q4 2026)**: Scale
- [ ] 100,000+ papers
- [ ] Query optimization
- [ ] Real-time updates
- [ ] Multi-region

[Detailed roadmap →](docs/roadmap.md)

---

## Contributing

We need help from:
- **Medical professionals**: Validate entity extraction and relationships
- **NLP/ML engineers**: Improve entity recognition
- **Data engineers**: Scale ingestion pipeline
- **Frontend developers**: Build query interfaces
- **Technical writers**: Documentation and tutorials

### How to Contribute
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Open a Pull Request

[Contributing guide →](CONTRIBUTING.md) | [Code of conduct →](CODE_OF_CONDUCT.md)

---

## License

MIT License - see [LICENSE](LICENSE)

**Data licensing**: The schema/code is MIT, but extracted data from PubMed/PMC is subject to [PMC Open Access terms](https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/).

---

## Links

- **Documentation**: https://docs.medgraph.com
- **API Reference**: https://api.medgraph.com/docs
- **Demo**: https://demo.medgraph.com
- **Discussions**: https://github.com/yourusername/medical-knowledge-graph/discussions
- **Issues**: https://github.com/yourusername/medical-knowledge-graph/issues

---

## Contact

- Email: contact@medgraph.com
- Twitter: @medgraph
- Discord: [Join our community](https://discord.gg/medgraph)

---

## Disclaimer

⚠️ **This is a research tool and clinical decision support aid.**

It is NOT:
- A substitute for professional medical advice
- FDA-approved for diagnostic use
- Validated for clinical decision-making

**Always consult qualified healthcare professionals for medical decisions.**

---

## Acknowledgments

- **PubMed/PMC**: Making biomedical literature freely available
- **UMLS**: Comprehensive medical terminology
- **Anthropic**: MCP specification
- **Open source community**: Countless tools and libraries
- **My partner's doctor**: Inspiration for this project
