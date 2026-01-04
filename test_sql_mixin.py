"""
Test suite for SQL Mixin

Demonstrates SQL generation from Pydantic models for both PostgreSQL and SQLite.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

# Add schema to path
sys.path.insert(0, str(Path(__file__).parent / "schema"))

from sql_mixin import SQLMixin

# ============================================================================
# Example Models
# ============================================================================


class Disease(BaseModel, SQLMixin):
    """Example disease model"""

    id: str
    name: str
    synonyms: list[str]
    umls_id: Optional[str] = None
    icd10_codes: list[str] = []
    category: Optional[str] = None
    created_at: datetime = datetime.utcnow()


class Author(BaseModel, SQLMixin):
    """Example author model with nested data"""

    orcid: str
    name: str
    affiliations: list[str] = []
    h_index: Optional[int] = None


class Paper(BaseModel, SQLMixin):
    """Example paper model with nested Author"""

    paper_id: str
    title: str
    authors: list[Author] = []  # Nested Pydantic models
    metadata: dict = {}
    publication_date: Optional[datetime] = None


# ============================================================================
# Tests
# ============================================================================


def test_create_table_postgresql():
    """Test CREATE TABLE generation for PostgreSQL"""
    print("=" * 70)
    print("CREATE TABLE - PostgreSQL")
    print("=" * 70)

    sql = Disease.create_table_sql(dialect="postgresql")
    print(sql)
    print()

    # Verify key elements
    assert "CREATE TABLE" in sql
    assert "diseases" in sql  # Pluralized table name
    assert "id TEXT NOT NULL PRIMARY KEY" in sql
    assert "synonyms TEXT[]" in sql  # PostgreSQL array
    assert "umls_id TEXT" in sql  # Nullable (no NOT NULL)


def test_create_table_sqlite():
    """Test CREATE TABLE generation for SQLite"""
    print("=" * 70)
    print("CREATE TABLE - SQLite")
    print("=" * 70)

    sql = Disease.create_table_sql(dialect="sqlite")
    print(sql)
    print()

    # Verify key elements
    assert "CREATE TABLE" in sql
    assert "synonyms TEXT" in sql  # SQLite uses TEXT for arrays


def test_insert_sql():
    """Test INSERT statement generation"""
    print("=" * 70)
    print("INSERT Statement")
    print("=" * 70)

    # PostgreSQL
    pg_sql, pg_params = Disease.insert_sql(dialect="postgresql")
    print("PostgreSQL:")
    print(f"  SQL: {pg_sql}")
    print(f"  Params: {pg_params}")
    print()

    # SQLite
    sqlite_sql, sqlite_params = Disease.insert_sql(dialect="sqlite")
    print("SQLite:")
    print(f"  SQL: {sqlite_sql}")
    print(f"  Params: {sqlite_params}")
    print()

    assert "$1" in pg_sql  # PostgreSQL placeholders
    assert "?" in sqlite_sql  # SQLite placeholders


def test_select_sql():
    """Test SELECT statement generation"""
    print("=" * 70)
    print("SELECT Statement")
    print("=" * 70)

    # Basic select
    sql1 = Disease.select_sql()
    print(f"All: {sql1}")

    # With WHERE clause
    sql2 = Disease.select_sql(where="umls_id = $1")
    print(f"Filtered: {sql2}")

    # Specific columns
    sql3 = Disease.select_sql(columns=["id", "name", "umls_id"])
    print(f"Columns: {sql3}")
    print()


def test_update_sql():
    """Test UPDATE statement generation"""
    print("=" * 70)
    print("UPDATE Statement")
    print("=" * 70)

    # PostgreSQL
    pg_sql, pg_params = Disease.update_sql(where="id = $1", dialect="postgresql")
    print("PostgreSQL:")
    print(f"  SQL: {pg_sql}")
    print(f"  Params: {pg_params}")
    print()

    # SQLite
    sqlite_sql, sqlite_params = Disease.update_sql(where="id = ?", dialect="sqlite")
    print("SQLite:")
    print(f"  SQL: {sqlite_sql}")
    print(f"  Params: {sqlite_params}")
    print()


def test_to_db_dict():
    """Test conversion to database dictionary"""
    print("=" * 70)
    print("Model → Database Dictionary")
    print("=" * 70)

    disease = Disease(id="C0006142", name="Breast Cancer", synonyms=["Breast Carcinoma", "Mammary Cancer"], umls_id="C0006142", icd10_codes=["C50.9"], category="genetic")

    # PostgreSQL (keeps lists as lists)
    pg_dict = disease.to_db_dict(dialect="postgresql")
    print("PostgreSQL dict:")
    for key, value in pg_dict.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    print()

    # SQLite (converts lists to JSON strings)
    sqlite_dict = disease.to_db_dict(dialect="sqlite")
    print("SQLite dict:")
    for key, value in sqlite_dict.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    print()

    # Verify JSON serialization for SQLite
    assert isinstance(sqlite_dict["synonyms"], str)  # JSON string
    assert '"Breast Carcinoma"' in sqlite_dict["synonyms"]


def test_nested_models():
    """Test handling of nested Pydantic models"""
    print("=" * 70)
    print("Nested Models (Paper with Authors)")
    print("=" * 70)

    # Create paper with nested authors
    paper = Paper(
        paper_id="PMC123",
        title="Test Paper",
        authors=[Author(orcid="0000-0001", name="Jane Doe", affiliations=["MIT"]), Author(orcid="0000-0002", name="John Smith", affiliations=["Harvard", "MGH"])],
        metadata={"study_type": "rct", "sample_size": 100},
    )

    # Generate CREATE TABLE
    create_sql = Paper.create_table_sql(dialect="postgresql")
    print("CREATE TABLE:")
    print(create_sql)
    print()

    # Convert to database dict
    db_dict = paper.to_db_dict(dialect="postgresql")
    print("Database dict:")
    for key, value in db_dict.items():
        if key == "authors":
            print(f"  {key}: {value[:100]}... (nested models as JSON)")
        else:
            print(f"  {key}: {value}")
    print()

    # Verify authors are serialized to JSON-compatible format
    assert isinstance(db_dict["authors"], list)
    assert isinstance(db_dict["authors"][0], dict)
    assert db_dict["authors"][0]["name"] == "Jane Doe"


def test_from_db_dict():
    """Test reconstruction from database dictionary"""
    print("=" * 70)
    print("Database Dictionary → Model")
    print("=" * 70)

    # Simulate SQLite row data (with JSON strings)
    sqlite_row = {
        "id": "C0006142",
        "name": "Breast Cancer",
        "synonyms": '["Breast Carcinoma", "Mammary Cancer"]',  # JSON string
        "umls_id": "C0006142",
        "icd10_codes": '["C50.9"]',  # JSON string
        "category": "genetic",
        "created_at": "2024-01-01T00:00:00",
    }

    # Reconstruct model
    disease = Disease.from_db_dict(sqlite_row, dialect="sqlite")

    print(f"Reconstructed Disease:")
    print(f"  ID: {disease.id}")
    print(f"  Name: {disease.name}")
    print(f"  Synonyms: {disease.synonyms}")
    print(f"  ICD-10: {disease.icd10_codes}")
    print()

    # Verify lists were parsed correctly
    assert isinstance(disease.synonyms, list)
    assert len(disease.synonyms) == 2
    assert "Breast Carcinoma" in disease.synonyms


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "SQL Mixin Test Suite" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    test_create_table_postgresql()
    test_create_table_sqlite()
    test_insert_sql()
    test_select_sql()
    test_update_sql()
    test_to_db_dict()
    test_nested_models()
    test_from_db_dict()

    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("The SQL Mixin successfully:")
    print("  ✓ Generates CREATE TABLE for PostgreSQL and SQLite")
    print("  ✓ Generates INSERT/SELECT/UPDATE statements")
    print("  ✓ Handles arrays (PostgreSQL ARRAY vs SQLite JSON)")
    print("  ✓ Serializes nested Pydantic models to JSON")
    print("  ✓ Converts to/from database dictionaries")
    print()


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
