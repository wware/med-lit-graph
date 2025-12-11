/**
 * Medical Knowledge Graph Query Client (TypeScript)
 *
 * TypeScript/JavaScript client library for querying the medical knowledge graph
 * using the JSON-based graph query language.
 *
 * @example
 * ```typescript
 * import { MedicalGraphClient, QueryBuilder } from './medical-graph-client';
 *
 * // Client will use MEDGRAPH_SERVER environment variable for the base URL
 * const client = new MedicalGraphClient();
 *
 * // Simple query
 * const results = await client.findTreatments('breast cancer');
 *
 * // Complex query using builder
 * const query = new QueryBuilder()
 *   .findNodes(EntityType.DRUG)
 *   .withEdge(RelationType.TREATS, { minConfidence: 0.7 })
 *   .filterTarget(EntityType.DISEASE, { name: 'diabetes' })
 *   .limit(10)
 *   .build();
 *
 * const results = await client.execute(query);
 * ```
 */

// ============================================================================
// Types and Enums
// ============================================================================

export enum EntityType {
  DISEASE = 'disease',
  SYMPTOM = 'symptom',
  DRUG = 'drug',
  GENE = 'gene',
  PROTEIN = 'protein',
  ANATOMICAL_STRUCTURE = 'anatomical_structure',
  PROCEDURE = 'procedure',
  TEST = 'test',
  BIOMARKER = 'biomarker',
  PAPER = 'paper',
  AUTHOR = 'author',
  INSTITUTION = 'institution',
  CLINICAL_TRIAL = 'clinical_trial',
  MEASUREMENT = 'measurement'
}

export enum RelationType {
  // Causal
  CAUSES = 'causes',
  PREVENTS = 'prevents',
  INCREASES_RISK = 'increases_risk',
  DECREASES_RISK = 'decreases_risk',

  // Treatment
  TREATS = 'treats',
  MANAGES = 'manages',
  CONTRAINDICATES = 'contraindicates',

  // Biological
  BINDS_TO = 'binds_to',
  INHIBITS = 'inhibits',
  ACTIVATES = 'activates',
  UPREGULATES = 'upregulates',
  DOWNREGULATES = 'downregulates',
  ENCODES = 'encodes',
  METABOLIZES = 'metabolizes',

  // Clinical
  DIAGNOSES = 'diagnoses',
  INDICATES = 'indicates',
  PRECEDES = 'precedes',
  CO_OCCURS_WITH = 'co_occurs_with',
  ASSOCIATED_WITH = 'associated_with',

  // Location
  LOCATED_IN = 'located_in',
  AFFECTS = 'affects',

  // Provenance
  AUTHORED_BY = 'authored_by',
  CITES = 'cites',
  CONTRADICTS = 'contradicts',
  SUPPORTS = 'supports'
}

export type FilterOperator =
  | 'eq'
  | 'ne'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'in'
  | 'contains'
  | 'regex';

export type Direction = 'outgoing' | 'incoming' | 'both';

export type SortDirection = 'asc' | 'desc';

export type AggregationFunction = 'count' | 'sum' | 'avg' | 'min' | 'max';

export type FindType = 'nodes' | 'edges' | 'paths' | 'subgraph';

// ============================================================================
// Query Interfaces
// ============================================================================

export interface PropertyFilter {
  field: string;
  operator: FilterOperator;
  value: any;
}

export interface NodePattern {
  node_type?: EntityType;
  node_types?: EntityType[];
  id?: string;
  name?: string;
  name_pattern?: string;
  properties?: Record<string, any>;
  property_filters?: PropertyFilter[];
  external_id?: Record<string, string>;
  var?: string;
}

export interface EdgePattern {
  relation_type?: RelationType;
  relation_types?: RelationType[];
  direction?: Direction;
  min_confidence?: number;
  property_filters?: PropertyFilter[];
  require_evidence_from?: string[];
  min_evidence_count?: number;
  var?: string;
}

export interface PathStep {
  edge: EdgePattern;
  node: NodePattern;
}

export interface PathPattern {
  start: NodePattern;
  edges: PathStep[];
  max_hops?: number;
  avoid_cycles?: boolean;
  shortest_path?: boolean;
  all_paths?: boolean;
}

export interface AggregationSpec {
  group_by?: string[];
  aggregations: Record<string, [AggregationFunction, string]>;
}

