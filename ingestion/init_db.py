#!/usr/bin/env python3
"""
Utility to initialize the Medical Knowledge Graph PostgreSQL database.
"""

import os

from med_lit_schema.setup_database import setup_database


def init_db():
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medgraph")
    print(f"Setting up database: {database_url}")
    try:
        setup_database(database_url, skip_vector_index=False)
        print("Database initialization completed successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")


if __name__ == "__main__":
    init_db()
