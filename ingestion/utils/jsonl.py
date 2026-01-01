"""
JSONL utilities for modular pipeline.

Provides consistent reading/writing of JSONL files with validation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def write_jsonl(data: List[Dict[str, Any]], output_path: Path, append: bool = False) -> int:
    """
    Write data to JSONL file.

    Args:
        data: List of dictionaries to write
        output_path: Path to output file
        append: If True, append to existing file

    Returns:
        Number of records written
    """
    mode = "a" if append else "w"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode) as f:
        for record in data:
            f.write(json.dumps(record) + "\n")

    return len(data)


def read_jsonl(input_path: Path, validate: Optional[callable] = None) -> Iterator[Dict[str, Any]]:
    """
    Read JSONL file line by line.

    Args:
        input_path: Path to input file
        validate: Optional validation function that raises on invalid record

    Yields:
        Dictionaries from JSONL file
    """
    if not input_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {input_path}")

    with open(input_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)

                if validate:
                    validate(record)

                yield record
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}")
            except Exception as e:
                raise ValueError(f"Validation failed on line {line_num}: {e}")


def count_jsonl(input_path: Path) -> int:
    """Count records in JSONL file."""
    if not input_path.exists():
        return 0

    count = 0
    with open(input_path, "r") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def append_jsonl(record: Dict[str, Any], output_path: Path) -> None:
    """Append single record to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "a") as f:
        f.write(json.dumps(record) + "\n")


def validate_entity_record(record: Dict[str, Any]) -> None:
    """Validate entity JSONL record."""
    required_fields = ["entity_id", "entity_type", "name"]

    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")

    if "provenance" not in record:
        raise ValueError("Missing provenance field")


def validate_relationship_record(record: Dict[str, Any]) -> None:
    """Validate relationship JSONL record."""
    required_fields = ["subject_id", "predicate", "object_id"]

    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")

    if "provenance" not in record:
        raise ValueError("Missing provenance field")


class JSONLWriter:
    """Context manager for writing JSONL files."""

    def __init__(self, output_path: Path, append: bool = False):
        self.output_path = output_path
        self.append = append
        self.file = None
        self.count = 0

    def __enter__(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if self.append else "w"
        self.file = open(self.output_path, mode)
        return self

    def write(self, record: Dict[str, Any]) -> None:
        """Write a single record."""
        self.file.write(json.dumps(record) + "\n")
        self.count += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        return False
