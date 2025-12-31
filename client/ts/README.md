# @medgraph/client

TypeScript/JavaScript client library for the Medical Knowledge Graph API.

Query medical research papers, drug-disease relationships, gene associations, and more through a powerful graph database built on PubMed/PMC data.

## Features

- 🔍 **Powerful Query Builder** - Fluent API for constructing complex graph queries
- 🧬 **Medical Entity Types** - Drugs, diseases, genes, proteins, symptoms, and more
- 🔗 **Relationship Discovery** - Find treatments, mechanisms, associations, contradictions
- 📊 **Aggregation & Analytics** - Group, count, average across papers and evidence
- 🎯 **Type-Safe** - Full TypeScript support with comprehensive types
- ⚡ **Performance** - Batch queries, pagination, configurable timeouts
- 🛠️ **Convenience Methods** - Pre-built queries for common use cases

## Installation

```bash
# To install dependencies:
cd client/ts
npm install

# To use as a local package:
npm link
```

## Quick Start

```typescript
import { MedicalGraphClient } from '@medgraph/client';

const client = new MedicalGraphClient({
  baseUrl: 'https://api.medgraph.example.com',
  apiKey: 'your-api-key' // optional
});

// Find treatments for a disease
const treatments = await client.findTreatments('breast cancer', {
  minConfidence: 0.7,
  limit: 20
});

console.log(treatments.results);
// [
//   { 'drug.name': 'tamoxifen', paper_count: 234, avg_confidence: 0.89 },
//   { 'drug.name': 'trastuzumab', paper_count: 189, avg_confidence: 0.92 }
// ]
```

## Usage Examples

### Convenience Methods

```typescript
// Find treatments
const treatments = await client.findTreatments('diabetes');

// Find associated genes
const genes = await client.findDiseaseGenes('Alzheimer disease');

// Find diagnostic tests
const tests = await client.findDiagnosticTests('lupus');

// Find drug mechanisms
const mechanism = await client.findDrugMechanisms('metformin');

// Compare treatment evidence
const comparison = await client.compareTreatmentEvidence(
  'hypertension',
  ['lisinopril', 'losartan', 'amlodipine']
);

// Search by symptoms (differential diagnosis)
const diseases = await client.searchBySymptoms([
  'fatigue',
  'joint pain',
  'butterfly rash'
]);

// Find contradictory evidence
const contradictions = await client.findContradictoryEvidence(
  'aspirin',
  'myocardial infarction'
);
```

### Query Builder

Build custom queries with the fluent API:

```typescript
import { MedicalGraphClient, QueryBuilder, EntityType, PredicateType } from '@medgraph/client';

const query = new QueryBuilder()
  .findNodes(EntityType.GENE)
  .withEdge(PredicateType.ASSOCIATED_WITH, {
    direction: 'incoming',
    minConfidence: 0.6
  })
  .filterTarget(EntityType.DISEASE, { 
    namePattern: '.*cancer.*' 
  })
  .aggregate(
    ['gene.name'],
    {
      paper_count: ['count', 'rel.evidence.paper_id'],
      avg_confidence: ['avg', 'rel.confidence']
    }
  )
  .orderBy('paper_count', 'desc')
  .limit(50)
  .build();

const results = await client.execute(query);
```

### Multi-Hop Path Queries

```typescript
// Find drug repurposing opportunities
// Disease -> Gene -> Protein -> Drug pathway

const query: GraphQuery = {
  find: 'paths',
  path_pattern: {
    start: {
      node_type: EntityType.DISEASE,
      name: 'Alzheimer disease',
      var: 'disease'
    },
    edges: [
      {
        edge: {
          relation_types: [PredicateType.ASSOCIATED_WITH],
          min_confidence: 0.6
        },
        node: { node_type: EntityType.GENE, var: 'gene' }
      },
      {
        edge: { relation_type: PredicateType.ENCODES },
        node: { node_type: EntityType.PROTEIN, var: 'protein' }
      },
      {
        edge: {
          relation_types: [PredicateType.BINDS_TO, PredicateType.INHIBITS],
          direction: 'incoming'
        },
        node: {
          node_type: EntityType.DRUG,
          property_filters: [
            { field: 'properties.fda_approved', operator: 'eq', value: true }
          ]
        }
      }
    ],
    max_hops: 3
  }
};

const candidates = await client.execute(query);
```

