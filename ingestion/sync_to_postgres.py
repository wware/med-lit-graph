#!/usr/bin/env python3
"""
Sync tool to load existing paper JSON files into PostgreSQL with vector embeddings.
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psycopg2
from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from ingestion.ingest_papers import EntityDatabase, PostgresDatabase
except ImportError:
    from ingest_papers import EntityDatabase, PostgresDatabase


def sync_papers(papers_dir: Path, db_url: str, embedding_model: str):
    print(f"Syncing papers from {papers_dir} to PostgreSQL...")

    db = PostgresDatabase(db_url)

    # Initialize embeddings for entity vectorization
    print(f"Loading embeddings: {embedding_model}")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model, model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True})

    paper_files = list(papers_dir.glob("*.json"))
    print(f"Found {len(paper_files)} papers.")

    for idx, paper_file in enumerate(paper_files, 1):
        print(f"[{idx}/{len(paper_files)}] Processing {paper_file.name}...")
        try:
            with open(paper_file, "r") as f:
                data = json.load(f)

            # Extract entities and generate embeddings if missing
            entities = data.get("entities", [])
            for entity in entities:
                if "embedding" not in entity or entity["embedding"] is None:
                    search_text = f"{entity['type']}: {entity['name']}"
                    entity["embedding"] = embeddings.embed_query(search_text)

            # Ensure predicates are lowercase
            relationships = data.get("relationships", [])
            for rel in relationships:
                rel["predicate"] = rel["predicate"].lower()

            # Save to PostgreSQL
            db.save_paper_results(data)
            print(f"  ✓ Synced {paper_file.name}")

        except Exception as e:
            print(f"  × Error syncing {paper_file.name}: {e}")

    print("\nSync completed.")


def main():
    parser = argparse.ArgumentParser(description="Sync paper JSONs to Postgres")
    parser.add_argument("--papers-dir", type=Path, default=Path("./data/papers"), help="Directory containing paper JSONs")
    parser.add_argument("--embedding-model", default="microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext", help="Embedding model name")

    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set.")
        return 1

    sync_papers(args.papers_dir, db_url, args.embedding_model)
    return 0


if __name__ == "__main__":
    exit(main())
