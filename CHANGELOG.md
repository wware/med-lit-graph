# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- GPU-accelerated ingestion support via remote Ollama servers
- Lambda Labs and AWS EC2 setup guides in `cloud/` directory
- Flexible LLM output parsing to handle multiple relationship formats
- Exact name matching for entity deduplication before similarity search
- Defensive parsing for malformed LLM relationships
- `OLLAMA_HOST` environment variable support in docker-compose
- Comprehensive test suite for entity matching and relationship parsing

### Changed
- Entity similarity threshold lowered to 0.01 for stricter matching
- Entity deduplication now uses exact name matching first, then similarity
- Relationship parsing now handles both `subject/predicate/object` and `entity1/relationship/entity2` formats
- Updated documentation with current status and GPU setup instructions

### Fixed
- Entity matching false positives (different diseases matching same ID)
- LLM relationship crashes due to missing required fields
- Schema non-compliance where LLM uses alternative field names
- Predicate normalization (spaces replaced with underscores)

## [0.1.0] - 2025-12-31

### Added
- Initial ingestion pipeline with Ollama LLM extraction
- PostgreSQL storage with pgvector integration
- Entity deduplication using ChromaDB
- Provenance tracking for all extracted relationships
- Docker Compose setup for local development
- Medical entity extraction prompts (v1, v2, v3)

### Status
- Successfully ingested 25+ papers
- Entity extraction and deduplication working
- Relationship extraction with full evidence trails
- Vector embeddings for semantic search
