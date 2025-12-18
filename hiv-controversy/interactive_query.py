#!/usr/bin/env python3
"""
Interactive Query Tool for Medical Literature Knowledge Graph

This script provides an interactive REPL for querying the PostgreSQL/AGE
knowledge graph using Cypher queries.

Usage:
    python interactive_query.py

Commands:
    /help       - Show help message
    /examples   - Show example queries
    /stats      - Show graph statistics
    /clear      - Clear screen
    /quit       - Exit

Or enter any Cypher query directly.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Any, Optional
import json


# ============================================================================
# Configuration
# ============================================================================

AGE_HOST = os.getenv("AGE_HOST", "localhost")
AGE_PORT = int(os.getenv("AGE_PORT", "5432"))
AGE_DB = os.getenv("AGE_DB", "age")
AGE_USER = os.getenv("AGE_USER", "age")
AGE_PASSWORD = os.getenv("AGE_PASSWORD", "agepassword")
GRAPH_NAME = "medical_literature_graph"


# ============================================================================
# Connection Functions
# ============================================================================


def get_age_connection() -> psycopg2.extensions.connection:
    """Create connection to PostgreSQL/AGE database."""
    conn = psycopg2.connect(host=AGE_HOST, port=AGE_PORT, database=AGE_DB, user=AGE_USER, password=AGE_PASSWORD)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def init_age_session(cursor: Any) -> None:
    """
    EVERY db connection using AGE should use this init function.

    IMPORTANT: This must be called for EVERY cursor/session that uses AGE.
    AGE requires both LOAD and search_path to be set per session.

    Args:
        cursor: PostgreSQL cursor
    """
    cursor.execute("LOAD 'age';")
    cursor.execute('SET search_path = ag_catalog, "$user", public;')


def execute_cypher(conn: psycopg2.extensions.connection, query: str) -> tuple[list, Optional[str]]:
    """
    Execute a Cypher query using AGE.

    Returns:
        Tuple of (results, error_message)
    """
    with conn.cursor() as cursor:
        # CRITICAL: Initialize AGE for this session
        init_age_session(cursor)

        sql = f"SELECT * FROM ag_catalog.cypher('{GRAPH_NAME}', $$ {query} $$) as (result agtype);"

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            return results, None
        except Exception as e:
            return [], str(e)


def parse_agtype(value: str) -> Any:
    """
    Parse AGE's agtype format to Python objects.

    AGE returns results in a JSON-like format that we need to parse.
    """
    try:
        # Remove the ::vertex or ::edge annotations
        value = str(value)
        if "::" in value:
            value = value.split("::")[0]

        # Try to parse as JSON
        return json.loads(value)
    except Exception:
        # If parsing fails, return as string
        return value


def format_results(results: list, max_width: int = 100) -> str:
    """Format query results for display."""
    if not results:
        return "No results found."

    output = []
    for i, row in enumerate(results, 1):
        output.append(f"\n{'=' * max_width}")
        output.append(f"Result {i}")
        output.append("=" * max_width)

        for j, value in enumerate(row):
            parsed = parse_agtype(value)

            if isinstance(parsed, dict):
                # Pretty print dictionaries
                output.append(json.dumps(parsed, indent=2))
            elif isinstance(parsed, list):
                # Pretty print lists
                output.append(json.dumps(parsed, indent=2))
            else:
                # Simple value
                output.append(str(parsed))

        output.append("")

    return "\n".join(output)


# ============================================================================
# Commands
# ============================================================================


def show_help() -> None:
    """Show help message."""
    help_text = """
╔════════════════════════════════════════════════════════════════════════════╗
║           INTERACTIVE QUERY TOOL FOR MEDICAL LITERATURE GRAPH              ║
╚════════════════════════════════════════════════════════════════════════════╝

COMMANDS:
  /help       - Show this help message
  /examples   - Show example Cypher queries
  /stats      - Show graph statistics
  /clear      - Clear screen
  /quit       - Exit the tool

QUERY SYNTAX:
  Enter any Cypher query directly at the prompt. Queries are executed against
  the '{graph}' graph in PostgreSQL/AGE.

EXAMPLES:
  # Find all papers
  MATCH (p:Paper) RETURN p LIMIT 5

  # Find claims about HIV
  MATCH (c:Claim) WHERE c.text =~ '.*HIV.*' RETURN c

  # Find papers and their claims
  MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim) RETURN p.title, c.predicate LIMIT 10

TIPS:
  - Use LIMIT to restrict large result sets
  - Use WHERE clauses to filter results
  - Use RETURN to specify what to display
  - Press Ctrl+C to cancel a long-running query
  - Command history is available with arrow keys
    """.format(
        graph=GRAPH_NAME
    )
    print(help_text)


def show_examples() -> None:
    """Show example queries."""
    examples = """
