"""
Practical Example: Using SQL Mixin with Existing Entity Models

This demonstrates how to add SQLMixin to your existing Pydantic models
and use it for database operations.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent / "schema"))
from sql_mixin import SQLMixin

# ============================================================================
# Add SQLMixin to Existing Models
# ============================================================================


class Disease(BaseModel, SQLMixin):
    """Disease entity with SQL generation capabilities"""

    id: str
    name: str
    synonyms: list[str] = []
    abbreviations: list[str] = []
    umls_id: Optional[str] = None
    mesh_id: Optional[str] = None
    icd10_codes: list[str] = []
    category: Optional[str] = None
    created_at: datetime = datetime.now()
    source: str = "extracted"


# ============================================================================
# Database Setup
# ============================================================================


def setup_database():
    """Create database and tables"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row  # Enable dict-like access

    # Generate and execute CREATE TABLE
    create_sql = Disease.create_table_sql(dialect="sqlite")
    print("Creating table...")
    print(create_sql)
    print()

    conn.execute(create_sql)
    return conn


# ============================================================================
# CRUD Operations
# ============================================================================


def insert_disease(conn, disease: Disease):
    """Insert a disease into the database"""
    insert_sql, params = Disease.insert_sql(dialect="sqlite")
    db_dict = disease.to_db_dict(dialect="sqlite")

    values = [db_dict[p] for p in params]
    conn.execute(insert_sql, values)
    conn.commit()

    print(f"✓ Inserted: {disease.name}")


def get_disease_by_id(conn, disease_id: str) -> Optional[Disease]:
    """Retrieve a disease by ID"""
    select_sql = Disease.select_sql(where="id = ?")

    row = conn.execute(select_sql, (disease_id,)).fetchone()
    if row:
        return Disease.from_db_dict(dict(row), dialect="sqlite")
    return None


def get_all_diseases(conn) -> list[Disease]:
    """Retrieve all diseases"""
    select_sql = Disease.select_sql()

    rows = conn.execute(select_sql).fetchall()
    return [Disease.from_db_dict(dict(row), dialect="sqlite") for row in rows]


def update_disease(conn, disease: Disease):
    """Update a disease"""
    update_sql, params = Disease.update_sql(where="id = ?", dialect="sqlite")
    db_dict = disease.to_db_dict(dialect="sqlite")

    values = [db_dict[p] for p in params] + [disease.id]
    conn.execute(update_sql, values)
    conn.commit()

    print(f"✓ Updated: {disease.name}")


# ============================================================================
# Demo
# ============================================================================


def main():
    print("=" * 70)
    print("Practical SQL Mixin Example")
    print("=" * 70)
    print()

    # Setup
    conn = setup_database()

    # Create some diseases
    print("1. Creating diseases...")
    diseases = [
        Disease(
            id="UMLS:C0006142",
            name="Breast Cancer",
            synonyms=["Breast Carcinoma", "Mammary Cancer"],
            abbreviations=["BC"],
            umls_id="C0006142",
            mesh_id="D001943",
            icd10_codes=["C50.9"],
            category="genetic",
        ),
        Disease(id="UMLS:C0011860", name="Type 2 Diabetes Mellitus", synonyms=["T2DM", "Type II Diabetes"], abbreviations=["T2DM"], umls_id="C0011860", icd10_codes=["E11.9"], category="metabolic"),
        Disease(id="UMLS:C0020538", name="Hypertension", synonyms=["High Blood Pressure", "HTN"], abbreviations=["HTN", "HBP"], umls_id="C0020538", icd10_codes=["I10"], category="cardiovascular"),
    ]

    for disease in diseases:
        insert_disease(conn, disease)
    print()

    # Retrieve by ID
    print("2. Retrieving disease by ID...")
    retrieved = get_disease_by_id(conn, "UMLS:C0006142")
    if retrieved:
        print(f"  Found: {retrieved.name}")
        print(f"  Synonyms: {retrieved.synonyms}")
        print(f"  ICD-10: {retrieved.icd10_codes}")
    print()

    # Retrieve all
    print("3. Retrieving all diseases...")
    all_diseases = get_all_diseases(conn)
    for d in all_diseases:
        print(f"  - {d.name} ({d.category})")
    print()

    # Update
    print("4. Updating disease...")
    retrieved.category = "oncological"
    retrieved.synonyms.append("Breast Neoplasm")
    update_disease(conn, retrieved)

    # Verify update
    updated = get_disease_by_id(conn, "UMLS:C0006142")
    print(f"  Category: {updated.category}")
    print(f"  Synonyms: {updated.synonyms}")
    print()

    # Custom query
    print("5. Custom query (diseases with 'diabetes' in name)...")
    custom_sql = "SELECT * FROM diseases WHERE name LIKE ?"
    rows = conn.execute(custom_sql, ("%Diabetes%",)).fetchall()
    for row in rows:
        disease = Disease.from_db_dict(dict(row), dialect="sqlite")
        print(f"  - {disease.name}")
    print()

    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  ✓ Add SQLMixin to any Pydantic model")
    print("  ✓ Auto-generate CREATE TABLE, INSERT, SELECT, UPDATE")
    print("  ✓ to_db_dict() handles JSON serialization")
    print("  ✓ from_db_dict() reconstructs models from rows")
    print("  ✓ Works with both SQLite and PostgreSQL")
    print("  ✓ Can still write custom SQL when needed")
    print()

    conn.close()


if __name__ == "__main__":
    main()
