#!/bin/bash
#
# Multi-Stage Pipeline Runner
#
# This script orchestrates the execution of multiple pipeline stages.
# It can run individual stages or ranges of stages.
#
# Stages:
#   1. Entity Extraction (pmc_ner_pipeline.py)
#   2. Provenance Extraction (pmc_provenance_pipeline.py)
#   3. Claims Extraction (pmc_claims_pipeline.py)
#   4. Embeddings Generation (pmc_embeddings_pipeline.py)
#   5. Evidence Synthesis (pmc_evidence_pipeline.py)
#
# Usage:
#     ./run_pipeline.sh 1              # Run only stage 1
#     ./run_pipeline.sh 1 2 3          # Run stages 1, 2, and 3
#     ./run_pipeline.sh 1-5            # Run stages 1 through 5
#     ./run_pipeline.sh 2-4 5          # Run stages 2-4 and 5
#
# Docker usage:
#     docker-compose run pipeline 1-5  # Run all stages in Docker
#
# Options:
#     --xml-dir DIR       Directory containing PMC XML files (default: pmc_xmls)
#     --output-dir DIR    Output directory (default: output)
#

set -e  # Exit on error

# Stage definitions
declare -A STAGE_NAMES
declare -A STAGE_SCRIPTS
declare -A STAGE_DESCRIPTIONS

STAGE_NAMES[1]="Entity Extraction"
STAGE_SCRIPTS[1]="pmc_ner_pipeline.py"
STAGE_DESCRIPTIONS[1]="Extract biomedical entities using BioBERT NER"

STAGE_NAMES[2]="Provenance Extraction"
STAGE_SCRIPTS[2]="pmc_provenance_pipeline.py"
STAGE_DESCRIPTIONS[2]="Extract paper metadata and document structure"

STAGE_NAMES[3]="Claims Extraction"
STAGE_SCRIPTS[3]="pmc_claims_pipeline.py"
STAGE_DESCRIPTIONS[3]="Extract claims from paragraphs"

STAGE_NAMES[4]="Embeddings Generation"
STAGE_SCRIPTS[4]="pmc_embeddings_pipeline.py"
STAGE_DESCRIPTIONS[4]="Generate embeddings for semantic search"

STAGE_NAMES[5]="Evidence Synthesis"
STAGE_SCRIPTS[5]="pmc_evidence_pipeline.py"
STAGE_DESCRIPTIONS[5]="Synthesize evidence from claims"

STAGE_NAMES[6]="Graph Database Loading"
STAGE_SCRIPTS[6]="pmc_graph_pipeline.py"
STAGE_DESCRIPTIONS[6]="Load data into PostgreSQL/AGE graph database"

# Default values
XML_DIR="pmc_xmls"
OUTPUT_DIR="output"
STAGES_TO_RUN=()

# Parse command line arguments
show_help() {
    cat << EOF
Multi-Stage Pipeline Runner

Usage: $0 [OPTIONS] STAGES...

Stages:
  1. Entity Extraction
  2. Provenance Extraction
  3. Claims Extraction
  4. Embeddings Generation
  5. Evidence Synthesis
  6. Graph Database Loading

Arguments:
  STAGES    Stage numbers to run (e.g., '1', '1-3', '1 2 3')

Options:
  --xml-dir DIR       Directory containing PMC XML files (default: pmc_xmls)
  --output-dir DIR    Output directory (default: output)
  --help              Show this help message

Examples:
  $0 1                Run only stage 1
  $0 1 2 3            Run stages 1, 2, and 3
  $0 1-5              Run stages 1 through 5
  $0 2-4 5            Run stages 2-4 and 5

Docker usage:
  docker-compose run pipeline 1-5
EOF
}

