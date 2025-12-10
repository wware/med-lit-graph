# Medical Graph Client - TypeScript Examples

Comprehensive examples for using the TypeScript/JavaScript client library.

## Installation

```bash
npm install @medgraph/client
# or
yarn add @medgraph/client
# or
pnpm add @medgraph/client
```

## Basic Setup

```typescript
import { MedicalGraphClient, QueryBuilder, EntityType, RelationType } from '@medgraph/client';

// Initialize client
const client = new MedicalGraphClient({
  baseUrl: 'https://api.medgraph.example.com',
  apiKey: process.env.MEDGRAPH_API_KEY,
  timeout: 30000 // optional, defaults to 30s
});

// Or simple initialization
const client = new MedicalGraphClient('https://api.medgraph.example.com');
```

---

## Example 1: Simple Convenience Methods

```typescript
// Find treatments for a disease
const treatments = await client.findTreatments('breast cancer', {
  minConfidence: 0.7,
  limit: 20
});

console.log('Found treatments:', treatments.results);
// [
//   { 'drug.name': 'tamoxifen', paper_count: 234, avg_confidence: 0.89 },
//   { 'drug.name': 'trastuzumab', paper_count: 189, avg_confidence: 0.92 }
// ]

// Find genes associated with a disease
const genes = await client.findDiseaseGenes('Alzheimer disease', {
  minConfidence: 0.6,
  limit: 50
});

// Find diagnostic tests
const tests = await client.findDiagnosticTests('systemic lupus erythematosus');

// Get drug mechanism
const mechanism = await client.findDrugMechanisms('metformin');
```

---

## Example 2: Query Builder - Basic

```typescript
// Build a custom query
const query = new QueryBuilder()
  .findNodes(EntityType.DRUG)
  .withEdge(RelationType.TREATS, { minConfidence: 0.7 })
  .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
  .orderBy('confidence', 'desc')
  .limit(10)
  .build();

const results = await client.execute(query);
```

---

## Example 3: Query Builder - Advanced Aggregation

```typescript
const query = new QueryBuilder()
  .findNodes(EntityType.GENE)
  .withEdge(RelationType.ASSOCIATED_WITH, {
    direction: 'incoming',
    minConfidence: 0.6
  })
  .filterTarget(EntityType.DISEASE, { 
    namePattern: '.*breast cancer.*' 
  })
  .aggregate(
    ['gene.name'],
    {
      paper_count: ['count', 'rel.evidence.paper_id'],
      avg_confidence: ['avg', 'rel.confidence'],
      latest_study: ['max', 'rel.evidence.paper_publication_date']
    }
  )
  .orderBy('paper_count', 'desc')
  .limit(20)
  .build();

const genes = await client.execute(query);

genes.results.forEach(gene => {
  console.log(`${gene['gene.name']}: ${gene.paper_count} papers, confidence: ${gene.avg_confidence}`);
});
```

---

## Example 4: Multi-Hop Path Queries

```typescript
// Find drug repurposing opportunities
// Drug -> Protein -> Gene -> Disease pathway

const query: GraphQuery = {
  find: 'paths',
  path_pattern: {
    start: {
      node_type: EntityType.DISEASE,
      name: 'Alzheimer disease',
      var: 'alzheimers'
    },
    edges: [
      {
        edge: {
          relation_types: [RelationType.ASSOCIATED_WITH, RelationType.CAUSES],
          min_confidence: 0.6,
          var: 'disease_gene'
        },
        node: {
          node_type: EntityType.GENE,
          var: 'gene'
        }
      },
      {
        edge: {
          relation_type: RelationType.ENCODES,
          var: 'gene_protein'
        },
        node: {
          node_type: EntityType.PROTEIN,
          var: 'protein'
        }
      },
      {
        edge: {
          relation_types: [RelationType.BINDS_TO, RelationType.INHIBITS, RelationType.ACTIVATES],
          direction: 'incoming',
          var: 'drug_protein'
        },
        node: {
          node_type: EntityType.DRUG,
          property_filters: [
            {
              field: 'properties.fda_approved',
              operator: 'eq',
              value: true
            }
          ],
          var: 'drug'
        }
      }
    ],
    max_hops: 3,
    avoid_cycles: true
  },
  aggregate: {
    group_by: ['drug.name'],
    aggregations: {
      protein_targets: ['count', 'protein.name'],
      evidence_strength: ['avg', 'disease_gene.confidence']
    }
  },
  order_by: [
    ['protein_targets', 'desc'],
    ['evidence_strength', 'desc']
  ],
  limit: 10
};

const repurposingCandidates = await client.execute(query);
```

