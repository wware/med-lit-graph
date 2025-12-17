# pmc_ner_pipeline.py
"""
Stage 1: Entity Extraction Pipeline

Extracts biomedical entities from PMC XML files using BioBERT NER model.
Stores canonical entities in SQLite with alias mappings for entity resolution.
Outputs co-occurrence edges for knowledge graph construction.

Usage:
    docker-compose run pipeline

Output:
    - entities.db: SQLite database with canonical entities and aliases
    - nodes.csv: Extracted nodes for debugging/inspection
    - edges.csv: Co-occurrence edges for debugging/inspection
"""

from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import pandas as pd
from lxml import etree
from pathlib import Path
import sqlite3
from datetime import datetime
import os

# ------------------------------
# Setup NER pipeline
# ------------------------------
model_name = "ugaray96/biobert_ncbi_disease_ner"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
ner_pipeline = pipeline(
    "ner", 
    model=model, 
    tokenizer=tokenizer, 
    aggregation_strategy="simple"  # Groups subwords into entities
)

# ------------------------------
# Setup SQLite canonical entity DB
# ------------------------------
os.makedirs("/app/output", exist_ok=True)
db_path = "/app/output/entities.db"
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON;")

# Create tables
conn.execute("""
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE,
    type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    name TEXT UNIQUE,
    source TEXT,
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# Stopwords to filter out common non-entity words
STOPWORDS = {
    "acquired", "human", "chronic", "enter", "lymph",
    "the", "and", "or", "but", "with", "from", "that",
    "this", "these", "those", "their", "there"
}

def get_or_create_entity(name, entity_type="GENERIC", source=None, confidence=None):
    """
    Get existing entity ID or create new canonical entity with alias.
    
    This enables entity resolution: multiple mentions of the same entity
    (e.g., "HIV", "HTLV-III", "LAV") can be mapped to the same canonical ID.
    Currently does simple name matching; Stage 3 will add embedding-based clustering.
    """
    # Check if alias exists
    cursor = conn.execute("SELECT entity_id FROM aliases WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]  # return existing canonical ID

    # Insert new entity if needed
    cursor = conn.execute(
        "INSERT OR IGNORE INTO entities (canonical_name, type) VALUES (?, ?)",
        (name, entity_type)
    )
    entity_id = cursor.lastrowid
    if entity_id == 0:
        cursor = conn.execute("SELECT id FROM entities WHERE canonical_name=?", (name,))
        entity_id = cursor.fetchone()[0]

    # Insert alias
    conn.execute(
        "INSERT OR IGNORE INTO aliases (entity_id, name, source, confidence) VALUES (?, ?, ?, ?)",
        (entity_id, name, source, confidence)
    )
    conn.commit()
    return entity_id

# ------------------------------
# Process PMC XMLs
# ------------------------------
input_dir = Path("./pmc_xmls")
nodes = []
edges_dict = {}  # {(subject_id, object_id): count}
processed_count = 0

for xml_file in input_dir.glob("PMC*.xml"):
    pmc_id = xml_file.stem
    tree = etree.parse(str(xml_file))
    root = tree.getroot()

    # Extract text - prefer abstract, fall back to body
    text_chunks = [p.text for p in root.findall(".//abstract//p") if p.text]
    if not text_chunks:
        text_chunks = [p.text for p in root.findall(".//body//p") if p.text]
    if not text_chunks:
        continue
    full_text = " ".join(text_chunks)

    # Run NER
    entities = ner_pipeline(full_text)
    entity_ids_in_text = []

    for ent in entities:
        # Filter by entity label - this model uses 'Disease' and 'No Disease'
        label = ent.get("entity_group", ent.get("entity", "O"))
        if label != "Disease":
            continue

        name = ent["word"].strip()

        # Skip obvious garbage
        if len(name) < 3:  # Minimum 3 characters
            continue
        if name in ["(", ")", ",", ".", "-"]:
            continue
        if name.startswith("##"):  # Subword tokens
            continue
        if name.lower() in STOPWORDS:  # Common non-entity words
            continue

        confidence = ent.get("score", None)
        
        # Skip low-confidence predictions to reduce noise
        if confidence and confidence < 0.85:
            continue

        # Get or create canonical entity
        entity_id = get_or_create_entity(
            name=name,
            entity_type=label,
            source=pmc_id,
            confidence=confidence
        )

        # Store node for CSV output
        nodes.append({
            "id": entity_id,
            "name": name,
            "type": label,
            "source": pmc_id,
            "confidence": confidence
        })

        entity_ids_in_text.append(entity_id)

    # Build co-occurrence edges with counts
    # This is EXTRACTION layer only - no semantic predicates yet (that's Stage 4)
    for i in range(len(entity_ids_in_text)):
        for j in range(i + 1, len(entity_ids_in_text)):
            key = tuple(sorted((entity_ids_in_text[i], entity_ids_in_text[j])))
            edges_dict[key] = edges_dict.get(key, 0) + 1
    
    processed_count += 1

# ------------------------------
# Convert nodes and edges to DataFrames
# ------------------------------
nodes_df = pd.DataFrame(nodes).drop_duplicates(subset=["id"])
edges_df = pd.DataFrame([
    {"subject_id": k[0], "object_id": k[1], "relation": "co_occurrence", "weight": v}
    for k, v in edges_dict.items()
])

# Write CSVs for inspection/debugging
nodes_df.to_csv("/app/output/nodes.csv", index=False)
edges_df.to_csv("/app/output/edges.csv", index=False)

print(f"Processed {processed_count} XML files.")
print(f"Nodes: {len(nodes_df)}, Edges: {len(edges_df)}")

# Close database connection
conn.close()
