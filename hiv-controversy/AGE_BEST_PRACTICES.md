# Apache AGE Best Practices

## Critical: Session Initialization Pattern

**EVERY database cursor/session that uses AGE MUST be initialized with this pattern:**

```python
def init_age_session(cursor):
    """
    EVERY db connection using AGE should use this init function.

    IMPORTANT: This must be called for EVERY cursor/session that uses AGE.
    AGE requires both LOAD and search_path to be set per session.

    Args:
        cursor: PostgreSQL cursor

    Usage:
        with conn.cursor() as cur:
            init_age_session(cur)
            cur.execute(...)
    """
    cursor.execute("LOAD 'age';")
    cursor.execute('SET search_path = ag_catalog, "$user", public;')
```

## Why This Matters

PostgreSQL/AGE requires **per-session** initialization because:

1. **`LOAD 'age'`** - Loads the AGE extension library into the current session
2. **`SET search_path`** - Makes AGE's functions and types available

Without this initialization on EVERY cursor:
- Cypher queries will fail with "function does not exist" errors
- AGE data types (agtype, vertex, edge) won't be recognized
- Graph operations will be unavailable

## Correct Usage Pattern

### ✅ CORRECT - Initialize per cursor

```python
def execute_query(conn, query):
    with conn.cursor() as cursor:
        # CRITICAL: Initialize AGE for THIS cursor
        init_age_session(cursor)

        # Now you can use AGE functions
        cursor.execute(f"SELECT * FROM ag_catalog.cypher('{GRAPH_NAME}', $$ {query} $$) as (result agtype);")
        return cursor.fetchall()
```

### ❌ INCORRECT - Initialize once per connection

```python
# DON'T DO THIS!
def setup_connection(conn):
    cursor = conn.cursor()
    cursor.execute("LOAD 'age';")  # This only affects THIS cursor
    cursor.execute("SET search_path = ag_catalog, '$user', public;")
    cursor.close()  # Session settings are lost!

def execute_query(conn, query):
    cursor = conn.cursor()  # New cursor = new session = no AGE!
    cursor.execute(...)  # WILL FAIL
```

## Implementation in This Project

All query scripts in this project follow the correct pattern:

1. **`pmc_graph_pipeline.py`** - Stage 6 graph loading
2. **`query_api.py`** - REST API endpoints
3. **`query_examples.py`** - Pre-built example queries
4. **`interactive_query.py`** - Interactive CLI

Each of these scripts:
- Defines `init_age_session(cursor)` function
- Uses `with conn.cursor() as cursor:` pattern
- Calls `init_age_session(cursor)` before EVERY Cypher query

## Common Pitfalls

### Pitfall 1: Reusing Cursors

```python
# BAD
cursor = conn.cursor()
init_age_session(cursor)
cursor.execute(query1)  # Works
cursor.execute(query2)  # Still works (same cursor)
cursor.close()

cursor = conn.cursor()  # New cursor, no initialization!
cursor.execute(query3)  # FAILS
```

**Solution:** Use context managers (`with`) and initialize each time:

```python
# GOOD
with conn.cursor() as cursor:
    init_age_session(cursor)
    cursor.execute(query1)

with conn.cursor() as cursor:
    init_age_session(cursor)
    cursor.execute(query2)
```

### Pitfall 2: Connection Pooling

When using connection pools, each checkout from the pool may give you a connection with a fresh session:

```python
# In production with pooling
def execute_with_pool(pool, query):
    with pool.getconn() as conn:
        with conn.cursor() as cursor:
            init_age_session(cursor)  # Always initialize
            cursor.execute(query)
            return cursor.fetchall()
```

### Pitfall 3: Long-Running Connections

Even with a long-running connection, you must initialize each cursor:

```python
# Web server with persistent connection
class QueryService:
    def __init__(self):
        self.conn = psycopg2.connect(...)

    def query(self, cypher):
        with self.conn.cursor() as cursor:
            init_age_session(cursor)  # Every time!
            cursor.execute(f"SELECT * FROM ag_catalog.cypher(...)")
            return cursor.fetchall()
```

## Testing Your Implementation

To verify your code follows this pattern:

1. **Restart your database** to clear any cached sessions
2. **Run a query** - if it works without explicitly calling `init_age_session`, you're doing it wrong
3. **Check for context managers** - every `cursor.execute()` using AGE should be inside a `with` block that calls `init_age_session`

## Performance Considerations

**Q: Doesn't this add overhead to call `init_age_session` every time?**

A: The overhead is minimal (microseconds) compared to:
- Query execution time
- Network latency
- Actual graph traversal

The reliability gained far outweighs the tiny performance cost.

**Q: Can I cache the initialization?**

A: No. PostgreSQL sessions are per-cursor, and there's no reliable way to know if a cursor has already been initialized. Always initialize explicitly.

## Summary

**The Golden Rule of Apache AGE:**

> Every cursor that uses AGE functions or data types must be initialized with `LOAD 'age'` and `SET search_path` before use.

**The Safe Pattern:**

```python
with conn.cursor() as cursor:
    init_age_session(cursor)
    # Now you can use AGE
    cursor.execute(...)
```

Follow this pattern religiously, and your AGE queries will work reliably every time.