---

## Example 5: Using QueryBuilder for Multi-Hop

```typescript
const builder = new QueryBuilder()
  .findPaths({
    node_type: EntityType.DRUG,
    name: 'metformin',
    var: 'drug'
  })
  .addPathStep(
    {
      relation_types: [RelationType.BINDS_TO, RelationType.INHIBITS],
      var: 'interaction'
    },
    {
      node_type: EntityType.PROTEIN,
      var: 'target'
    }
  )
  .addPathStep(
    {
      relation_types: [RelationType.UPREGULATES, RelationType.DOWNREGULATES],
      var: 'regulation'
    },
    {
      node_type: EntityType.GENE,
      var: 'gene'
    }
  )
  .pathConstraints({ maxHops: 2, avoidCycles: true })
  .returnFields(
    'drug.name',
    'target.name',
    'gene.name',
    'interaction.relation_type',
    'regulation.relation_type'
  );

const pathways = await client.execute(builder.build());
```

---

## Example 6: Compare Treatment Evidence

```typescript
const comparison = await client.compareTreatmentEvidence(
  'hypercholesterolemia',
  ['atorvastatin', 'simvastatin', 'evolocumab', 'alirocumab']
);

// Display as a table
console.table(
  comparison.results.map(r => ({
    Drug: r['source.name'],
    'Total Papers': r.total_papers,
    'RCT Count': r.rct_count,
    'Avg Confidence': r.avg_confidence.toFixed(2)
  }))
);
```

---

## Example 7: Differential Diagnosis

```typescript
const symptoms = ['fatigue', 'joint pain', 'butterfly rash'];

const diseases = await client.searchBySymptoms(symptoms);

console.log('Possible diagnoses:');
diseases.results
  .filter(d => d.symptom_match_count >= 2)
  .forEach(d => {
    console.log(`- ${d['disease.name']}: ${d.symptom_match_count}/${symptoms.length} symptoms matched`);
  });
```

---

## Example 8: Batch Queries

```typescript
// Execute multiple queries in parallel
const batchResults = await client.batch([
  {
    id: 'treatments',
    query: new QueryBuilder()
      .findNodes(EntityType.DRUG)
      .withEdge(RelationType.TREATS)
      .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
      .limit(10)
      .build()
  },
  {
    id: 'genes',
    query: new QueryBuilder()
      .findNodes(EntityType.GENE)
      .withEdge(RelationType.ASSOCIATED_WITH, { direction: 'incoming' })
      .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
      .limit(10)
      .build()
  },
  {
    id: 'diagnostics',
    query: new QueryBuilder()
      .findNodes(EntityType.TEST)
      .withEdge(RelationType.DIAGNOSES)
      .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
      .build()
  }
]);

console.log('Treatments:', batchResults.treatments.results);
console.log('Associated genes:', batchResults.genes.results);
console.log('Diagnostic tests:', batchResults.diagnostics.results);
```

---

## Example 9: Find Contradictory Evidence

```typescript
const contradictions = await client.findContradictoryEvidence(
  'aspirin',
  'myocardial infarction'
);

console.log('Evidence breakdown:');
contradictions.results.forEach(r => {
  console.log(`${r['rel.relation_type']}: ${r.paper_count} papers (confidence: ${r.avg_confidence})`);
});

// Example output:
// prevents: 45 papers (confidence: 0.82)
// increases_risk: 3 papers (confidence: 0.65)
```

---

## Example 10: Pagination

