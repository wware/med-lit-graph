# HIV Controversy Knowledge Graph Pipeline - Package Contents

**Version**: 0.1.0  
**Date**: 2024-12-17  
**Status**: Stage 1 (Entity Extraction) Working, Stages 2-6 Designed

---

## Package Contents

### 🚀 Quick Start Files

1. **QUICKSTART.md** (6.7 KB)
   - Installation instructions
   - Running the pipeline
   - Troubleshooting common issues
   - Health check script

### 📖 Documentation

2. **README.md** (12 KB)
   - Project overview
   - Architecture design
   - Pipeline stages (1-6)
   - Technology stack
   - Design decisions & rationale
   - Development commands

3. **SCHEMA.md** (12 KB)
   - Database schemas for all stages
   - SQLite and PostgreSQL table definitions
   - Example data
   - Query examples (SQL and Cypher)
   - Migration strategy

4. **JSON_FORMAT.md** (13 KB)
   - Complete JSON output schema
   - Field descriptions
   - Usage examples
   - Validation code
   - Benefits of JSON approach

5. **CHANGELOG.md** (8.6 KB)
   - Development progress
   - Completed features (Stage 1)
   - Planned features (Stages 2-6)
   - Design decisions with rationale
   - Known bugs and workarounds
   - Performance metrics

### 🐳 Docker Files

6. **Dockerfile** (1 KB)
   - Python 3.11 slim base
   - CPU-only PyTorch installation
   - Pre-downloads BioBERT model (431 MB)
   - Creates output directory
   - Final image size: ~1.5 GB

7. **docker-compose.yml** (194 bytes)
   - Service definition for pipeline
   - Volume mounts (input XML, output data)
   - Environment variables
   - No model cache volume (baked into image)

8. **requirements.txt** (187 bytes)
   - Python dependencies
   - CPU-only PyTorch index
   - Transformers, pandas, scikit-learn
   - sentence-transformers (for future stages)

### 🐍 Python Code

9. **pmc_ner_pipeline.py** (6.2 KB)
   - Stage 1: Entity extraction implementation
   - BioBERT NER model integration
   - SQLite entity canonicalization
   - Entity-to-alias mappings
   - Co-occurrence edge extraction
   - CSV output for debugging
   - Well-documented with comments

---

## What Works (Stage 1)

✅ Docker containerization  
✅ BioBERT NER entity extraction  
✅ SQLite entity database  
✅ Alias mappings for entity resolution  
✅ Co-occurrence edges  
✅ CSV output (nodes.csv, edges.csv)  
✅ PMC XML parsing (JATS format)  
✅ Stopword and confidence filtering  
✅ CPU-only PyTorch (1.5GB image, not 8.5GB)  
✅ Pre-downloaded model (no runtime download)  

**Current Results**: 9 XML files → 12 entities, 24 edges in ~3 seconds

---

## What's Designed (Stages 2-6)

📋 Stage 2: Provenance extraction (paper metadata, sections, paragraphs)  
📋 Stage 3: Embeddings (entity + paragraph vectors, clustering)  
📋 Stage 4: Claims extraction (semantic relationships with predicates)  
📋 Stage 5: Evidence aggregation (support/refute with metrics)  
📋 Stage 6: PostgreSQL/AGE import (graph database, Cypher queries)  

All schemas, JSON formats, and import strategies documented and ready to implement.

---

## File Organization

```
hiv-controversy-package/
├── QUICKSTART.md          # Start here!
├── README.md              # Full documentation
├── SCHEMA.md              # Database design
├── JSON_FORMAT.md         # Output format spec
├── CHANGELOG.md           # Development history
├── Dockerfile             # Container definition
├── docker-compose.yml     # Orchestration
├── requirements.txt       # Python deps
└── pmc_ner_pipeline.py    # Stage 1 code
```

---

## Installation Summary

