import json
import logging
import os

from query_executor import execute_query

# Mock entities/relationships for non-vector parts (execute_query signature requires them)
entities = {}
relationships = []

# Mock vector search query
query = {"vector_search": {"text": "metformin diabetes", "top_k": 5}, "return_fields": ["name", "entity_type", "similarity"]}

# Ensure DB URL is set (mimic the environment)
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/medlitgraph"

logging.basicConfig(level=logging.INFO)
print("Executing vector search query...")

try:
    result = execute_query(query, entities, relationships)
    print(json.dumps(result, indent=2))

    if "error" in result:
        print("Test FAILED with error")
        exit(1)

    if not result["results"]:
        print("Test PASSED but returned no results (DB might be empty of matching entities)")
    else:
        print(f"Test PASSED with {len(result['results'])} results")

except Exception as e:
    print(f"Test FAILED with exception: {e}")
    exit(1)
