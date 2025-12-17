# Quick Start Guide

## Prerequisites

- Docker & Docker Compose installed
- PMC XML files (JATS format)
- ~2GB disk space for Docker image
- ~500MB for model weights

---

## Installation

### 1. Clone/Create Project Directory

```bash
mkdir -p ~/med-lit-graph/hiv-controversy
cd ~/med-lit-graph/hiv-controversy
```

### 2. Copy Files

Copy these files to your project directory:
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `pmc_ner_pipeline.py`

### 3. Create Input Directory

```bash
mkdir -p pmc_xmls
# Copy your PMC XML files here
```

### 4. Create Output Directory

```bash
mkdir -p output
```

---

## Running the Pipeline

### Build Container (First Time)

```bash
docker-compose build
```

This will:
- Pull Python 3.11 slim image
- Install dependencies (CPU-only PyTorch)
- Download BioBERT NER model (431MB)
- Bake model into image (no runtime download)

**Build time**: ~5-10 minutes
**Image size**: ~1.5GB (down from 8.5GB!)

### Run Entity Extraction

```bash
docker-compose run pipeline
```

Expected output:
```
Device set to use cpu
Processed 9 XML files.
Nodes: 12, Edges: 24
```

### Inspect Results

```bash
# Check SQLite database
sqlite3 output/entities.db "SELECT COUNT(*) FROM entities;"

# Find HIV/AIDS entities
sqlite3 output/entities.db "
  SELECT a.name, a.entity_id, e.canonical_name, a.confidence
  FROM aliases a
  JOIN entities e ON a.entity_id = e.id
  WHERE a.name LIKE '%HIV%' OR a.name LIKE '%AIDS%'
  ORDER BY a.confidence DESC;
"

# View extracted nodes
head -20 output/nodes.csv

# View co-occurrence edges
head -20 output/edges.csv
```

---

## Common Issues

### Issue: "Model downloading at runtime"

**Symptom**: Progress bar shows downloading model.safetensors

**Cause**: Volume mount masking pre-downloaded model

**Fix**: Remove `hf-models` volume from docker-compose.yml

```yaml
# WRONG - has volume mount
volumes:
  - hf-models:/root/.cache/huggingface
  
# RIGHT - no volume mount (model baked in image)
volumes:
  - ./pmc_xmls:/app/pmc_xmls:ro
  - ./output:/app/output
```

Then rebuild:
```bash
docker-compose build --no-cache
docker-compose run pipeline
```

### Issue: "0 nodes, 0 edges"

**Symptom**: Pipeline runs but extracts nothing

**Possible causes**:
1. Entity filter too aggressive
2. Wrong NER model labels
3. Empty/malformed XML files

**Debug**:
```bash
# Check XML files
ls -lh pmc_xmls/

# Check one XML manually
less pmc_xmls/PMC322947.xml

# Test model directly
docker run --rm -it hiv-controversy_pipeline python -c "
from transformers import pipeline
ner = pipeline('ner', model='ugaray96/biobert_ncbi_disease_ner', aggregation_strategy='simple')
results = ner('The patient has AIDS and HIV infection')
for r in results:
    print(r)
"
```

### Issue: "Docker image too large (8GB+)"

**Symptom**: `docker images` shows hiv-controversy_pipeline at 8+ GB

**Cause**: Full CUDA PyTorch installed

**Fix**: Use CPU-only PyTorch in requirements.txt

```txt
# Add this line at top
--extra-index-url https://download.pytorch.org/whl/cpu
torch>=2.1.0
```

Then rebuild:
```bash
docker-compose build --no-cache
```

### Issue: "Permission denied on output files"

**Symptom**: Can't read/delete output files

**Cause**: Docker running as root creates root-owned files

**Fix**:
```bash
sudo chown -R $USER:$USER output/
```

Or add to Dockerfile:
```dockerfile
RUN useradd -m -u $(id -u) appuser
USER appuser
```

---

## Verifying the Setup

### Health Check Script

```bash
#!/bin/bash
# check_setup.sh

echo "Checking Docker..."
docker --version || { echo "Docker not found!"; exit 1; }

echo "Checking Docker Compose..."
docker-compose --version || { echo "Docker Compose not found!"; exit 1; }

echo "Checking input files..."
count=$(ls pmc_xmls/PMC*.xml 2>/dev/null | wc -l)
if [ $count -eq 0 ]; then
    echo "No PMC XML files found in pmc_xmls/"
    exit 1
fi
echo "Found $count XML files"

echo "Checking Docker image..."
if docker images | grep -q hiv-controversy_pipeline; then
    echo "Docker image built ✓"
else
    echo "Docker image not built. Run: docker-compose build"
    exit 1
fi

echo "All checks passed! ✓"
```

Run it:
```bash
chmod +x check_setup.sh
./check_setup.sh
```

---

## Development Workflow

### Make Code Changes

1. Edit `pmc_ner_pipeline.py`
2. Rebuild container: `docker-compose build`
3. Run: `docker-compose run pipeline`
4. Inspect results in `output/`

### Debug Inside Container

```bash
# Shell into container
docker-compose run --rm pipeline /bin/bash

# Inside container
python
>>> from transformers import pipeline
>>> ner = pipeline('ner', model='ugaray96/biobert_ncbi_disease_ner')
>>> # Test stuff
```

### View Logs

```bash
# Run with verbose output
docker-compose run pipeline 2>&1 | tee pipeline.log

# Or detach and check logs
docker-compose up -d
docker-compose logs -f pipeline
```

### Clean Everything

```bash
# Remove output files
rm -rf output/*

# Remove Docker containers
docker-compose down

# Remove Docker images (careful!)
docker rmi hiv-controversy_pipeline

# Rebuild from scratch
docker-compose build --no-cache
```

---

## Next Steps

Once Stage 1 (entity extraction) is working:

1. **Add provenance extraction** - Parse paper metadata
2. **Generate embeddings** - Enable semantic search
3. **Extract claims** - Find relationships between entities
4. **Aggregate evidence** - Link supporting/refuting evidence
5. **Import to graph DB** - PostgreSQL + Apache AGE

See `README.md` for full pipeline architecture.

---

## Sample PMC XML Files

If you need test data, download from PubMed Central:

```bash
# Example papers about HIV/AIDS controversy
wget https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC322947 -O pmc_xmls/PMC322947.xml
wget https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC2545367 -O pmc_xmls/PMC2545367.xml
```

Or use the PMC FTP:
```bash
# Browse PMC Open Access subset
# ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/
```

---

## Performance

### Current (Stage 1)

- **9 XML files**: ~3 seconds (after model load)
- **First run**: 68 seconds (model download) - FIXED by baking into image
- **Subsequent runs**: Instant (no download)

### Expected (Full Pipeline)

- **100 papers**: ~5 minutes
- **1000 papers**: ~1 hour
- **10000 papers**: ~10 hours

Parallelization and caching will improve this significantly.

---

## Resources

- **BioBERT NER Model**: https://huggingface.co/ugaray96/biobert_ncbi_disease_ner
- **PMC JATS XML Spec**: https://jats.nlm.nih.gov/
- **Docker Docs**: https://docs.docker.com/
- **Apache AGE**: https://age.apache.org/

---

## Support

Issues? Questions?

1. Check the troubleshooting section above
2. Review `README.md` for architecture details
3. Inspect `SCHEMA.md` for database design
4. Look at `JSON_FORMAT.md` for output format

File issues at: https://github.com/wware/med-lit-graph