### Batch Queries

Execute multiple queries in parallel:

```typescript
const results = await client.batch([
  {
    id: 'treatments',
    query: new QueryBuilder()
      .findNodes(EntityType.DRUG)
      .withEdge(PredicateType.TREATS)
      .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
      .limit(10)
      .build()
  },
  {
    id: 'genes',
    query: new QueryBuilder()
      .findNodes(EntityType.GENE)
      .withEdge(PredicateType.ASSOCIATED_WITH, { direction: 'incoming' })
      .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
      .limit(10)
      .build()
  }
]);

console.log('Treatments:', results.treatments);
console.log('Genes:', results.genes);
```

### Pagination

```typescript
async function getAllResults(disease: string) {
  const pageSize = 20;
  let offset = 0;
  let allResults = [];
  let hasMore = true;

  while (hasMore) {
    const query = new QueryBuilder()
      .findNodes(EntityType.DRUG)
      .withEdge(PredicateType.TREATS)
      .filterTarget(EntityType.DISEASE, { name: disease })
      .limit(pageSize)
      .offset(offset)
      .build();

    const page = await client.execute(query);
    allResults.push(...page.results);

    hasMore = page.results.length === pageSize;
    offset += pageSize;
  }

  return allResults;
}
```

## API Reference

### MedicalGraphClient

#### Constructor

```typescript
new MedicalGraphClient(config: ClientConfig | string)
```

**ClientConfig:**
- `baseUrl: string` - API endpoint URL
- `apiKey?: string` - Optional API key for authentication
- `timeout?: number` - Request timeout in milliseconds (default: 30000)
- `headers?: Record<string, string>` - Additional headers

#### Methods

**`execute<T>(query: GraphQuery): Promise<QueryResult<T>>`**  
Execute a graph query

**`executeRaw<T>(queryDict: Record<string, any>): Promise<QueryResult<T>>`**  
Execute a raw query object

**`findTreatments(disease: string, options?): Promise<QueryResult>`**  
Find drugs that treat a disease

**`findDiseaseGenes(disease: string, options?): Promise<QueryResult>`**  
Find genes associated with a disease

**`findDiagnosticTests(disease: string, options?): Promise<QueryResult>`**  
Find diagnostic tests for a disease

**`findDrugMechanisms(drugName: string): Promise<QueryResult>`**  
Find mechanism of action for a drug

**`compareTreatmentEvidence(disease: string, drugs: string[]): Promise<QueryResult>`**  
Compare evidence quality across treatments

**`searchBySymptoms(symptoms: string[], options?): Promise<QueryResult>`**  
Differential diagnosis from symptoms

**`findContradictoryEvidence(drug: string, disease: string): Promise<QueryResult>`**  
Find contradictory relationships

**`getPaperDetails(paperId: string): Promise<QueryResult>`**  
Get details about a specific paper

**`batch(queries: Array<{id: string, query: GraphQuery}>): Promise<Record<string, QueryResult>>`**  
Execute multiple queries in parallel

### QueryBuilder

Fluent API for building graph queries:

- `findNodes(nodeType, options?)` - Start node query
- `findEdges(relationType?, options?)` - Start edge query
- `findPaths(startPattern)` - Start path query
- `withEdge(relationType, options?)` - Add edge pattern
- `addPathStep(edge, node)` - Add path step
- `pathConstraints(options)` - Set path constraints
- `filterTarget(nodeType, options?)` - Filter target nodes
- `filter(field, operator, value)` - Add custom filter
- `aggregate(groupBy, aggregations)` - Add aggregation
- `orderBy(field, direction?)` - Add ordering
- `limit(n)` - Limit results
- `offset(n)` - Offset results
- `returnFields(...fields)` - Specify return fields
- `build()` - Build final query

