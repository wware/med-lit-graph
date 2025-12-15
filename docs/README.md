# Medical Knowledge Graph Documentation

Welcome to the comprehensive documentation for the Medical Knowledge Graph project. This documentation provides detailed information about the architecture, design decisions, implementation, and usage of the system.

## 📚 Documentation Index

### Architecture & Design

**[Design Decisions](DESIGN_DECISIONS.md)**
- Comprehensive rationale for architectural choices
- Trade-offs analysis for key technical decisions
- Provenance requirements, query language design, and storage strategies
- Comparison of different database and search technologies

**[Schema Notes](SCHEMA_NOTES.md)**
- Complete graph schema definition
- Entity types (diseases, drugs, genes, proteins, papers, etc.)
- Relationship types (treats, causes, binds_to, etc.)
- Evidence and measurement structures
- Per-paper JSON schema design

**[Ontology Support](ONTOLOGY_SUPPORT.md)**
- Integration with biomedical ontologies (ECO, OBI, STATO, IAO, SEPIO)
- Scientific methodology support (hypotheses, study designs, statistical methods)
- Evidence quality classification and weighting
- Complete workflow examples

### Query Language

**[Query Language Notes](QUERY_LANGUAGE_NOTES.md)**
- JSON-based graph query language design
- LLM-friendly query structure
- Translation to PostgreSQL SQL (via Recursive CTEs)
- Natural language to structured query parsing
- MCP registry and publishing information

### Implementation & Validation

**[Implementation Summary](IMPLEMENTATION_SUMMARY.md)**
- Summary of core scientific method ontologies implementation
- New entity types and relationships
- Test coverage and code quality metrics
- Usage examples and benefits

**[Curl Examples Validation](CURL_EXAMPLES_VALIDATION.md)**
- Validation report for API examples
- Schema compliance testing
- Coverage of PR #3 features (ontology support)
- Automated testing documentation

### Development

**[TODO](TODO.md)**
- Development roadmap and feature tracking
- Implementation status (Phase 1, 2, 3)
- Query executor progress
- Examples coverage matrix

## 🔗 Client Documentation

The client libraries and examples are maintained alongside the implementation code:

- **[Python Client](../client/python/)** - Python client library with high-level API
- **[TypeScript Client](../client/ts/)** - TypeScript/JavaScript client library
  - [TypeScript Examples](../client/ts/typescript-examples.md) - Comprehensive usage examples
- **[Curl Examples](../client/curl/EXAMPLES.md)** - Complete REST API examples
- **[Query Language Spec](../client/QUERY_LANGUAGE.md)** - Formal query language specification

## 🏗️ Schema Documentation

- **[Schema README](../schema/README.md)** - Schema package documentation
- Entity and relationship type definitions in code

## 🧪 Testing

- **[Tests README](../tests/README.md)** - Test suite documentation
- Comprehensive test coverage for schema, relationships, and query execution

## 📖 Getting Started

1. **New to the project?** Start with the root [README.md](../README.md) for project overview
2. **Understanding the architecture?** Read [Design Decisions](DESIGN_DECISIONS.md)
3. **Working with the schema?** See [Schema Notes](SCHEMA_NOTES.md) and [Ontology Support](ONTOLOGY_SUPPORT.md)
4. **Building queries?** Check [Query Language Notes](QUERY_LANGUAGE_NOTES.md) and [Curl Examples](../client/curl/EXAMPLES.md)
5. **Developing features?** Refer to [TODO](TODO.md) for the roadmap

## 🎯 Key Concepts

### Provenance First
Every medical relationship must include evidence from peer-reviewed literature. See [Design Decisions - Provenance](DESIGN_DECISIONS.md#1-provenance-as-a-first-class-citizen) for rationale.

### Immutable Source of Truth
Per-paper JSON files serve as the immutable source of truth. The graph database is regenerated from these files. See [Design Decisions - Source of Truth](DESIGN_DECISIONS.md#2-immutable-source-of-truth-json-files).

### Vendor-Neutral Query Language
JSON-based query language that translates to any relational or graph database (optimized for PostgreSQL). See [Query Language Notes](QUERY_LANGUAGE_NOTES.md) and [Design Decisions - Query Language](DESIGN_DECISIONS.md#3-json-query-language-vs-native-graph-qls).

### Evidence Quality Weighting
Automatic confidence scoring based on study type (RCT > meta-analysis > case report). See [Design Decisions - Evidence Weighting](DESIGN_DECISIONS.md#4-evidence-quality-weighting).

### Hybrid Graph RAG
Combines vector search (semantic) with graph traversal (relationships) for comprehensive results. See [Design Decisions - Hybrid RAG](DESIGN_DECISIONS.md#5-hybrid-graph-rag-architecture).

## 🔬 Advanced Topics

### Scientific Methodology Support
The system tracks hypotheses, study designs, statistical methods, and evidence chains using established ontologies:
- **ECO** - Evidence type classification
- **OBI** - Study designs
- **STATO** - Statistical methods
- **IAO** - Hypotheses
- **SEPIO** - Evidence provenance

See [Ontology Support](ONTOLOGY_SUPPORT.md) for complete details.

### Multi-Hop Graph Queries
The query language supports complex multi-hop path queries for drug repurposing, mechanism of action analysis, and differential diagnosis. See [Query Language Notes](QUERY_LANGUAGE_NOTES.md) for examples.

## 📝 Contributing

When contributing to documentation:
1. Keep documentation in sync with code changes
2. Update internal links when moving files
3. Add examples for new features
4. Run validation tests (see [Curl Examples Validation](CURL_EXAMPLES_VALIDATION.md))
5. Follow the existing documentation structure and style

## 📞 Support

- **Issues**: https://github.com/wware/med-lit-graph/issues
- **Discussions**: https://github.com/wware/med-lit-graph/discussions
- **Main README**: [../README.md](../README.md)

---

**Last Updated**: December 2025
