#!/usr/bin/env python3
"""
Utility to initialize the Medical Knowledge Graph PostgreSQL database.
"""
import os
from pathlib import Path

import psycopg2


def init_db():
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medgraph")
    schema_file = Path(__file__).parent.parent / "schema" / "migration.sql"

    if not schema_file.exists():
        print(f"Error: Schema file not found at {schema_file}")
        return

    print(f"Connecting to database: {database_url}")
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                print(f"Executing migration script: {schema_file.name}")
                cur.execute(schema_file.read_text())
            conn.commit()
        print("Database initialization completed successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")


if __name__ == "__main__":
    init_db()