export interface GraphQuery {
  find?: FindType;
  node_pattern?: NodePattern;
  edge_pattern?: EdgePattern;
  path_pattern?: PathPattern;
  filters?: PropertyFilter[];
  aggregate?: AggregationSpec;
  order_by?: [string, SortDirection][];
  limit?: number;
  offset?: number;
  return_fields?: string[];
}

// ============================================================================
// Response Types
// ============================================================================

export interface QueryResult<T = any> {
  results: T[];
  metadata: {
    total_results: number;
    query_time_ms: number;
    has_more?: boolean;
  };
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

// ============================================================================
// Query Builder
// ============================================================================

export class QueryBuilder {
  private query: GraphQuery = {};
  private filterList: PropertyFilter[] = [];

  /**
   * Find nodes of a specific type
   */
  findNodes(
    nodeType: EntityType,
    options: {
      name?: string;
      namePattern?: string;
      var?: string;
    } = {}
  ): this {
    this.query.find = 'nodes';
    this.query.node_pattern = {
      node_type: nodeType,
      name: options.name,
      name_pattern: options.namePattern,
      var: options.var || 'n'
    };
    return this;
  }

  /**
   * Find edges/relationships
   */
  findEdges(
    relationType?: RelationType,
    options: { var?: string } = {}
  ): this {
    this.query.find = 'edges';
    this.query.edge_pattern = {
      relation_type: relationType,
      var: options.var || 'r'
    };
    return this;
  }

  /**
   * Find paths through the graph
   */
  findPaths(startPattern: NodePattern): this {
    this.query.find = 'paths';
    this.query.path_pattern = {
      start: startPattern,
      edges: []
    };
    return this;
  }

  /**
   * Add edge pattern to node query
   */
  withEdge(
    relationType: RelationType | RelationType[],
    options: {
      direction?: Direction;
      minConfidence?: number;
      var?: string;
    } = {}
  ): this {
    const edge: EdgePattern = {
      direction: options.direction || 'outgoing',
      min_confidence: options.minConfidence,
      var: options.var || 'r'
    };

    if (Array.isArray(relationType)) {
      edge.relation_types = relationType;
    } else {
      edge.relation_type = relationType;
    }

    this.query.edge_pattern = edge;
    return this;
  }

  /**
   * Add a path step (for multi-hop queries)
   */
  addPathStep(edge: EdgePattern, node: NodePattern): this {
    if (!this.query.path_pattern) {
      throw new Error('Must call findPaths() before adding path steps');
    }
    this.query.path_pattern.edges.push({ edge, node });
    return this;
  }

  /**
   * Set path constraints
   */
  pathConstraints(options: {
    maxHops?: number;
    avoidCycles?: boolean;
    shortestPath?: boolean;
  }): this {
    if (!this.query.path_pattern) {
      throw new Error('Must call findPaths() before setting path constraints');
    }
    Object.assign(this.query.path_pattern, options);
    return this;
  }

  /**
   * Filter on target node (when using withEdge)
   */
  filterTarget(
    nodeType: EntityType,
    options: {
      name?: string;
      namePattern?: string;
    } = {}
  ): this {
    this.filterList.push({
      field: 'target.node_type',
      operator: 'eq',
      value: nodeType
    });

    if (options.name) {
      this.filterList.push({
        field: 'target.name',
        operator: 'eq',
        value: options.name
      });
    }

    if (options.namePattern) {
      this.filterList.push({
        field: 'target.name_pattern',
        operator: 'regex',
        value: options.namePattern
      });
    }

    return this;
  }

  /**
   * Add custom filter
   */
  filter(field: string, operator: FilterOperator, value: any): this {
    this.filterList.push({ field, operator, value });
    return this;
  }

  /**
   * Add aggregation
   */
  aggregate(
    groupBy: string[],
    aggregations: Record<string, [AggregationFunction, string]>
  ): this {
    this.query.aggregate = {
      group_by: groupBy,
      aggregations
    };
    return this;
  }

  /**
   * Add ordering
   */
  orderBy(field: string, direction: SortDirection = 'desc'): this {
    if (!this.query.order_by) {
      this.query.order_by = [];
    }
    this.query.order_by.push([field, direction]);
    return this;
  }

  /**
   * Limit results
   */
  limit(n: number): this {
    this.query.limit = n;
    return this;
  }

  /**
   * Offset results (pagination)
   */
  offset(n: number): this {
    this.query.offset = n;
    return this;
  }

  /**
   * Specify which fields to return
   */
  returnFields(...fields: string[]): this {
    this.query.return_fields = fields;
    return this;
  }

