"""
Test utilities for modular pipeline.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from ingestion.utils import ModelInfo, PipelineInfo, PromptInfo, count_jsonl, create_provenance, read_jsonl, write_jsonl


def test_jsonl_write_read():
    """Test JSONL writing and reading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.jsonl"

        # Write data
        data = [
            {"id": "1", "name": "Test 1"},
            {"id": "2", "name": "Test 2"},
        ]
        count = write_jsonl(data, output_path)
        assert count == 2

        # Read data
        records = list(read_jsonl(output_path))
        assert len(records) == 2
        assert records[0]["name"] == "Test 1"

        # Count records
        assert count_jsonl(output_path) == 2

    print("✓ JSONL write/read test passed")


def test_provenance():
    """Test provenance creation."""
    pipeline_info = PipelineInfo(name="test_pipeline", version="1.0.0", stage="stage1")

    model_info = ModelInfo(name="llama3.1:70b", provider="ollama", temperature=0.1)

    prompt_info = PromptInfo(version="v1", template="medical_extraction", checksum="abc123")

    start_time = datetime.now()
    end_time = datetime.now()

    provenance = create_provenance(pipeline_info=pipeline_info, model_info=model_info, prompt_info=prompt_info, start_time=start_time, end_time=end_time)

    # Verify structure
    assert "extraction_pipeline" in provenance
    assert "model" in provenance
    assert "prompt" in provenance
    assert "execution" in provenance

    assert provenance["extraction_pipeline"]["name"] == "test_pipeline"
    assert provenance["model"]["name"] == "llama3.1:70b"
    assert provenance["prompt"]["version"] == "v1"

    print("✓ Provenance test passed")


if __name__ == "__main__":
    test_jsonl_write_read()
    test_provenance()
    print("\n✅ All utility tests passed!")
