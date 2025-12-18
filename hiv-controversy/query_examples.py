#!/usr/bin/env python3
"""
Example Queries for Medical Literature Knowledge Graph

This script demonstrates various Cypher queries you can run against the
PostgreSQL/AGE knowledge graph.

Usage:
    python query_examples.py [query_name]

Available queries:
    all_claims          - List all claims in the database
    hiv_claims          - Find claims mentioning HIV
    evidence_chains     - Find claims with supporting evidence
    paper_claims        - Show papers and their claims
    entity_mentions     - Find entities and where they're mentioned
    causal_claims       - Find claims about causation
    high_confidence     - Find high-confidence claims
    contradictions      - Find potentially contradictory claims
    paper_network       - Show relationships between papers
    entity_cooccurrence - Find entities that appear together
"""

import argparse
import os
import sys
from typing import Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


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


def init_age_session(cursor: psycopg2.extensions.cursor) -> None:
    """
    EVERY db connection using AGE should use this init function.

    IMPORTANT: This must be called for EVERY cursor/session that uses AGE.
    AGE requires both LOAD and search_path to be set per session.

    Args:
        cursor: PostgreSQL cursor
    """
    cursor.execute("LOAD 'age';")
    cursor.execute('SET search_path = ag_catalog, "$user", public;')


def execute_cypher(conn: psycopg2.extensions.connection, query: str) -> list:
    """Execute a Cypher query using AGE."""
    with conn.cursor() as cursor:
        # CRITICAL: Initialize AGE for this session
        init_age_session(cursor)

        sql = f"SELECT * FROM ag_catalog.cypher('{GRAPH_NAME}', $$ {query} $$) as (result agtype);"

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error executing query: {e}")
            print(f"Query: {query}")
            return []


def format_result(result: Any) -> str:
    """Format AGE result for display."""
    # AGE returns results as agtype, which is a string representation
    # We'll just convert to string for now
    return str(result)


# ============================================================================
# Example Queries
# ============================================================================


def query_all_claims(conn: psycopg2.extensions.connection) -> None:
    """List all claims in the database."""
    print("\n" + "=" * 80)
    print("ALL CLAIMS IN DATABASE")
    print("=" * 80 + "\n")

    query = """
    MATCH (c:Claim)
    RETURN c.claim_id, c.predicate, c.confidence, c.text
    ORDER BY c.confidence DESC
    LIMIT 20
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No claims found.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")
        print()


def query_hiv_claims(conn: psycopg2.extensions.connection) -> None:
    """Find claims mentioning HIV."""
    print("\n" + "=" * 80)
    print("CLAIMS MENTIONING HIV")
    print("=" * 80 + "\n")

    query = """
    MATCH (c:Claim)
    WHERE c.text =~ '.*[Hh][Ii][Vv].*'
    RETURN c.predicate, c.confidence, c.text, c.evidence_type
    ORDER BY c.confidence DESC
    LIMIT 10
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No HIV-related claims found.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")
        print()


def query_evidence_chains(conn: psycopg2.extensions.connection) -> None:
    """Find claims with supporting evidence."""
    print("\n" + "=" * 80)
    print("CLAIMS WITH SUPPORTING EVIDENCE")
    print("=" * 80 + "\n")

    query = """
    MATCH (e:Evidence)-[:SUPPORTS]->(c:Claim)
    RETURN c.predicate, c.text, e.type, e.strength, e.supports
    ORDER BY e.strength DESC
    LIMIT 10
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No evidence chains found.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")
        print()


def query_paper_claims(conn: psycopg2.extensions.connection) -> None:
    """Show papers and their claims."""
    print("\n" + "=" * 80)
    print("PAPERS AND THEIR CLAIMS")
    print("=" * 80 + "\n")

    query = """
    MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim)
    RETURN p.paper_id, p.title, c.predicate, c.confidence
    ORDER BY p.paper_id, c.confidence DESC
    LIMIT 15
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No paper-claim relationships found.")
        return

    for row in results:
        result_str = format_result(row[0])
        # Try to parse paper_id from the result
        print(f"  {result_str}")


def query_entity_mentions(conn: psycopg2.extensions.connection) -> None:
    """Find entities and where they're mentioned."""
    print("\n" + "=" * 80)
    print("ENTITY MENTIONS")
    print("=" * 80 + "\n")

    query = """
    MATCH (e:Entity)
    RETURN e.entity_id, e.name, e.type
    ORDER BY e.name
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No entities found.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")


def query_causal_claims(conn: psycopg2.extensions.connection) -> None:
    """Find claims about causation."""
    print("\n" + "=" * 80)
    print("CAUSAL CLAIMS")
    print("=" * 80 + "\n")

    query = """
    MATCH (c:Claim)
    WHERE c.predicate IN ['CAUSES', 'PREVENTS', 'INHIBITS', 'TREATS']
    RETURN c.predicate, c.confidence, c.text, c.evidence_type
    ORDER BY c.confidence DESC
    LIMIT 10
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No causal claims found.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")
        print()