  /**
   * Build the final query
   */
  build(): GraphQuery {
    if (this.filterList.length > 0) {
      this.query.filters = this.filterList;
    }
    return this.query;
  }
}

// ============================================================================
// Client Configuration
// ============================================================================

export interface ClientConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

// ============================================================================
// Medical Graph Client
// ============================================================================

export class MedicalGraphClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private headers: Record<string, string>;

  constructor(config?: ClientConfig | string) {
    const baseUrl = typeof config === 'string'
        ? config
        : (config?.baseUrl || process.env.MEDGRAPH_SERVER || '');

    if (!baseUrl) {
      throw new Error("MedicalGraphClient: baseUrl is required. Provide it in the constructor or set the MEDGRAPH_SERVER environment variable.");
    }
    this.baseUrl = baseUrl.replace(/\/$/, '');

    if (typeof config === 'string' || !config) {
      this.timeout = 30000;
      this.headers = {};
    } else {
      this.apiKey = config.apiKey;
      this.timeout = config.timeout || 30000;
      this.headers = config.headers || {};
    }

    this.headers['Content-Type'] = 'application/json';
    if (this.apiKey) {
      this.headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
  }

  /**
   * Execute a graph query
   */
  async execute<T = any>(query: GraphQuery): Promise<QueryResult<T>> {
    const response = await fetch(`${this.baseUrl}/api/v1/query`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(query),
      signal: AbortSignal.timeout(this.timeout)
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(`API Error: ${error.error.message}`);
    }

    return response.json();
  }

  /**
   * Execute a raw query (for custom queries)
   */
  async executeRaw<T = any>(queryDict: Record<string, any>): Promise<QueryResult<T>> {
    const response = await fetch(`${this.baseUrl}/api/v1/query`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(queryDict),
      signal: AbortSignal.timeout(this.timeout)
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(`API Error: ${error.error.message}`);
    }

    return response.json();
  }

  // ========================================================================
  // Convenience Methods
  // ========================================================================

  /**
   * Find drugs that treat a specific disease
   */
  async findTreatments(
    disease: string,
    options: {
      minConfidence?: number;
      limit?: number;
    } = {}
  ): Promise<QueryResult> {
    const query = new QueryBuilder()
      .findNodes(EntityType.DRUG)
      .withEdge(RelationType.TREATS, {
        minConfidence: options.minConfidence || 0.6
      })
      .filterTarget(EntityType.DISEASE, { name: disease })
      .aggregate(
        ['drug.name'],
        {
          paper_count: ['count', 'treatment_rel.evidence.paper_id'],
          avg_confidence: ['avg', 'treatment_rel.confidence']
        }
      )
      .orderBy('paper_count', 'desc')
      .limit(options.limit || 20)
      .build();

    return this.execute(query);
  }

  /**
   * Find genes associated with a disease
   */
  async findDiseaseGenes(
    disease: string,
    options: {
      minConfidence?: number;
      limit?: number;
    } = {}
  ): Promise<QueryResult> {
    const query = new QueryBuilder()
      .findNodes(EntityType.GENE)
      .withEdge(
        [RelationType.ASSOCIATED_WITH, RelationType.CAUSES, RelationType.INCREASES_RISK],
        {
          direction: 'incoming',
          minConfidence: options.minConfidence || 0.5
        }
      )
      .filterTarget(EntityType.DISEASE, { namePattern: `.*${disease}.*` })
      .returnFields(
        'gene.name',
        'gene.external_ids.hgnc',
        'rel.confidence',
        'rel.evidence.paper_id'
      )
      .orderBy('rel.confidence', 'desc')
      .limit(options.limit || 50)
      .build();

    return this.execute(query);
  }

  /**
   * Find diagnostic tests for a disease
   */
  async findDiagnosticTests(
    disease: string,
    options: {
      minConfidence?: number;
    } = {}
  ): Promise<QueryResult> {
    const query: GraphQuery = {
      find: 'nodes',
      node_pattern: {
        node_types: [EntityType.TEST, EntityType.BIOMARKER],
        var: 'diagnostic'
      },
      edge_pattern: {
        relation_types: [RelationType.DIAGNOSES, RelationType.INDICATES],
        direction: 'outgoing',
        min_confidence: options.minConfidence || 0.6
      },
      filters: [
        { field: 'target.name', operator: 'eq', value: disease }
      ],
      aggregate: {
        group_by: ['diagnostic.name', 'diagnostic.node_type'],
        aggregations: {
          paper_count: ['count', 'rel.evidence.paper_id'],
          avg_confidence: ['avg', 'rel.confidence']
        }
      },
      order_by: [['avg_confidence', 'desc']]
    };

    return this.execute(query);
  }

  /**
   * Find mechanism of action for a drug
   */
  async findDrugMechanisms(drugName: string): Promise<QueryResult> {
    const query = {
      find: 'paths',
      path_pattern: {
        start: {
          node_type: EntityType.DRUG,
          name: drugName,
          var: 'drug'
        },
        edges: [
          {
            edge: {
              relation_types: [
                RelationType.BINDS_TO,
                RelationType.INHIBITS,
                RelationType.ACTIVATES
              ],
              var: 'interaction'
            },
            node: {
              node_types: [EntityType.PROTEIN, EntityType.GENE],
              var: 'target'
            }
          }
        ],
        max_hops: 1
      },
      return_fields: [
        'drug.name',
        'target.name',
        'target.node_type',
        'interaction.relation_type',
        'interaction.confidence'
      ]
    };

    return this.executeRaw(query);
  }

  /**
   * Compare evidence quality for different treatments
   */
  async compareTreatmentEvidence(
    disease: string,
    drugs: string[]
  ): Promise<QueryResult> {
    const query: GraphQuery = {
      find: 'edges',
      edge_pattern: {
        relation_type: RelationType.TREATS,
        min_confidence: 0.5
      },
      filters: [
        { field: 'source.name', operator: 'in', value: drugs },
        { field: 'target.name', operator: 'eq', value: disease }
      ],
      aggregate: {
        group_by: ['source.name'],
        aggregations: {
          total_papers: ['count', 'rel.evidence.paper_id'],
          rct_count: ['count', "rel.evidence[study_type='rct'].paper_id"],
          avg_confidence: ['avg', 'rel.confidence']
        }
      },
      order_by: [['rct_count', 'desc']]
    };

    return this.execute(query);
  }

  /**
   * Search for diseases by symptoms (differential diagnosis)
   */
  async searchBySymptoms(
    symptoms: string[],
    options: {
      minSymptomMatches?: number;
    } = {}
  ): Promise<QueryResult> {
    const query = {
      find: 'nodes',
      node_pattern: {
        node_type: EntityType.DISEASE,
        var: 'disease'
      },
      filters: [
        {
          field: "incoming_edges[relation_type='symptom_of'].source.name",
          operator: 'in',
          value: symptoms
        }
      ],
      aggregate: {
        group_by: ['disease.name'],
        aggregations: {
          symptom_match_count: ['count', "incoming_edges[relation_type='symptom_of']"],
          total_papers: ['count', 'incoming_edges.evidence.paper_id']
        }
      },
      order_by: [
        ['symptom_match_count', 'desc'],
        ['total_papers', 'desc']
      ],
      limit: 10
    };

    return this.executeRaw(query);
  }

  /**
   * Get details about a specific paper
   */
  async getPaperDetails(paperId: string): Promise<QueryResult> {
    const query = new QueryBuilder()
      .findNodes(EntityType.PAPER)
      .filter('id', 'eq', paperId)
      .build();

    return this.execute(query);
  }

  /**
   * Find contradictory evidence
   */
  async findContradictoryEvidence(
    drug: string,
    disease: string
  ): Promise<QueryResult> {
    const query: GraphQuery = {
      find: 'edges',
      edge_pattern: {
        relation_types: [
          RelationType.TREATS,
          RelationType.CONTRAINDICATES,
          RelationType.INCREASES_RISK
        ]
      },
      filters: [
        { field: 'source.name', operator: 'eq', value: drug },
        { field: 'target.name', operator: 'eq', value: disease }
      ],
      aggregate: {
        group_by: ['rel.relation_type'],
        aggregations: {
          paper_count: ['count', 'rel.evidence.paper_id'],
          avg_confidence: ['avg', 'rel.confidence']
        }
      }
    };

    return this.execute(query);
  }

  /**
   * Execute multiple queries in a batch
   */
  async batch(queries: Array<{ id: string; query: GraphQuery }>): Promise<Record<string, QueryResult>> {
    const response = await fetch(`${this.baseUrl}/api/v1/batch`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ queries }),
      signal: AbortSignal.timeout(this.timeout)
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(`API Error: ${error.error.message}`);
    }

    return response.json();
  }
}

// ============================================================================
// Exports
// ============================================================================

export default MedicalGraphClient;

// Also export everything for named imports
export {
  MedicalGraphClient,
  QueryBuilder
};
