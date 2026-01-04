#!/usr/bin/env python3
"""
Test flexible relationship parsing with multiple formats.
"""

import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.ingest_papers import OllamaPaperPipeline


def test_flexible_parsing():
    """Test that both relationship formats work."""

    # Mock extracted data with BOTH formats
    extracted_data = {
        "entities": [
            {"name": "Metformin", "type": "drug"},
            {"name": "Diabetes", "type": "disease"},
        ],
        "relationships": [
            # Correct format
            {"subject": "Metformin", "predicate": "treats", "object": "Diabetes"},
            # Alternative format (what llama3.1:8b returns)
            {"entity1": "Metformin", "relationship": "compared to", "entity2": "Diabetes"},
            # Mixed format (should still work)
            {"subject": "Metformin", "relationship": "prevents", "entity2": "Diabetes"},
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = OllamaPaperPipeline(entity_db_dir=Path(tmpdir) / "test_entity_db", embedding_model="sentence-transformers/all-MiniLM-L6-v2")

        print("Testing flexible relationship parsing...")
        resolved = pipeline._resolve_entities(extracted_data)

        print(f"\n✓ Input: {len(extracted_data['relationships'])} relationships")
        print(f"✓ Output: {len(resolved['relationships'])} valid relationships")

        # Check predicates are normalized
        for rel in resolved["relationships"]:
            print(f"  - {rel['predicate']}")

        if len(resolved["relationships"]) == 3:
            print("\n✅ SUCCESS: All relationship formats parsed!")
            return True
        else:
            print(f"\n❌ FAILURE: Expected 3 relationships, got {len(resolved['relationships'])}")
            return False


if __name__ == "__main__":
    success = test_flexible_parsing()
    sys.exit(0 if success else 1)
