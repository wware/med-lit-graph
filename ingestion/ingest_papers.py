#!/usr/bin/env python3
"""
Ollama-based paper ingestion pipeline with entity database integration.

Uses local LLM for extraction and LangChain for entity resolution/deduplication.

Requirements:
    pip install langchain langchain-community ollama chromadb sentence-transformers

Usage:
    # Start Ollama with a good model
    ollama pull llama3.1:70b
    # or: ollama pull qwen2.5:32b
    # or: ollama pull mixtral:8x7b

    # Default: BiomedBERT embeddings
    python ingest_papers_ollama.py --query "metformin diabetes" --limit 50

    # Or use PubMedBERT
    python ingest_papers_ollama.py \
        --query "PARP inhibitors" \
        --embedding-model "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext" \
        --limit 100
"""

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaLLM

try:
    from medical_prompts import PROMPT_VERSIONS
    from provenance import create_paper_output, get_tracker
except ImportError:
    from ingestion.medical_prompts import PROMPT_VERSIONS
    from ingestion.provenance import create_paper_output, get_tracker


def get_git_info() -> Dict[str, str]:
    """Get current git commit and branch info for provenance."""
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, cwd=Path(__file__).parent.parent).decode("ascii").strip()  # Run from repo root

        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL, cwd=Path(__file__).parent.parent).decode("ascii").strip()

        # Check if working directory is clean
        status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, cwd=Path(__file__).parent.parent).decode("ascii").strip()

        is_dirty = len(status) > 0

        return {"commit": commit, "commit_short": commit[:7], "branch": branch, "dirty": is_dirty, "repo_url": "https://github.com/wware/med-lit-graph"}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"commit": "unknown", "commit_short": "unknown", "branch": "unknown", "dirty": False, "repo_url": "unknown"}


def get_extraction_provenance(model_name: str, embedding_model: str, prompt_version: str = "v1", script_version: str = "1.0.0") -> Dict[str, Any]:
    """
    Generate complete provenance metadata for extraction process.

    Tracks: git commit, models, prompts, execution context
    Enables: reproducibility, debugging, version comparison
    """
    git_info = get_git_info()

    return {
        "extraction_pipeline": {
            "name": "ollama_langchain_pipeline",
            "version": script_version,
            "git_commit": git_info["commit"],
            "git_commit_short": git_info["commit_short"],
            "git_branch": git_info["branch"],
            "git_dirty": git_info["dirty"],
            "repo_url": git_info["repo_url"],
        },
        "models": {
            "llm": {
                "name": model_name,
                "provider": "ollama",
                "temperature": 0.1,
            },
            "embeddings": {
                "name": embedding_model,
                "provider": "huggingface",
            },
        },
        "prompt": {
            "version": prompt_version,
            "template": "medical_extraction_prompt_v1",
        },
        "execution": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hostname": os.uname().nodename,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        },
    }