# Parse stage specification (handles ranges like "1-5")
parse_stages() {
    local spec="$1"

    if [[ "$spec" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        # Range specification (e.g., "1-5")
        local start="${BASH_REMATCH[1]}"
        local end="${BASH_REMATCH[2]}"

        if [ "$start" -gt "$end" ]; then
            echo "Error: Invalid range $spec (start > end)" >&2
            exit 1
        fi

        for ((i=start; i<=end; i++)); do
            if [ -z "${STAGE_SCRIPTS[$i]}" ]; then
                echo "Error: Invalid stage number: $i" >&2
                exit 1
            fi
            STAGES_TO_RUN+=("$i")
        done
    elif [[ "$spec" =~ ^[0-9]+$ ]]; then
        # Single stage number
        if [ -z "${STAGE_SCRIPTS[$spec]}" ]; then
            echo "Error: Invalid stage number: $spec" >&2
            exit 1
        fi
        STAGES_TO_RUN+=("$spec")
    else
        echo "Error: Invalid stage specification: $spec" >&2
        echo "Use a number (e.g., '1') or range (e.g., '1-5')" >&2
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --xml-dir)
            XML_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -*)
            echo "Error: Unknown option: $1" >&2
            show_help
            exit 1
            ;;
        *)
            parse_stages "$1"
            shift
            ;;
    esac
done

# Check if any stages were specified
if [ ${#STAGES_TO_RUN[@]} -eq 0 ]; then
    echo "Error: No stages specified" >&2
    show_help
    exit 1
fi

# Sort stages and remove duplicates
IFS=$'\n' STAGES_TO_RUN=($(sort -nu <<<"${STAGES_TO_RUN[*]}"))
unset IFS

# Validate directories
if [ ! -d "$XML_DIR" ]; then
    echo "Error: XML directory not found: $XML_DIR" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Print execution plan
echo "================================================================================"
echo "PIPELINE EXECUTION PLAN"
echo "================================================================================"
echo "XML Directory: $XML_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo "Stages to run: ${STAGES_TO_RUN[*]}"
echo ""

for stage in "${STAGES_TO_RUN[@]}"; do
    echo "  $stage. ${STAGE_NAMES[$stage]}: ${STAGE_DESCRIPTIONS[$stage]}"
done

echo "================================================================================"
echo ""

# Run stages
FAILED_STAGES=()
SUCCESSFUL_STAGES=()

for stage in "${STAGES_TO_RUN[@]}"; do
    echo "================================================================================"
    echo "Stage $stage: ${STAGE_NAMES[$stage]}"
    echo "Description: ${STAGE_DESCRIPTIONS[$stage]}"
    echo "Script: ${STAGE_SCRIPTS[$stage]}"
    echo "================================================================================"
    echo ""

    # Run the stage (use python3 if python is not available)
    PYTHON_CMD="python"
    if ! command -v python &> /dev/null; then
        PYTHON_CMD="python3"
    fi

    # Stages 1 and 2 need --xml-dir, stages 3-6 only need --output-dir
    if [ "$stage" -le 2 ]; then
        CMD=("$PYTHON_CMD" "${STAGE_SCRIPTS[$stage]}" --xml-dir "$XML_DIR" --output-dir "$OUTPUT_DIR")
    else
        CMD=("$PYTHON_CMD" "${STAGE_SCRIPTS[$stage]}" --output-dir "$OUTPUT_DIR")
    fi

    if "${CMD[@]}"; then
        echo ""
        echo "Stage $stage completed successfully"
        SUCCESSFUL_STAGES+=("$stage")
    else
        EXIT_CODE=$?
        echo ""
        echo "Error: Stage $stage failed with exit code $EXIT_CODE" >&2
        FAILED_STAGES+=("$stage")

        # Ask whether to continue (only if running interactively)
        if [ -t 0 ]; then
            read -p "Continue with remaining stages? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Pipeline execution halted."
                break
            fi
        else
            # Non-interactive mode: stop on first error
            echo "Pipeline execution halted."
            break
        fi
    fi

    echo ""
done

# Print summary
echo "================================================================================"
echo "PIPELINE EXECUTION SUMMARY"
echo "================================================================================"
echo "Total stages attempted: ${#STAGES_TO_RUN[@]}"
echo "Successful stages: ${#SUCCESSFUL_STAGES[@]}"
echo "Failed stages: ${#FAILED_STAGES[@]}"

if [ ${#FAILED_STAGES[@]} -gt 0 ]; then
    echo "Failed stage numbers: ${FAILED_STAGES[*]}"
    exit 1
else
    echo "All stages completed successfully!"
    exit 0
fi