```typescript
async function getAllTreatments(disease: string) {
  const pageSize = 20;
  let offset = 0;
  let allResults = [];
  let hasMore = true;

  while (hasMore) {
    const query = new QueryBuilder()
      .findNodes(EntityType.DRUG)
      .withEdge(RelationType.TREATS)
      .filterTarget(EntityType.DISEASE, { name: disease })
      .limit(pageSize)
      .offset(offset)
      .build();

    const page = await client.execute(query);
    allResults.push(...page.results);

    hasMore = page.metadata.has_more ?? page.results.length === pageSize;
    offset += pageSize;
  }

  return allResults;
}

const allTreatments = await getAllTreatments('breast cancer');
console.log(`Found ${allTreatments.length} total treatments`);
```

---

## Example 11: Error Handling

```typescript
import { MedicalGraphClient, type ApiError } from '@medgraph/client';

try {
  const results = await client.findTreatments('nonexistent disease');
} catch (error) {
  if (error instanceof Error) {
    console.error('Query failed:', error.message);
    
    // Parse error details if available
    if (error.message.includes('API Error:')) {
      // Handle API-specific errors
      console.error('Check your query parameters');
    }
  }
}

// With timeout handling
const clientWithShortTimeout = new MedicalGraphClient({
  baseUrl: 'https://api.medgraph.example.com',
  timeout: 5000 // 5 seconds
});

try {
  const results = await clientWithShortTimeout.execute(complexQuery);
} catch (error) {
  if (error.name === 'AbortError') {
    console.error('Query timed out after 5 seconds');
  }
}
```

---

## Example 12: React Integration

```typescript
import { useState, useEffect } from 'react';
import { MedicalGraphClient } from '@medgraph/client';

const client = new MedicalGraphClient(process.env.REACT_APP_API_URL);

function TreatmentSearch() {
  const [disease, setDisease] = useState('');
  const [treatments, setTreatments] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchTreatments = async () => {
    setLoading(true);
    try {
      const results = await client.findTreatments(disease);
      setTreatments(results.results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={disease}
        onChange={e => setDisease(e.target.value)}
        placeholder="Enter disease name"
      />
      <button onClick={searchTreatments} disabled={loading}>
        Search
      </button>
      
      {loading && <p>Loading...</p>}
      
      <ul>
        {treatments.map((t, i) => (
          <li key={i}>
            {t['drug.name']} - {t.paper_count} papers
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Example 13: Node.js CLI Tool

```typescript
#!/usr/bin/env node

import { Command } from 'commander';
import { MedicalGraphClient } from '@medgraph/client';

const program = new Command();
const client = new MedicalGraphClient(
  process.env.MEDGRAPH_API_URL || 'https://api.medgraph.example.com'
);

program
  .name('medgraph')
  .description('Medical Knowledge Graph CLI')
  .version('1.0.0');

program
  .command('treatments <disease>')
  .description('Find treatments for a disease')
  .option('-c, --confidence <number>', 'Minimum confidence', '0.6')
  .option('-l, --limit <number>', 'Result limit', '20')
  .action(async (disease, options) => {
    const results = await client.findTreatments(disease, {
      minConfidence: parseFloat(options.confidence),
      limit: parseInt(options.limit)
    });

    console.table(results.results);
  });

program
  .command('genes <disease>')
  .description('Find genes associated with a disease')
  .action(async (disease) => {
    const results = await client.findDiseaseGenes(disease);
    console.table(results.results);
  });

program.parse();

// Usage:
// $ medgraph treatments "breast cancer" --confidence 0.7
// $ medgraph genes "Alzheimer disease"
```

---

## Example 14: Express.js API Endpoint

```typescript
import express from 'express';
import { MedicalGraphClient } from '@medgraph/client';

const app = express();
const client = new MedicalGraphClient(process.env.MEDGRAPH_API_URL);

app.use(express.json());

app.post('/api/search/treatments', async (req, res) => {
  try {
    const { disease, minConfidence, limit } = req.body;
    
    const results = await client.findTreatments(disease, {
      minConfidence,
      limit
    });
    
    res.json(results);
  } catch (error) {
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Unknown error' 
    });
  }
});

