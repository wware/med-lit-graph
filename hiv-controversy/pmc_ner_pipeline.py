# pmc_ner_pipeline.py
"""
Let’s put together a **Python pipeline** to extract entities from your PMC
XMLs, normalize them with UMLS IDs (via SciSpacy), and output a CSV suitable
for building a knowledge graph.

### **How it works**

1.  Reads all `PMC*.xml` files from `./pmc_xmls`.
2.  Extracts abstract text first; falls back to `<body>` if abstract missing.
3.  Uses **SciSpacy** with **UMLS linking** to find biomedical entities.
4.  Outputs CSV with columns:

```
pmc_id, source_text, entity_text, umls_cuis
```

-   `source_text` can be used for context in KG edges.
-   `umls_cuis` gives canonical IDs, so multiple mentions of the same entity
    across papers can be merged.
    
### **Next Steps / Improvements**

-   Add **sentence-level splitting** if you want to extract co-occurrence or relationships.
-   Consider **filtering entity types** (genes, chemicals, diseases) to reduce noise.
-   Later, you can ingest this CSV into **Neo4j** or **NetworkX** to build the knowledge graph.

If you want, I can also extend this script to **produce a node & edge CSV for
Neo4j directly**, so you could load your KG without extra processing.

CSV will not be the last word on formatting this stuff, but it's sufficient for now.
"""

# pmc_ner_pipeline_epistemic.py
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import pandas as pd
from lxml import etree
from pathlib import Path
import sqlite3
from datetime import datetime

# ------------------------------
# Setup NER pipeline
# ------------------------------
# Use a model with clear NER capabilities
model_name = "ugaray96/biobert_ncbi_disease_ner"  # Well-documented, NCBI disease NER
# For diseases specifically (best for HIV/AIDS focus)
# model_name = "alvaroalon2/biobert_diseases_ner"  # BC5CDR + NCBI diseases
# model_name = "d4data/biomedical-ner-all"  # Multi-corpus trained
# model_name = "raynardj/ner-disease-ncbi-bionlp-bc5cdr-pubmed"
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
import os
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

def get_or_create_entity(name, entity_type="GENERIC", source=None, confidence=None):
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

    # Extract text
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
        # Skip if it's not actually an entity label
        label = ent.get("entity_group", ent.get("entity", "O"))
        if label == "O" or label == "0" or not label.startswith(("B-", "I-", "DISEASE", "CHEMICAL")):
            continue

        name = ent["word"].strip()

        # Skip obvious garbage
        if len(name) < 2 or name in ["(", ")", ",", ".", "-"]:
            continue
        if name.startswith("##"):
            continue

        label = ent.get("entity_group", "GENERIC")
        confidence = ent.get("score", None)

        entity_id = get_or_create_entity(
            name=name,
            entity_type=label,
            source=pmc_id,
            confidence=confidence
        )

        nodes.append({
            "id": entity_id,
            "name": name,
            "type": label,
            "source": pmc_id,
            "confidence": confidence
        })

        entity_ids_in_text.append(entity_id)

    # Build co-occurrence edges with counts
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

# Write CSVs for Neo4j
nodes_df.to_csv("/app/output/nodes.csv", index=False)
edges_df.to_csv("/app/output/edges.csv", index=False)

print(f"Processed {processed_count} XML files.")
print(f"Nodes: {len(nodes_df)}, Edges: {len(edges_df)}")