╔════════════════════════════════════════════════════════════════════════════╗
║                          EXAMPLE CYPHER QUERIES                            ║
╚════════════════════════════════════════════════════════════════════════════╝

1. List all papers:
   MATCH (p:Paper) RETURN p.paper_id, p.title LIMIT 10

2. Find claims mentioning HIV:
   MATCH (c:Claim) WHERE c.text =~ '.*[Hh][Ii][Vv].*' RETURN c.predicate, c.text LIMIT 10

3. Find claims with evidence:
   MATCH (e:Evidence)-[:SUPPORTS]->(c:Claim) RETURN e.type, e.strength, c.text LIMIT 10

4. Find papers making causal claims:
   MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim)
   WHERE c.predicate IN ['CAUSES', 'PREVENTS']
   RETURN p.title, c.predicate, c.text LIMIT 10

5. Find high-confidence claims:
   MATCH (c:Claim) WHERE c.confidence >= 0.8 RETURN c.predicate, c.confidence, c.text LIMIT 10

6. Find all entities:
   MATCH (e:Entity) RETURN e.entity_id, e.name, e.type

7. Find claims about specific entities:
   MATCH (c:Claim)-[:HAS_SUBJECT]->(e:Entity)
   WHERE e.name = 'HIV'
   RETURN c.predicate, c.text LIMIT 10

8. Count claims by predicate:
   MATCH (c:Claim) RETURN c.predicate, count(*) as count ORDER BY count DESC

9. Find papers containing specific paragraphs:
   MATCH (p:Paper)-[:CONTAINS]->(para:Paragraph)
   WHERE para.text =~ '.*AIDS.*'
   RETURN p.title, para.text LIMIT 5

10. Find evidence strength distribution:
    MATCH (e:Evidence) RETURN e.strength, count(*) as count

    """
    print(examples)


def show_stats(conn: psycopg2.extensions.connection) -> None:
    """Show graph statistics."""
    print("\n" + "=" * 80)
    print("GRAPH STATISTICS")
    print("=" * 80 + "\n")

    # Count nodes
    node_types = ["Paper", "Entity", "Paragraph", "Claim", "Evidence"]
    for node_type in node_types:
        query = f"MATCH (n:{node_type}) RETURN count(n)"
        results, error = execute_cypher(conn, query)
        if error:
            print(f"Error counting {node_type}: {error}")
        elif results:
            count = parse_agtype(results[0][0])
            print(f"{node_type:12} nodes: {count}")

    # Count edges
    query = "MATCH ()-[r]->() RETURN count(r)"
    results, error = execute_cypher(conn, query)
    if not error and results:
        count = parse_agtype(results[0][0])
        print(f"\nTotal edges: {count}")

    # Edge type distribution
    edge_types = ["CONTAINS", "MAKES_CLAIM", "CONTAINS_CLAIM", "SUPPORTS", "HAS_SUBJECT", "HAS_OBJECT"]
    print("\nEdge type distribution:")
    for edge_type in edge_types:
        query = f"MATCH ()-[r:{edge_type}]->() RETURN count(r)"
        results, error = execute_cypher(conn, query)
        if not error and results:
            count = parse_agtype(results[0][0])
            if count > 0:
                print(f"  {edge_type:20} {count}")

    print()


# ============================================================================
# Main REPL
# ============================================================================


def main():
    """Main REPL loop."""
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║           INTERACTIVE QUERY TOOL FOR MEDICAL LITERATURE GRAPH              ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Connecting to PostgreSQL/AGE at {AGE_HOST}:{AGE_PORT}...")

    try:
        conn = get_age_connection()
        print("Connected successfully!")
        print("AGE session will be initialized for each query")
        print()
        print("Type /help for help, /quit to exit")
        print()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1

    # REPL loop
    while True:
        try:
            # Get user input
            query = input("cypher> ").strip()

            if not query:
                continue

            # Handle commands
            if query.startswith("/"):
                cmd = query.lower()

                if cmd == "/quit" or cmd == "/exit" or cmd == "/q":
                    print("Goodbye!")
                    break
                elif cmd == "/help" or cmd == "/h":
                    show_help()
                elif cmd == "/examples" or cmd == "/ex":
                    show_examples()
                elif cmd == "/stats" or cmd == "/s":
                    show_stats(conn)
                elif cmd == "/clear" or cmd == "/cls":
                    os.system("clear" if os.name != "nt" else "cls")
                else:
                    print(f"Unknown command: {query}")
                    print("Type /help for available commands")

                continue

            # Execute Cypher query
            results, error = execute_cypher(conn, query)

            if error:
                print(f"\n❌ Error: {error}\n")
            else:
                if not results:
                    print("\nNo results found.\n")
                else:
                    print(f"\nFound {len(results)} result(s):")
                    print(format_results(results))

        except KeyboardInterrupt:
            print("\n\nQuery interrupted. Type /quit to exit.\n")
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
