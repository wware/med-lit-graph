"""
Provenance tracking utilities for modular pipeline.

Tracks git info, model info, execution context for reproducibility.
Adapted from hiv-controversy branch with current schema.
"""

import platform
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class GitInfo:
    """Git repository information."""

    commit: str
    commit_short: str
    branch: str
    dirty: bool
    repo_url: str


@dataclass
class PipelineInfo:
    """Pipeline execution information."""

    name: str
    version: str
    stage: Optional[str] = None


@dataclass
class ModelInfo:
    """Model information."""

    name: str
    provider: str
    temperature: Optional[float] = None
    version: Optional[str] = None


@dataclass
class PromptInfo:
    """Prompt template information."""

    version: str
    template: str
    checksum: Optional[str] = None


@dataclass
class ExecutionInfo:
    """Execution context information."""

    timestamp: str
    hostname: str
    python_version: str
    duration_seconds: Optional[float] = None


def get_git_info() -> GitInfo:
    """Get current git repository information."""
    try:
        # Get repo root
        repo_root = Path(__file__).parent.parent.parent

        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, cwd=repo_root).decode().strip()

        commit_short = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, cwd=repo_root).decode().strip()

        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL, cwd=repo_root).decode().strip()

        # Check if working directory is dirty
        dirty = subprocess.call(["git", "diff", "--quiet"], stderr=subprocess.DEVNULL, cwd=repo_root) != 0

        return GitInfo(commit=commit, commit_short=commit_short, branch=branch, dirty=dirty, repo_url="https://github.com/wware/med-lit-graph")
    except Exception:
        return GitInfo(commit="unknown", commit_short="unknown", branch="unknown", dirty=False, repo_url="unknown")


def create_provenance(
    pipeline_info: PipelineInfo, model_info: ModelInfo, prompt_info: Optional[PromptInfo] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create complete provenance dictionary.

    Args:
        pipeline_info: Pipeline information
        model_info: Model information
        prompt_info: Optional prompt information
        start_time: Optional start time
        end_time: Optional end time for duration calculation

    Returns:
        Provenance dictionary
    """
    git_info = get_git_info()

    duration = None
    if start_time and end_time:
        duration = (end_time - start_time).total_seconds()

    execution_info = ExecutionInfo(timestamp=datetime.now().isoformat(), hostname=socket.gethostname(), python_version=platform.python_version(), duration_seconds=duration)

    provenance = {
        "extraction_pipeline": {
            **asdict(pipeline_info),
            "git_commit": git_info.commit,
            "git_commit_short": git_info.commit_short,
            "git_branch": git_info.branch,
            "git_dirty": git_info.dirty,
            "repo_url": git_info.repo_url,
        },
        "model": asdict(model_info),
        "execution": asdict(execution_info),
    }

    if prompt_info:
        provenance["prompt"] = asdict(prompt_info)

    return provenance


def add_provenance_to_record(record: Dict[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
    """Add provenance to a record dictionary."""
    record["provenance"] = provenance
    return record