### Entity Types

```typescript
enum EntityType {
  DISEASE, SYMPTOM, DRUG, GENE, PROTEIN,
  ANATOMICAL_STRUCTURE, PROCEDURE, TEST,
  BIOMARKER, PAPER, AUTHOR, INSTITUTION,
  CLINICAL_TRIAL, MEASUREMENT
}
```

### Relationship Types

```typescript
enum PredicateType {
  // Causal
  CAUSES, PREVENTS, INCREASES_RISK, DECREASES_RISK,
  
  // Treatment
  TREATS, MANAGES, CONTRAINDICATES,
  
  // Biological
  BINDS_TO, INHIBITS, ACTIVATES,
  UPREGULATES, DOWNREGULATES, ENCODES,
  
  // Clinical
  DIAGNOSES, INDICATES, ASSOCIATED_WITH,
  
  // Provenance
  CITES, CONTRADICTS, SUPPORTS
}
```

## Framework Integration

### React

```typescript
import { useState, useEffect } from 'react';
import { MedicalGraphClient } from '@medgraph/client';

const client = new MedicalGraphClient(process.env.REACT_APP_API_URL);

function DiseaseSearch() {
  const [disease, setDisease] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const data = await client.findTreatments(disease);
      setResults(data.results);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input value={disease} onChange={e => setDisease(e.target.value)} />
      <button onClick={search}>Search</button>
      {loading ? <p>Loading...</p> : (
        <ul>
          {results.map((r, i) => (
            <li key={i}>{r['drug.name']}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### Express.js

```typescript
import express from 'express';
import { MedicalGraphClient } from '@medgraph/client';

const app = express();
const client = new MedicalGraphClient(process.env.API_URL);

app.post('/api/treatments', async (req, res) => {
  try {
    const results = await client.findTreatments(req.body.disease);
    res.json(results);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000);
```

### Next.js API Route

```typescript
// app/api/treatments/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { MedicalGraphClient } from '@medgraph/client';

const client = new MedicalGraphClient(process.env.API_URL);

export async function POST(request: NextRequest) {
  const { disease } = await request.json();
  const results = await client.findTreatments(disease);
  return NextResponse.json(results);
}
```

## Environment Configuration

Example configuration (replace with your actual API endpoint):

```bash
# .env (example)
MEDGRAPH_API_URL=https://api.medgraph.example.com
MEDGRAPH_API_KEY=your_api_key_here
MEDGRAPH_TIMEOUT=30000
```

```typescript
import { MedicalGraphClient } from '@medgraph/client';

const client = new MedicalGraphClient({
  baseUrl: process.env.MEDGRAPH_API_URL,
  apiKey: process.env.MEDGRAPH_API_KEY,
  timeout: parseInt(process.env.MEDGRAPH_TIMEOUT || '30000')
});
```

## Error Handling

```typescript
try {
  const results = await client.findTreatments('disease');
} catch (error) {
  if (error instanceof Error) {
    console.error('Query failed:', error.message);
    
    if (error.name === 'AbortError') {
      console.error('Request timed out');
    }
  }
}
```

## TypeScript

Full TypeScript support with comprehensive types:

```typescript
import { 
  MedicalGraphClient,
  QueryBuilder,
  EntityType,
  PredicateType,
  GraphQuery,
  QueryResult,
  NodePattern,
  EdgePattern
} from '@medgraph/client';

// Define custom result types
interface TreatmentResult {
  'drug.name': string;
  paper_count: number;
  avg_confidence: number;
}

const results = await client.execute<TreatmentResult>(query);
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://docs.medgraph.example.com)
- [API Reference](https://api.medgraph.example.com/docs)
- [GitHub Repository](https://github.com/yourusername/medgraph-client)
- [Issues](https://github.com/yourusername/medgraph-client/issues)

## Related Projects

- [Python Client](../python/README.md)
- [MCP Server](../../mcp/server.py)
