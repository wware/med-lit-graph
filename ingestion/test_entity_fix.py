#!/usr/bin/env python3
"""
Test that different neurodegenerative diseases don't match each other.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.ingest_papers import EntityDatabase


def test_neurodegenerative_diseases():
    """Test that similar diseases get unique IDs."""

    with tempfile.TemporaryDirectory() as tmpdir:
        entity_db = EntityDatabase(persist_dir=Path(tmpdir) / "test_entity_db", embedding_model="sentence-transformers/all-MiniLM-L6-v2")

        # These are all neurodegenerative diseases - should NOT match
        test_entities = [
            {"name": "Alzheimer's Disease", "type": "disease", "aliases": []},
            {"name": "Parkinson's Disease", "type": "disease", "aliases": []},
            {"name": "Huntington's Disease", "type": "disease", "aliases": []},
            {"name": "Alzheimer's Disease", "type": "disease", "aliases": []},  # Exact duplicate - should match
        ]

        canonical_ids = []
        for entity in test_entities:
            canonical_id = entity_db.find_or_create_entity(entity)
            canonical_ids.append(canonical_id)
            print(f"{entity['name']} -> {canonical_id}")

        # Should have 3 unique IDs (4th is duplicate of 1st)
        unique_ids = set(canonical_ids)
        print(f"\n✓ Created {len(canonical_ids)} entities")
        print(f"✓ {len(unique_ids)} unique canonical IDs")

        # Check that first and last match (exact duplicates)
        if canonical_ids[0] == canonical_ids[3]:
            print(f"✓ Exact duplicate matched correctly")
        else:
            print(f"✗ Exact duplicate did NOT match")
            return False

        # Check that different diseases don't match
        if len(unique_ids) == 3:
            print("\n✅ SUCCESS: Different diseases have unique IDs!")
            return True
        else:
            print(f"\n❌ FAILURE: Expected 3 unique IDs, got {len(unique_ids)}")
            print(f"IDs: {canonical_ids}")
            return False


if __name__ == "__main__":
    success = test_neurodegenerative_diseases()
    sys.exit(0 if success else 1)
