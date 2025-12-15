"""
Provenance tracking utilities for the ingestion pipeline.

Provides helper functions for creating provenance records and formatting paper outputs.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib


class ProvenanceTracker:
    """
    Tracks provenance information for paper extraction pipeline.

    Provides methods to generate consistent provenance records across different
    ingestion methods (Ollama, Claude, etc.).
    """

    def __init__(self, script_version: str = "1.0.0"):
        self.script_version = script_version
        self.git_info = self._get_git_info()

    def _get_git_info(self) -> Dict[str, Any]:
        """Get current git commit and branch info for provenance."""
        try:
            # Get the repository root (parent of ingestion directory)
            repo_root = Path(__file__).parent.parent

            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, cwd=repo_root).decode("ascii").strip()

            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL, cwd=repo_root).decode("ascii").strip()

            # Check if working directory is clean
            status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, cwd=repo_root).decode("ascii").strip()

            is_dirty = len(status) > 0

            return {"commit": commit, "commit_short": commit[:7], "branch": branch, "dirty": is_dirty, "repo_url": "https://github.com/wware/med-lit-graph"}
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"commit": "unknown", "commit_short": "unknown", "branch": "unknown", "dirty": False, "repo_url": "unknown"}

    def create_provenance_record(
        self, paper_id: str, model_name: str, embedding_model: str, prompt_template: str, processing_start: datetime, processing_end: datetime, additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a complete provenance record for a paper extraction.

        Args:
            paper_id: Paper identifier (PMC ID, etc.)
            model_name: Name of the LLM used for extraction
            embedding_model: Name of the embedding model used
            prompt_template: The prompt template text
            processing_start: When extraction started
            processing_end:  When extraction completed
            additional_metadata: Extra metadata to include

        Returns:
            Complete provenance dictionary
        """
        duration = (processing_end - processing_start).total_seconds()

        # Calculate prompt checksum for reproducibility
        prompt_checksum = hashlib.sha256(prompt_template.encode()).hexdigest()

        provenance = {
            "extraction_pipeline": {
                "name": "ollama_langchain_pipeline",
                "version": self.script_version,
                "git_commit": self.git_info["commit"],
                "git_commit_short": self.git_info["commit_short"],
                "git_branch": self.git_info["branch"],
                "git_dirty": self.git_info["dirty"],
                "repo_url": self.git_info["repo_url"],
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
            "prompt": {"version": "v1", "template": "medical_extraction_prompt_v1", "checksum": prompt_checksum},  # Update this as prompts evolve
            "execution": {
                "timestamp": processing_start.isoformat() + "Z",
                "hostname": os.uname().nodename,
                "python_version": f"{sys.version_info.major}.{sys.version_info. minor}. {sys.version_info.micro}",
                "duration_seconds": duration,
            },
        }

        # Add additional metadata if provided
        if additional_metadata:
            provenance.update(additional_metadata)

        return provenance

    def generate_pipeline_id(self, provenance: Dict[str, Any]) -> str:
        """
        Generate a unique pipeline ID from provenance data.

        Useful for grouping papers extracted with identical pipeline configurations.

        Args:
            provenance:  Provenance dictionary

        Returns:
            Unique pipeline identifier (short hash)
        """
        # Create a stable string representation of the pipeline config
        pipeline_config = f"{provenance['extraction_pipeline']['git_commit_short']}_" f"{provenance['models']['llm']['name']}_" f"{provenance['prompt']['version']}"

        # Generate short hash
        pipeline_hash = hashlib.sha256(pipeline_config.encode()).hexdigest()[:8]

        return f"pipeline_{pipeline_hash}"


def create_paper_output(paper_id: str, title: str, abstract: str, entities: list, relationships: list, metadata: dict, provenance: dict) -> Dict[str, Any]:
    """
    Create a complete paper output JSON structure.

    Args:
        paper_id: Paper identifier
        title: Paper title
        abstract: Paper abstract
        entities:  List of extracted entities
        relationships: List of extracted relationships
        metadata: Paper metadata
        provenance: Provenance record

    Returns:
        Complete paper dictionary ready for JSON serialization
    """
    return {"paper_id": paper_id, "title": title, "abstract": abstract, "entities": entities, "relationships": relationships, "metadata": metadata, "extraction_provenance": provenance}


# Singleton instance
_tracker: Optional[ProvenanceTracker] = None


def get_tracker(script_version: str = "1.0.0") -> ProvenanceTracker:
    """Get or create the global provenance tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProvenanceTracker(script_version=script_version)
    return _tracker
