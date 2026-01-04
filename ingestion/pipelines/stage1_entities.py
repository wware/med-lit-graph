"""
Stage 1: Entity Extraction

Extracts medical entities from papers using Ollama LLM.
Outputs entities.jsonl with full provenance tracking.

Usage:
    python -m ingestion.pipelines.stage1_entities \
        --query "metformin diabetes" \
        --limit 10 \
        --model llama3.1:70b \
        --output outputs/entities.jsonl
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_ollama import OllamaLLM

from ingestion.utils import (
    JSONLWriter,
    ModelInfo,
    PipelineInfo,
    PromptInfo,
    create_provenance,
)

try:
    from ingestion.medical_prompts import PROMPT_VERSIONS
except ImportError:
    # Fallback if medical_prompts not available
    PROMPT_VERSIONS = {
        "v1": {
            "entity_extraction": """Extract all medical entities from this text.

For each entity, identify:
- name: The entity name
- type: One of: disease, drug, gene, protein, symptom, biomarker, pathway, mutation, procedure
- synonyms: Alternative names (if mentioned)

Text: {text}

Return JSON array of entities:
[{{"name": "...", "type": "...", "synonyms": [...]}}]
"""
        }
    }


def extract_entities_from_text(text: str, llm: OllamaLLM, prompt_template: str, paper_id: str) -> List[Dict[str, Any]]:
    """
    Extract entities from text using LLM.

    Args:
        text: Text to extract from
        llm: Ollama LLM instance
        prompt_template: Prompt template
        paper_id: Source paper ID

    Returns:
        List of entity dictionaries
    """
    prompt = prompt_template.format(text=text)

    try:
        response = llm.invoke(prompt)

        # Try to parse JSON response
        # Handle both direct JSON and markdown code blocks
        response = response.strip()

        # If response contains markdown code blocks, extract the JSON
        if "```" in response:
            # Find the code block
            lines = response.split("\n")
            start_idx = None
            end_idx = None

            # Find start of code block
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    start_idx = i + 1
                    break

            # Find end of code block
            if start_idx is not None:
                for i in range(start_idx, len(lines)):
                    if lines[i].strip() == "```":
                        end_idx = i
                        break

            if start_idx is not None and end_idx is not None:
                response = "\n".join(lines[start_idx:end_idx])

        entities = json.loads(response)

        if not isinstance(entities, list):
            entities = [entities]

        # Add paper_id to each entity
        for entity in entities:
            entity["source_paper"] = paper_id
            entity["source_section"] = "full_text"  # Could be more specific

        return entities

    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse LLM response for {paper_id}: {e}")
        print(f"Response: {response[:200]}...")
        return []
    except Exception as e:
        print(f"⚠️  Error extracting entities from {paper_id}: {e}")
        return []


def fetch_papers(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch papers from PubMed.

    For now, returns mock data. In production, would use actual PubMed API.
    """
    # TODO: Implement actual PubMed fetching
    # For now, return mock data for testing
    return [
        {
            "paper_id": "PMC_TEST_001",
            "title": "Metformin in Type 2 Diabetes Treatment",
            "abstract": "Metformin is a first-line treatment for type 2 diabetes mellitus. It improves insulin sensitivity and reduces hepatic glucose production.",
        }
    ]


def main():
    parser = argparse.ArgumentParser(description="Stage 1: Entity Extraction")
    parser.add_argument("--query", required=True, help="PubMed search query")
    parser.add_argument("--limit", type=int, default=10, help="Number of papers to process")
    parser.add_argument("--model", default="llama3.1:70b", help="Ollama model name")
    parser.add_argument("--output", default="ingestion/outputs/entities.jsonl", help="Output JSONL file")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama host URL")
    parser.add_argument("--prompt-version", default="v1", help="Prompt version to use")

    args = parser.parse_args()

    print("Stage 1: Entity Extraction")
    print(f"  Query: {args.query}")
    print(f"  Limit: {args.limit}")
    print(f"  Model: {args.model}")
    print(f"  Output: {args.output}")
    print()

    # Initialize LLM
    llm = OllamaLLM(
        model=args.model,
        base_url=args.ollama_host,
        temperature=0.1,
    )

    # Get prompt template
    prompt_template = PROMPT_VERSIONS[args.prompt_version]["entity_extraction"]

    # Create provenance
    start_time = datetime.now()
    provenance = create_provenance(
        pipeline_info=PipelineInfo(name="modular_llm_pipeline", version="2.0.0", stage="stage1_entities"),
        model_info=ModelInfo(name=args.model, provider="ollama", temperature=0.1),
        prompt_info=PromptInfo(version=args.prompt_version, template="entity_extraction", checksum=None),
        start_time=start_time,
    )

    # Fetch papers
    print("Fetching papers...")
    papers = fetch_papers(args.query, args.limit)
    print(f"✓ Found {len(papers)} papers")
    print()

    # Extract entities
    output_path = Path(args.output)
    all_entities = []

    with JSONLWriter(output_path) as writer:
        for i, paper in enumerate(papers, 1):
            print(f"[{i}/{len(papers)}] Processing {paper['paper_id']}...")

            # Extract from title + abstract
            text = f"{paper['title']}. {paper['abstract']}"
            entities = extract_entities_from_text(text=text, llm=llm, prompt_template=prompt_template, paper_id=paper["paper_id"])

            # Add provenance to each entity
            for entity in entities:
                entity["entity_id"] = f"temp_{len(all_entities) + 1:06d}"
                entity["provenance"] = provenance
                writer.write(entity)
                all_entities.append(entity)

            print(f"  ✓ Extracted {len(entities)} entities")

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print()
    print("=" * 70)
    print("✅ Stage 1 Complete!")
    print(f"  Papers processed: {len(papers)}")
    print(f"  Entities extracted: {len(all_entities)}")
    print(f"  Output: {output_path}")
    print(f"  Duration: {duration:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