class EntityDatabase:
    """
    Vector database for entity deduplication and canonical ID resolution.

    Stores known entities and finds similar ones to avoid duplicates.
    Uses ChromaDB for simple local persistence.
    """

    def __init__(self, persist_dir: Path = Path("./data/entity_db"), embedding_model: str = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"):
        """
        Initialize entity database with medical embeddings.

        Args:
            persist_dir: Directory for ChromaDB persistence
            embedding_model: HuggingFace model name. Options:
                - "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext" (default, best for general biomedical)
                - "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext" (PubMed-specific)
                - "dmis-lab/biobert-base-cased-v1.2" (original BioBERT)
                - "pritamdeka/S-PubMedBert-MS-MARCO" (good for similarity search)
        """
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        print(f"Loading medical embeddings: {embedding_model}")

        # Use HuggingFace medical embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model, model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True}  # Use 'cuda' if you have GPU  # Better for similarity search
        )

        # Initialize vector store
        self.db = Chroma(collection_name="medical_entities", embedding_function=self.embeddings, persist_directory=str(persist_dir))

        # In-memory canonical entity mapping
        self.canonical_entities = self._load_canonical_entities()

    def _load_canonical_entities(self) -> Dict[str, Dict]:
        """Load pre-existing canonical entities from disk."""
        canonical_file = self.persist_dir / "canonical_entities.json"
        if canonical_file.exists():
            return json.loads(canonical_file.read_text())
        return {}

    def _save_canonical_entities(self):
        """Persist canonical entities to disk."""
        canonical_file = self.persist_dir / "canonical_entities.json"
        canonical_file.write_text(json.dumps(self.canonical_entities, indent=2))

    def find_or_create_entity(self, entity: Dict[str, Any]) -> str:
        """
        Find existing entity or create new one with canonical ID.

        Returns canonical entity ID.
        """
        entity_name = entity["name"]
        entity_type = entity["type"]

        # Search for similar entities
        search_text = f"{entity_type}: {entity_name}"
        results = self.db.similarity_search_with_score(search_text, k=3)

        # Check if we have a very close match (score < 0.3 is very similar)
        if results and results[0][1] < 0.3:
            existing_doc = results[0][0]
            canonical_id = existing_doc.metadata.get("canonical_id")
            print(f"  Found existing: {entity_name} -> {canonical_id}")
            return canonical_id

        # Create new canonical entity
        canonical_id = entity.get("canonical_id") or self._generate_canonical_id(entity)

        # Store in vector DB
        doc = Document(
            page_content=search_text,
            metadata={
                "canonical_id": canonical_id,
                "name": entity_name,
                "type": entity_type,
                "aliases": json.dumps(entity.get("aliases", [])),
            },
        )
        self.db.add_documents([doc])

        # Store in canonical mapping
        self.canonical_entities[canonical_id] = {
            "id": canonical_id,
            "name": entity_name,
            "type": entity_type,
            "aliases": entity.get("aliases", []),
            "mentions": self.canonical_entities.get(canonical_id, {}).get("mentions", 0) + 1,
        }

        self._save_canonical_entities()

        print(f"  Created new: {entity_name} -> {canonical_id}")
        return canonical_id

    def _generate_canonical_id(self, entity: Dict) -> str:
        """Generate a canonical ID for new entity."""
        # Simple approach: use type prefix + sanitized name
        name_part = entity["name"].lower().replace(" ", "_")[:50]
        entity_type = entity["type"].upper()

        # Check if exists, add counter if needed
        base_id = f"{entity_type}:{name_part}"
        canonical_id = base_id
        counter = 1

        while canonical_id in self.canonical_entities:
            canonical_id = f"{base_id}_{counter}"
            counter += 1

        return canonical_id