```bash
# 1. Copy all files to project directory
cd ~/med-lit-graph/hiv-controversy
# (copy package contents here)

# 2. Add PMC XML files
mkdir -p pmc_xmls
# (copy your PMC*.xml files here)

# 3. Build container
docker-compose build

# 4. Run pipeline
docker-compose run pipeline

# 5. Inspect results
sqlite3 output/entities.db "SELECT * FROM entities;"
head output/nodes.csv
```

**Total setup time**: ~10 minutes (including Docker build)

---

## Key Design Decisions

### 1. Three-Layer Architecture
- **Layer 1**: Extraction (entities + co-occurrence)
- **Layer 2**: Claims (semantic predicates)
- **Layer 3**: Evidence (support/refute)

**Why**: Clean separation enables independent testing and avoids mixing extraction artifacts with semantic knowledge.

### 2. JSON Intermediate Format
- One JSON file per paper
- Self-contained with all extraction results
- Git-trackable, inspectable, portable

**Why**: Separates extraction from storage. Enables version control, debugging, and portability.

### 3. Hybrid SQLite + PostgreSQL
- SQLite for extraction and entity canonicalization (fast, local)
- PostgreSQL+AGE for graph queries (complex, production-ready)

**Why**: Different problems require different tools. Entity resolution needs speed; graph traversal needs power.

### 4. HIV ≠ AIDS (By Design!)
- Entity layer keeps them separate
- Claims layer captures the disputed relationship
- Evidence layer shows support/refute

**Why**: The controversy is about the RELATIONSHIP. Merging them at entity layer loses the ability to represent contradictory claims.

### 5. Embeddings for Entity Resolution
- Stage 3 generates semantic vectors
- Cluster variants: HIV/HTLV-III/LAV → same canonical ID

**Why**: String matching misses semantic equivalence. Embeddings enable intelligent clustering.

---

## Next Steps

### Week 1 (Immediate)
1. Refactor into multi-stage pipeline with argparse
2. Implement Stage 2 (provenance extraction)
3. Add JSON output for Stage 1 results

### Week 2-3 (Short Term)
4. Implement Stage 3 (embeddings)
5. Add entity clustering
6. Implement Stage 4 (claims extraction)

### Month 1 (Medium Term)
7. Implement Stage 5 (evidence aggregation)
8. Set up PostgreSQL + AGE
9. Implement Stage 6 (bulk import)

### Future
10. Build query interface for doctors/researchers
11. Add claim verification UI
12. Expand to other medical controversies

---

## Support & Resources

- **Repository**: https://github.com/wware/med-lit-graph
- **BioBERT Model**: https://huggingface.co/ugaray96/biobert_ncbi_disease_ner
- **PMC JATS Spec**: https://jats.nlm.nih.gov/
- **Apache AGE**: https://age.apache.org/

---

## Known Issues & TODOs

### Current (Stage 1)
- ⚠️ ~30% false positive rate in entity extraction
- ⚠️ No entity clustering yet (HIV ≠ HTLV-III)
- ⚠️ Co-occurrence only, no semantic predicates

### Future Stages
- 📋 Need to implement Stages 2-6
- 📋 Need claim extraction model/rules
- 📋 Need evidence classification logic
- 📋 Need PostgreSQL+AGE setup

---

## Performance

### Current
- **Build time**: 5-10 minutes
- **Image size**: 1.5 GB (down from 8.5 GB!)
- **9 XML files**: ~3 seconds
- **Model load**: Instant (baked into image)

### Expected (Full Pipeline)
- **100 papers**: ~5 minutes
- **1,000 papers**: ~1 hour
- **10,000 papers**: ~10 hours

---

## License

TBD

---

## Contact

Will Ware - wware@alum.mit.edu  
GitHub: @wware

---

**Package assembled**: 2024-12-17  
**Total documentation**: ~53 KB  
**Total code**: ~7.4 KB  
**Ready to deploy**: Yes (Stage 1)  
**Ready to extend**: Yes (Stages 2-6 designed)
