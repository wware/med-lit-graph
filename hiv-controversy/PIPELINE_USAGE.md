# Pipeline Usage Guide

## Overview

The HIV controversy pipeline consists of 5 stages that can be run individually or in sequence:

1. **Entity Extraction** - Extract biomedical entities using BioBERT NER
2. **Provenance Extraction** - Extract paper metadata and document structure
3. **Claims Extraction** - Extract claims from paragraphs
4. **Embeddings Generation** - Generate embeddings for semantic search
5. **Evidence Synthesis** - Synthesize evidence from claims

## Running with Docker Compose (Recommended)

### Run a single stage
```bash
docker-compose run pipeline 1
```

### Run multiple specific stages
```bash
docker-compose run pipeline 1 2 3
```

### Run a range of stages
```bash
docker-compose run pipeline 1-5
```

### Run mixed ranges and individual stages
```bash
docker-compose run pipeline 1 3-5
```

### Specify custom directories
```bash
docker-compose run pipeline --xml-dir /custom/path --output-dir /custom/output 1-5
```

## Running Locally (Without Docker)

You can also run the pipeline script directly on your host machine:

```bash
./run_pipeline.sh 1-5
```

Options:
- `--xml-dir DIR` - Directory containing PMC XML files (default: pmc_xmls)
- `--output-dir DIR` - Output directory (default: output)
- `--help` - Show help message

## Examples

### Process all stages
```bash
docker-compose run pipeline 1-5
```

### Run only provenance and claims extraction
```bash
docker-compose run pipeline 2 3
```

### Skip entity extraction, run everything else
```bash
docker-compose run pipeline 2-5
```

## Output Files

Each stage produces specific outputs in the `output/` directory:

- **Stage 1**: `entities.db`, `extraction_edges.jsonl`, `nodes.csv`, `edges.csv`
- **Stage 2**: `provenance.db`
- **Stage 3**: `claims.db`
- **Stage 4**: `embeddings.db`
- **Stage 5**: `evidence.db`

## Error Handling

If a stage fails:
- **Interactive mode**: You'll be prompted whether to continue with remaining stages
- **Non-interactive mode** (Docker): The pipeline will halt on the first error

## Tips

1. Always run stages in order (1, 2, 3, etc.) as later stages may depend on earlier ones
2. Check the output directory for results after each stage
3. Use `docker-compose logs` to view detailed logs
4. The AGE database service will start automatically when running the pipeline
