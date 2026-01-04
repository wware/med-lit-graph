# Next Step: Temporary PostgreSQL Database for Testing

To ensure idempotent and isolated tests, we will create a temporary PostgreSQL database for each test session. This approach avoids the complexities of mocking the database or using a shared, stateful database, and it is a robust strategy for integration testing.

I tried doing this using a SQLite `:memory:` database and there were issues with getting it to work, so trying now with PostgreSQL, which hews closer to future plans anyway so that's good. Where there may be existing SQLite code elsewhere, we might want to get rid of it, but that can wait.

For right now, here's the plan:

## 1. `pytest` Fixture for Database Management

A `pytest` fixture with session scope will be created in `tests/conftest.py`. This fixture will be responsible for:

*   **Creating a unique database name:** A unique name for the test database will be generated for each test session, for example, by using a timestamp or a UUID. This ensures that parallel test runs do not interfere with each other.
*   **Creating the test database:** The fixture will connect to the default `postgres` database and issue a `CREATE DATABASE` command to create the new test database.
*   **Initializing the schema:** Once the database is created, the fixture will connect to it and apply the schema from `schema/migration.sql`. This will also include enabling the `pgvector` extension.
*   **Yielding the database URL:** The fixture will yield the connection string for the newly created database to the tests.
*   **Cleaning up the database:** After the test session is complete, the fixture will drop the temporary database using `DROP DATABASE`.

Here is a sketch of what the fixture would look like in `tests/conftest.py`:

```python
import os
import uuid
import pytest
import psycopg2
from ingestion.init_db import init_db

@pytest.fixture(scope="session")
def temporary_db():
    """
    Creates a temporary PostgreSQL database for a test session.
    """
    db_name = f"test_{uuid.uuid4().hex}"
    base_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    test_db_url = base_url.replace("/postgres", f"/{db_name}")

    # Create the test database
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE {db_name}")
    conn.close()

    # Initialize the schema
    init_db(test_db_url)

    yield test_db_url

    # Drop the test database
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE {db_name}")
    conn.close()
```

## 2. Using the Fixture in Tests

The tests in `tests/test_postgresql_integration.py` will be updated to use the `temporary_db` fixture. The `SQLQueryExecutor` will be instantiated with the URL provided by the fixture.

Example:

```python
def test_sql_query_executor(temporary_db):
    """Tests the SQLQueryExecutor directly against the test database."""
    executor = SQLQueryExecutor(temporary_db)
    # ... rest of the test
```

This approach will provide a clean, isolated database for each test session, ensuring that tests are reproducible and independent of each other.