def query_high_confidence(conn: psycopg2.extensions.connection) -> None:
    """Find high-confidence claims (confidence >= 0.8)."""
    print("\n" + "=" * 80)
    print("HIGH CONFIDENCE CLAIMS")
    print("=" * 80 + "\n")

    query = """
    MATCH (c:Claim)
    WHERE c.confidence >= 0.8
    RETURN c.predicate, c.confidence, c.text, c.evidence_type
    ORDER BY c.confidence DESC
    LIMIT 10
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No high-confidence claims found.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")
        print()


def query_contradictions(conn: psycopg2.extensions.connection) -> None:
    """Find potentially contradictory claims (same predicate, different papers)."""
    print("\n" + "=" * 80)
    print("POTENTIALLY CONTRADICTORY CLAIMS")
    print("=" * 80 + "\n")

    query = """
    MATCH (p1:Paper)-[:MAKES_CLAIM]->(c1:Claim),
          (p2:Paper)-[:MAKES_CLAIM]->(c2:Claim)
    WHERE p1.paper_id < p2.paper_id
      AND c1.predicate = c2.predicate
      AND c1.claim_id <> c2.claim_id
    RETURN p1.paper_id, p2.paper_id, c1.predicate, c1.text, c2.text
    LIMIT 5
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No contradictions found (or papers need more analysis).")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")
        print()


def query_paper_network(conn: psycopg2.extensions.connection) -> None:
    """Show relationships between papers through shared entities."""
    print("\n" + "=" * 80)
    print("PAPER NETWORK (Papers connected through entities)")
    print("=" * 80 + "\n")

    query = """
    MATCH (p:Paper)-[:MAKES_CLAIM]->(c:Claim)-[:HAS_SUBJECT]->(e:Entity)
    RETURN p.paper_id, p.title, e.name, e.type
    LIMIT 10
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No entity connections found between papers.")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")


def query_entity_cooccurrence(conn: psycopg2.extensions.connection) -> None:
    """Find entities that appear together in claims."""
    print("\n" + "=" * 80)
    print("ENTITY CO-OCCURRENCE IN CLAIMS")
    print("=" * 80 + "\n")

    query = """
    MATCH (c:Claim)-[:HAS_SUBJECT]->(e1:Entity),
          (c:Claim)-[:HAS_OBJECT]->(e2:Entity)
    WHERE e1.entity_id < e2.entity_id
    RETURN e1.name, e2.name, c.predicate, count(*) as frequency
    ORDER BY frequency DESC
    LIMIT 10
    """

    results = execute_cypher(conn, query)

    if not results:
        print("No entity co-occurrences found (entity linking may need improvement).")
        return

    for i, row in enumerate(results, 1):
        print(f"{i}. {format_result(row[0])}")


def query_graph_stats(conn: psycopg2.extensions.connection) -> None:
    """Show overall graph statistics."""
    print("\n" + "=" * 80)
    print("GRAPH STATISTICS")
    print("=" * 80 + "\n")

    node_types = ["Paper", "Entity", "Paragraph", "Claim", "Evidence"]

    for node_type in node_types:
        query = f"MATCH (n:{node_type}) RETURN count(n)"
        results = execute_cypher(conn, query)
        if results:
            count = format_result(results[0][0])
            print(f"{node_type} nodes: {count}")

    query = "MATCH ()-[r]->() RETURN count(r)"
    results = execute_cypher(conn, query)
    if results:
        count = format_result(results[0][0])
        print(f"\nTotal edges: {count}")

    # Show edge type distribution
    edge_types = ["CONTAINS", "MAKES_CLAIM", "CONTAINS_CLAIM", "SUPPORTS", "HAS_SUBJECT", "HAS_OBJECT"]
    print("\nEdge types:")
    for edge_type in edge_types:
        query = f"MATCH ()-[r:{edge_type}]->() RETURN count(r)"
        results = execute_cypher(conn, query)
        if results:
            count = format_result(results[0][0])
            print(f"  {edge_type}: {count}")


# ============================================================================
# Main
# ============================================================================


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Query the medical literature knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available queries:
  all_claims          - List all claims in the database
  hiv_claims          - Find claims mentioning HIV
  evidence_chains     - Find claims with supporting evidence
  paper_claims        - Show papers and their claims
  entity_mentions     - Find entities and where they're mentioned
  causal_claims       - Find claims about causation
  high_confidence     - Find high-confidence claims
  contradictions      - Find potentially contradictory claims
  paper_network       - Show relationships between papers
  entity_cooccurrence - Find entities that appear together
  stats               - Show graph statistics

Examples:
  python query_examples.py hiv_claims
  python query_examples.py evidence_chains
  python query_examples.py stats
        """,
    )

    parser.add_argument("query", nargs="?", default="stats", help="Query to run (default: stats)")

    args = parser.parse_args()

    # Map query names to functions
    queries = {
        "all_claims": query_all_claims,
        "hiv_claims": query_hiv_claims,
        "evidence_chains": query_evidence_chains,
        "paper_claims": query_paper_claims,
        "entity_mentions": query_entity_mentions,
        "causal_claims": query_causal_claims,
        "high_confidence": query_high_confidence,
        "contradictions": query_contradictions,
        "paper_network": query_paper_network,
        "entity_cooccurrence": query_entity_cooccurrence,
        "stats": query_graph_stats,
    }

    if args.query not in queries:
        print(f"Error: Unknown query '{args.query}'")
        print(f"Available queries: {', '.join(queries.keys())}")
        return 1

    # Connect to database
    print(f"Connecting to PostgreSQL/AGE at {AGE_HOST}:{AGE_PORT}...")
    conn = get_age_connection()

    # Run the query (AGE session initialized per query)
    query_func = queries[args.query]
    query_func(conn)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