class PostgresDatabase:
    """
    SQL database for persisting the medical knowledge graph.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url

    def get_connection(self):
        return psycopg2.connect(self.database_url)

    def save_paper_results(self, output: Dict[str, Any]):
        """Save paper, entities, relationships, and evidence to PostgreSQL."""
        paper_id = output["paper_id"]
        title = output["title"]
        abstract = output["abstract"]
        entities = output["entities"]
        relationships = output["relationships"]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Upsert Paper
                cur.execute(
                    """
                    INSERT INTO papers (id, title, abstract, entity_count, relationship_count)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        abstract = EXCLUDED.abstract,
                        entity_count = EXCLUDED.entity_count,
                        relationship_count = EXCLUDED.relationship_count
                """,
                    (paper_id, title, abstract, len(entities), len(relationships)),
                )

                # 2. Upsert Entities
                for entity in entities:
                    cur.execute(
                        """
                        INSERT INTO entities (id, entity_type, name, canonical_id, mentions, embedding)
                        VALUES (%s, %s, %s, %s, 1, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            mentions = entities.mentions + 1,
                            embedding = EXCLUDED.embedding,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                        (entity["id"], entity["type"], entity["name"], entity["canonical_id"], entity.get("embedding")),
                    )

                # 3. Upsert Relationships and Evidence
                for rel in relationships:
                    # Upsert Relationship
                    cur.execute(
                        """
                        INSERT INTO relationships (subject_id, object_id, predicate, confidence)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (subject_id, object_id, predicate) DO UPDATE SET
                            confidence = (relationships.confidence + EXCLUDED.confidence) / 2.0
                        RETURNING id
                    """,
                        (rel["subject_id"], rel["object_id"], rel["predicate"], rel["confidence"]),
                    )
                    rel_id = cur.fetchone()[0]

                    # Insert Evidence
                    cur.execute(
                        """
                        INSERT INTO evidence (relationship_id, paper_id, section, text_span, confidence)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (rel_id, paper_id, rel.get("section", "unknown"), rel.get("evidence", ""), rel["confidence"]),
                    )

            conn.commit()


class OllamaPaperPipeline:
    """Paper ingestion pipeline using local Ollama models."""

    def __init__(
        self,
        model_name: str = "llama3.1:70b",
        output_dir: Path = Path("./data/papers"),
        entity_db_dir: Path = Path("./data/entity_db"),
        embedding_model: str = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
        prompt_version: str = "v1_detailed",
        database_url: Optional[str] = None,
    ):
        self.llm = OllamaLLM(model=model_name, base_url="http://localhost:11434", temperature=0.1)  # Low temp for more consistent extraction

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.entity_db = EntityDatabase(persist_dir=entity_db_dir, embedding_model=embedding_model)

        # SQL Database
        self.db = None
        if database_url:
            print(f"Connecting to PostgreSQL: {database_url}")
            self.db = PostgresDatabase(database_url)
        elif os.getenv("DATABASE_URL"):
            db_url = os.getenv("DATABASE_URL")
            print(f"Connecting to PostgreSQL via ENV: {db_url}")
            self.db = PostgresDatabase(db_url)

        # Store prompt template for provenance
        self.prompt_template = PROMPT_VERSIONS[prompt_version]
        self.prompt_version = prompt_version

        # Provenance tracker
        self.tracker = get_tracker()

        print(f"Using LLM model: {model_name}")
        print(f"Using embeddings: {embedding_model}")
        print(f"Using prompt: {prompt_version}")

    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed Central and return PMC IDs."""
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pmc", "term": query, "retmax": max_results, "retmode": "json", "sort": "relevance"}

        response = requests.get(search_url, params=params)
        response.raise_for_status()

        data = response.json()
        pmc_ids = data.get("esearchresult", {}).get("idlist", [])

        print(f"Found {len(pmc_ids)} papers for query: {query}")
        return [f"PMC{id}" for id in pmc_ids]

    def fetch_paper_xml(self, pmc_id: str) -> str:
        """Fetch JATS XML for a paper."""
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {"db": "pmc", "id": pmc_id.replace("PMC", ""), "rettype": "full", "retmode": "xml"}

        response = requests.get(fetch_url, params=params)
        response.raise_for_status()

        return response.text

    def extract_text_from_xml(self, xml_content: str) -> Dict[str, str]:
        """Extract title, abstract, and sections from JATS XML."""
        import re

        title_match = re.search(r"<article-title>(.*?)</article-title>", xml_content, re.DOTALL)
        abstract_match = re.search(r"<abstract[^>]*>(.*?)</abstract>", xml_content, re.DOTALL)

        def clean_xml(text):
            return re.sub(r"<[^>]+>", "", text).strip() if text else ""

        return {
            "title": clean_xml(title_match.group(1)) if title_match else "",
            "abstract": clean_xml(abstract_match.group(1)) if abstract_match else "",
            "full_text": clean_xml(xml_content)[:30000],  # Limit for context window
        }

    def extract_entities_with_ollama(self, paper_text: Dict[str, str], pmc_id: str) -> Dict[str, Any]:
        """Use Ollama to extract entities and relationships with enterprise prompt."""

        # Format the prompt template with paper data
        prompt = self.prompt_template.format(title=paper_text["title"], abstract=paper_text["abstract"])

        # Call Ollama
        response = self.llm.invoke(prompt)

        # Parse JSON from response
        import re

        # Try to extract JSON from response (in case model adds explanation)
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            response = json_match.group(0)

        try:
            extracted_data = json.loads(response)
            extracted_data["paper_id"] = pmc_id
            extracted_data["title"] = paper_text["title"]
            extracted_data["abstract"] = paper_text["abstract"]

            # Resolve entities to canonical IDs
            extracted_data = self._resolve_entities(extracted_data)

            return extracted_data

        except json.JSONDecodeError as e:
            print(f"  Failed to parse LLM response: {e}")
            print(f"  Response preview: {response[:500]}")
            return None

    def _resolve_entities(self, extracted_data: Dict) -> Dict:
        """Resolve extracted entities to canonical IDs using entity DB."""
        entities = extracted_data.get("entities", [])
        relationships = extracted_data.get("relationships", [])

        # Map: extracted name -> canonical ID
        name_to_canonical = {}

        # Resolve each entity
        resolved_entities = []
        for entity in entities:
            canonical_id = self.entity_db.find_or_create_entity(entity)
            name_to_canonical[entity["name"]] = canonical_id

            resolved_entities.append({"id": canonical_id, "name": entity["name"], "type": entity["type"], "canonical_id": canonical_id})

        # Update relationships with canonical IDs
        resolved_relationships = []
        for rel in relationships:
            subject_name = rel["subject"]
            object_name = rel["object"]

            if subject_name in name_to_canonical and object_name in name_to_canonical:
                resolved_relationships.append(
                    {
                        "subject_id": name_to_canonical[subject_name],
                        "predicate": rel["predicate"].lower(),
                        "object_id": name_to_canonical[object_name],
                        "confidence": rel.get("confidence", 0.8),
                        "evidence": rel.get("evidence", ""),
                        "section": rel.get("section", "unknown"),
                    }
                )

        extracted_data["entities"] = resolved_entities
        extracted_data["relationships"] = resolved_relationships

        return extracted_data

    def process_paper(self, pmc_id: str) -> Optional[Dict]:
        """Process a single paper with full provenance tracking."""
        print(f"Processing {pmc_id}...")

        output_file = self.output_dir / f"{pmc_id}.json"
        if output_file.exists():
            print("  Already processed, skipping")
            return json.loads(output_file.read_text())

        start_time = datetime.now()

        try:
            # Fetch paper
            xml_content = self.fetch_paper_xml(pmc_id)
            paper_text = self.extract_text_from_xml(xml_content)

            if not paper_text["title"]:
                print("  No title found, skipping")
                return None

            # Extract with Ollama
            extracted = self.extract_entities_with_ollama(paper_text, pmc_id)

            if extracted:
                end_time = datetime.now()

                # Generate embeddings for entities for Postgres
                if self.db:
                    for entity in extracted.get("entities", []):
                        # Use the same embedding model as the entity_db
                        search_text = f"{entity['type']}: {entity['name']}"
                        embedding = self.entity_db.embeddings.embed_query(search_text)
                        entity["embedding"] = embedding

                # Create provenance record
                provenance = self.tracker.create_provenance_record(
                    paper_id=pmc_id,
                    model_name=self.llm.model,
                    embedding_model=self.entity_db.embeddings.model_name,
                    prompt_template=self.prompt_template,
                    processing_start=start_time,
                    processing_end=end_time,
                    additional_metadata={"entity_db_size": len(self.entity_db.canonical_entities), "xml_length": len(xml_content), "prompt_version": self.prompt_version},
                )

                # Create final output with provenance
                output = create_paper_output(
                    paper_id=pmc_id,
                    title=paper_text["title"],
                    abstract=paper_text["abstract"],
                    entities=extracted.get("entities", []),
                    relationships=extracted.get("relationships", []),
                    metadata=extracted.get("metadata", {}),
                    provenance=provenance,
                )

                # Save result
                output_file.write_text(json.dumps(output, indent=2))

                # Save to PostgreSQL if available
                if self.db:
                    try:
                        self.db.save_paper_results(output)
                        print("  ✓ Persisted to PostgreSQL")
                    except Exception as pg_e:
                        print(f"  × PostgreSQL error: {pg_e}")

                print(f"  ✓ Extracted {len(output['entities'])} entities, " f"{len(output['relationships'])} relationships")
                print(f"  ✓ Pipeline ID: {self.tracker.generate_pipeline_id(provenance)}")

                return output

            return None

        except Exception as e:
            print(f"  Error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def ingest_batch(self, pmc_ids: List[str], delay: float = 1.0):
        """Process batch of papers."""
        results = []

        for idx, pmc_id in enumerate(pmc_ids, 1):
            print(f"\n[{idx}/{len(pmc_ids)}] ", end="")

            result = self.process_paper(pmc_id)
            if result:
                results.append(result)

            if idx < len(pmc_ids):
                time.sleep(delay)

        print(f"\n\nCompleted: {len(results)}/{len(pmc_ids)} papers")

        # Print entity DB stats
        print(f"\nEntity Database: {len(self.entity_db.canonical_entities)} canonical entities")

        return results


def main():
    parser = argparse.ArgumentParser(description="Ingest papers with Ollama + LangChain")
    parser.add_argument("--query", required=True, help="PubMed search query")
    parser.add_argument("--limit", type=int, default=50, help="Max papers")
    parser.add_argument("--model", default="llama3.1:70b", help="Ollama model name")
    parser.add_argument("--embedding-model", default="microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext", help="HuggingFace embedding model for entity matching")
    parser.add_argument("--output-dir", type=Path, default=Path("./data/papers"))
    parser.add_argument("--entity-db-dir", type=Path, default=Path("./data/entity_db"))
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between papers")

    args = parser.parse_args()

    # Create pipeline
    db_url = os.getenv("DATABASE_URL")
    pipeline = OllamaPaperPipeline(model_name=args.model, output_dir=args.output_dir, entity_db_dir=args.entity_db_dir, embedding_model=args.embedding_model, database_url=db_url)

    # Search and process
    pmc_ids = pipeline.search_pubmed(args.query, max_results=args.limit)

    if not pmc_ids:
        print("No papers found")
        return 1

    pipeline.ingest_batch(pmc_ids, delay=args.delay)

    print(f"\nResults in: {args.output_dir}")
    print(f"Entity DB in: {args.entity_db_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