app.post('/api/query/custom', async (req, res) => {
  try {
    const results = await client.execute(req.body);
    res.json(results);
  } catch (error) {
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Unknown error' 
    });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

---

## Example 15: TypeScript Type Safety

```typescript
// Define custom result types for type safety
interface TreatmentResult {
  'drug.name': string;
  paper_count: number;
  avg_confidence: number;
  total_evidence: number;
}

interface GeneResult {
  'gene.name': string;
  'gene.external_ids.hgnc': string;
  'rel.confidence': number;
  'rel.evidence.paper_id': string[];
}

// Use typed results
const treatments = await client.execute<TreatmentResult>(query);

treatments.results.forEach(treatment => {
  // TypeScript knows the shape of treatment
  console.log(`${treatment['drug.name']}: ${treatment.paper_count} papers`);
});

// Type-safe query builder
const typedQuery = new QueryBuilder()
  .findNodes(EntityType.DRUG)
  .withEdge(RelationType.TREATS, { minConfidence: 0.7 })
  .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
  .build();

// TypeScript ensures type safety throughout
const typedResults = await client.execute<TreatmentResult>(typedQuery);
```

---

## Testing Examples

```typescript
import { describe, it, expect, beforeAll } from 'vitest';
import { MedicalGraphClient, QueryBuilder, EntityType, RelationType } from '@medgraph/client';

describe('MedicalGraphClient', () => {
  let client: MedicalGraphClient;

  beforeAll(() => {
    client = new MedicalGraphClient({
      baseUrl: process.env.TEST_API_URL || 'http://localhost:8080',
      apiKey: process.env.TEST_API_KEY
    });
  });

  it('should find treatments for a disease', async () => {
    const results = await client.findTreatments('diabetes');
    
    expect(results.results).toBeDefined();
    expect(results.results.length).toBeGreaterThan(0);
    expect(results.metadata.total_results).toBeGreaterThan(0);
  });

  it('should build valid queries', () => {
    const query = new QueryBuilder()
      .findNodes(EntityType.DRUG)
      .withEdge(RelationType.TREATS)
      .limit(10)
      .build();

    expect(query.find).toBe('nodes');
    expect(query.node_pattern?.node_type).toBe(EntityType.DRUG);
    expect(query.limit).toBe(10);
  });

  it('should handle errors gracefully', async () => {
    await expect(
      client.execute({ find: 'nodes' as any })
    ).rejects.toThrow();
  });
});
```

---

## Performance Tips

```typescript
// 1. Reuse client instances
const globalClient = new MedicalGraphClient(API_URL);

// 2. Use batch queries for multiple related queries
const results = await globalClient.batch([
  { id: 'q1', query: query1 },
  { id: 'q2', query: query2 },
  { id: 'q3', query: query3 }
]);

// 3. Set appropriate limits
const query = new QueryBuilder()
  .findNodes(EntityType.DRUG)
  .limit(100) // Don't request more than you need
  .build();

// 4. Use pagination for large result sets
async function* paginateResults(baseQuery: GraphQuery, pageSize = 20) {
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const query = { ...baseQuery, limit: pageSize, offset };
    const page = await client.execute(query);
    
    yield page.results;
    
    hasMore = page.results.length === pageSize;
    offset += pageSize;
  }
}

// Usage
for await (const page of paginateResults(baseQuery)) {
  console.log('Processing page:', page);
}

// 5. Set reasonable timeouts
const client = new MedicalGraphClient({
  baseUrl: API_URL,
  timeout: 10000 // 10 seconds for most queries
});
```

---

## Environment Configuration

```typescript
// .env
MEDGRAPH_API_URL=https://api.medgraph.example.com
MEDGRAPH_API_KEY=your_api_key_here

// config.ts
export const config = {
  apiUrl: process.env.MEDGRAPH_API_URL || 'http://localhost:8080',
  apiKey: process.env.MEDGRAPH_API_KEY,
  timeout: parseInt(process.env.MEDGRAPH_TIMEOUT || '30000')
};

// app.ts
import { MedicalGraphClient } from '@medgraph/client';
import { config } from './config';

export const client = new MedicalGraphClient(config);
```
