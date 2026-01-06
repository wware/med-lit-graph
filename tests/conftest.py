"""Pytest fixtures: lightweight mock HTTP server that speaks the client's API.

This fixture starts a tiny HTTP server on localhost in a background thread and
exposes an endpoint POST /api/v1/query that returns plausible JSON results for
the MedicalGraphClient in client/python/client.py.

Usage in tests:
    def test_something(mock_med_graph_server, http_medical_graph_client):
        # http_medical_graph_client is pointed at the running mock server
        res = http_medical_graph_client.find_treatments("breast cancer", min_confidence=0.5, limit=3)
        assert isinstance(res, dict)
        assert "results" in res
"""

from __future__ import annotations

import json
import logging
import multiprocessing
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Generator, Tuple
from urllib.parse import urlparse

import psycopg2
import pytest

# Import the real client class from the repo so tests exercise it directly.
from client.python.client import MedicalGraphClient

# A small in-memory graph fixture representing a plausible med-lit knowledge graph.
# Node representation:
#   { "id": "<str>", "type": "Paper" | "Author" | "Venue" | "Concept", "props": { ... } }
# Edge representation:
#   { "source": "<node_id>", "target": "<node_id>", "type": "AUTHORED_BY" | "CITES" | "PUBLISHED_IN" }
#
# Adapt to the repository's actual node/edge shape if needed.


@pytest.fixture
def small_graph():
    nodes = [
        {"id": "paper:001", "type": "Paper", "props": {"title": "Graph methods in medlit", "year": 2020, "doi": "10.1000/xyz001"}},
        {"id": "paper:002", "type": "Paper", "props": {"title": "Applications of knowledge graphs", "year": 2021, "doi": "10.1000/xyz002"}},
        {"id": "paper:003", "type": "Paper", "props": {"title": "Survey of entity linking", "year": 2019, "doi": "10.1000/xyz003"}},
        {"id": "author:alice", "type": "Author", "props": {"name": "Alice Smith", "orcid": "0000-0001"}},
        {"id": "author:bob", "type": "Author", "props": {"name": "Bob Jones", "orcid": "0000-0002"}},
        {"id": "venue:confA", "type": "Venue", "props": {"name": "Conf A", "issn": "1234-5678"}},
        {"id": "concept:kg", "type": "Concept", "props": {"label": "Knowledge Graph"}},
    ]

    edges = [
        {"source": "paper:001", "target": "author:alice", "type": "AUTHORED_BY"},
        {"source": "paper:002", "target": "author:bob", "type": "AUTHORED_BY"},
        {"source": "paper:003", "target": "author:alice", "type": "AUTHORED_BY"},
        {"source": "paper:002", "target": "paper:001", "type": "CITES"},
        {"source": "paper:003", "target": "paper:001", "type": "CITES"},
        {"source": "paper:001", "target": "venue:confA", "type": "PUBLISHED_IN"},
        {"source": "paper:002", "target": "concept:kg", "type": "MENTIONS"},
    ]

    # Return a mutable object that tests can pass to query executors.
    return {"nodes": nodes, "edges": edges}


@pytest.fixture
def example_queries():
    # Example JSON-query language snippets. Adapt keys to match your JSON query language.
    # These are intentionally generic and cover basic operations: filter, traverse, aggregate.
    return {
        "select_papers_2020": {"select": {"type": "Paper", "fields": ["id", "title", "year"]}, "where": {"props.year": {"$eq": 2020}}, "limit": 10},
        "authors_of_paper_001": {"select": {"from": {"type": "Paper", "id": "paper:001"}, "expand": [{"edge": "AUTHORED_BY", "direction": "out"}], "fields": ["id", "props.name"]}},
        "citation_traversal_depth_1": {"select": {"from": {"type": "Paper", "id": "paper:002"}, "traverse": {"edge": "CITES", "direction": "out", "depth": 1}, "fields": ["id", "props.title"]}},
        "invalid_query_missing_select": {"where": {"props.year": {"$eq": 2020}}},
    }


# Simple entities used across tests
@pytest.fixture
def small_entities():
    # Minimal Disease/Gene/Drug-like dicts used to construct pydantic models
    return {
        "disease": {
            "entity_id": "C0006142",
            "name": "Breast Cancer",
            "synonyms": ["Breast Carcinoma"],
            "abbreviations": ["BC"],
            "source": "umls",
        },
        "gene": {
            "entity_id": "HGNC:1100",
            "name": "BRCA1",
            "synonyms": ["BRCA1 gene"],
            "abbreviations": ["BRCA1"],
            "source": "hgnc",
        },
        "drug": {
            "entity_id": "RxNorm:1187832",
            "name": "Olaparib",
            "synonyms": ["AZD2281"],
            "abbreviations": ["Ola"],
            "source": "rxnorm",
        },
    }


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTPServer with thread-per-request handling."""

    daemon_threads = True
    allow_reuse_address = True


class _MockHandler(BaseHTTPRequestHandler):
    # Silence logging from BaseHTTPRequestHandler
    def log_message(self, format, *args):
        return

    def _send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        # Only support the query endpoint
        parsed = urlparse(self.path)
        if parsed.path != "/api/v1/query":
            self._send_json({"error": "not found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}

        # Heuristic responses to make the client tests useful.
        # Recognize a few shapes:
        #  - GraphQuery-like dicts with "find": "nodes"/"edges"/"paths"
        #  - Raw query dicts with "find": "nodes"/etc.
        #  - Otherwise return a default "search" result.

        find = payload.get("find") or payload.get("query")  # query may be a string in some calls

        # Simple mapping for typical queries used by the client helper methods:
        # - find_treatments -> GraphQuery built by QueryBuilder: find='nodes', node_pattern.node_type=... or aggregate -> return aggregated structure
        # We keep the mock small but plausible.
        if isinstance(find, str) and find == "nodes":
            # Return two sample papers / nodes
            results = [
                {
                    "pmc_id": "PMC0001",
                    "title": "Mock study: Drug X treats Breast Cancer (small RCT)",
                    "section": "results",
                    "score": 0.95,
                    "chunk_text": "We found that Drug X reduced tumor size significantly...",
                },
                {
                    "pmc_id": "PMC0002",
                    "title": "Observational evidence for Drug X in breast cancer",
                    "section": "discussion",
                    "score": 0.82,
                    "chunk_text": "Cohort study showing association between Drug X and improved outcomes...",
                },
            ]
            self._send_json({"results": results})
            return

        if isinstance(find, str) and find == "paths":
            results = [
                {
                    "path": [
                        {"node_type": "drug", "name": payload.get("path_pattern", {}).get("start", {}).get("name", "Drug X")},
                        {"edge": "binds_to"},
                        {"node_type": "protein", "name": "Protein Y"},
                    ],
                    "score": 0.9,
                    "evidence": [{"paper_id": "PMC0003", "confidence": 0.88}],
                }
            ]
            self._send_json({"results": results})
            return

        # If the client sends a natural-language 'query' string (MCP-style), respond with search-like documents
        if isinstance(payload.get("query"), str):
            q = payload["query"].lower()
            results = []
            if "brca1" in q or "breast" in q:
                results.append(
                    {
                        "pmc_id": "PMC_BREAST_01",
                        "title": "BRCA1 and response to Drug X",
                        "section": "results",
                        "score": 0.93,
                        "chunk_text": "In BRCA1-mutated patients, Drug X showed improved progression-free survival...",
                    }
                )
            else:
                results.append(
                    {
                        "pmc_id": "PMC_MISC_01",
                        "title": "General literature match",
                        "section": "introduction",
                        "score": 0.6,
                        "chunk_text": "This paper discusses related mechanisms...",
                    }
                )
            self._send_json({"results": results})
            return

        # Default fallback: minimal empty-result structure
        self._send_json({"results": []})

    def do_GET(self):
        # Provide a trivial health endpoint
        if self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, status=404)


def _find_free_port() -> int:
    """Ask the OS for a free port and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        addr, port = s.getsockname()
        return port


@pytest.fixture(scope="session")
def mock_med_graph_server() -> Generator[Tuple[str, int], None, None]:
    """Start a mock HTTP server and yield the base URL and port.

    The server will be shut down after the tests in the session complete.
    """
    port = _find_free_port()
    server = _ThreadedHTTPServer(("127.0.0.1", port), _MockHandler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    # Basic sanity check: don't block if server isn't ready; just yield.
    yield (base_url, port)

    # Teardown
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


@pytest.fixture
def http_medical_graph_client(mock_med_graph_server) -> MedicalGraphClient:
    """Return a MedicalGraphClient configured to talk to the mock_med_graph_server.

    Tests can use this client directly; its network calls will hit the mock server.
    """
    base_url, port = mock_med_graph_server
    client = MedicalGraphClient(base_url=base_url, api_key=None, timeout=5)
    # Use the real requests.Session that the client creates (the server is local)
    return client


# ============================================================================
# PostgreSQL Fixture for Integration Tests
# ============================================================================


def _wait_for_postgres(db_url: str, retries: int = 30) -> bool:
    """Wait for postgres to be ready."""
    for _ in range(retries):
        try:
            with psycopg2.connect(db_url):
                return True
        except psycopg2.OperationalError:
            time.sleep(1)
    return False


@pytest.fixture(scope="session")
def postgres_container():
    """
    Starts a PostgreSQL container with pgvector using docker-compose.
    Yields the database connection URL.
    """
    # Find a free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    # Create a temporary directory for data
    # Use mkdtemp so we can control cleanup manually to handle Docker permissions
    temp_data_dir = tempfile.mkdtemp()

    db_url = f"postgresql://postgres:postgres@localhost:{port}/medgraph"

    # Path to the docker-compose file in the root directory
    docker_compose_file = Path(__file__).parent.parent / "docker-compose.yml"

    # Start the container
    logger = logging.getLogger(__name__)
    logger.info(f"Starting PostgreSQL container on port {port} with data in {temp_data_dir}")

    cmd = ["docker", "compose", "-f", str(docker_compose_file), "up", "-d", "postgres"]
    env = {**os.environ, "POSTGRES_PORT": str(port), "POSTGRES_DATA_DIR": str(temp_data_dir)}

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True)

        if not _wait_for_postgres(db_url):
            pytest.fail("PostgreSQL container failed to start")

        # Set up the database schema using SQLModel
        logger.info("Setting up database schema...")
        # Import models first so they register with SQLModel.metadata
        # Only import Entity and Relationship which are needed for these tests
        from med_lit_schema import entity_sqlmodel, relationship_sqlmodel  # noqa: F401
        from med_lit_schema.setup_database import setup_database

        setup_database(db_url, skip_vector_index=True)  # Skip vector index for faster test setup
        logger.info("Database schema setup complete")

        yield db_url

    finally:
        # Teardown
        logger.info("Stopping PostgreSQL container")
        down_cmd = ["docker", "compose", "-f", str(docker_compose_file), "down"]
        subprocess.run(down_cmd, env=env, check=False, capture_output=True)

        # Cleanup data directory
        # Docker creates files as root (or postgres user), which we can't delete directly.
        # Use a docker container to remove the files first.
        try:
            cleanup_cmd = ["docker", "run", "--rm", "-v", f"{temp_data_dir}:/data", "alpine", "sh", "-c", "rm -rf /data/*"]
            subprocess.run(cleanup_cmd, check=False, capture_output=True)
        except Exception as e:
            logger.warning(f"Failed to clean up docker files via container: {e}")

        # Now remove the directory
        try:
            shutil.rmtree(temp_data_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to remove temporary directory {temp_data_dir}: {e}")


##############################


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    """
    A fake requests.Session-like object with a post() method.
    The returned payload is chosen heuristically based on the JSON body.
    """

    def __init__(self):
        self.headers = {}

    def post(self, url, json=None, timeout=None):
        body = json or {}
        find = body.get("find") or body.get("query")

        # Mirror the mock HTTP server logic used elsewhere:
        if isinstance(find, str) and find == "nodes":
            results = [
                {
                    "pmc_id": "PMC0001",
                    "title": "Mock study: Drug X treats Breast Cancer (small RCT)",
                    "section": "results",
                    "score": 0.95,
                    "chunk_text": "We found that Drug X reduced tumor size significantly...",
                },
                {
                    "pmc_id": "PMC0002",
                    "title": "Observational evidence for Drug X in breast cancer",
                    "section": "discussion",
                    "score": 0.82,
                    "chunk_text": "Cohort study showing association between Drug X and improved outcomes...",
                },
            ]
            return FakeResponse({"results": results}, 200)

        if isinstance(find, str) and find == "paths":
            results = [
                {
                    "path": [
                        {"node_type": "drug", "name": body.get("path_pattern", {}).get("start", {}).get("name", "Drug X")},
                        {"edge": "binds_to"},
                        {"node_type": "protein", "name": "Protein Y"},
                    ],
                    "score": 0.9,
                    "evidence": [{"paper_id": "PMC0003", "confidence": 0.88}],
                }
            ]
            return FakeResponse({"results": results}, 200)

        if isinstance(body.get("query"), str):
            q = body["query"].lower()
            if "brca1" in q or "breast" in q:
                results = [
                    {
                        "pmc_id": "PMC_BREAST_01",
                        "title": "BRCA1 and response to Drug X",
                        "section": "results",
                        "score": 0.93,
                        "chunk_text": "In BRCA1-mutated patients, Drug X showed improved progression-free survival...",
                    }
                ]
            else:
                results = [
                    {
                        "pmc_id": "PMC_MISC_01",
                        "title": "General literature match",
                        "section": "introduction",
                        "score": 0.6,
                        "chunk_text": "This paper discusses related mechanisms...",
                    }
                ]
            return FakeResponse({"results": results}, 200)

        # Fallback empty results
        return FakeResponse({"results": []}, 200)


@pytest.fixture
def fake_session(monkeypatch):
    """Provide a FakeSession instance to patch into MedicalGraphClient."""
    sess = FakeSession()
    yield sess


@pytest.fixture
def mocked_medical_graph_client(monkeypatch, fake_session) -> MedicalGraphClient:
    """
    Return a MedicalGraphClient configured to use FakeSession (no network).
    This allows tests to exercise serialization + HTTP-path code without sockets.
    """
    client = MedicalGraphClient(base_url="http://127.0.0.1:0", api_key=None, timeout=5)
    # Patch the client's session to our fake session
    monkeypatch.setattr(client, "session", fake_session)
    return client


# ============================================================================
# Mini Server Fixture for Integration Tests
# ============================================================================

logger = logging.getLogger(__name__)

# Constants for mini server management
MINI_SERVER_STARTUP_TIMEOUT = 10  # seconds
MINI_SERVER_SHUTDOWN_TIMEOUT = 5  # seconds


def _run_mini_server(port: int):
    """
    Run the mini server in a separate process.

    This function is called in a subprocess to start the uvicorn server.
    """
    import sys

    import uvicorn

    # Add mini_server directory to path to allow imports
    mini_server_dir = Path(__file__).parent / "mini_server"
    if str(mini_server_dir) not in sys.path:
        sys.path.insert(0, str(mini_server_dir))

    # Import the FastAPI app - use relative import since mini_server is in sys.path
    from server import app

    # Run uvicorn server
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",  # Reduce noise in test output
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def _wait_for_server(url: str, timeout: int = MINI_SERVER_STARTUP_TIMEOUT) -> bool:
    """
    Wait for the server to be ready by polling the health endpoint.

    Args:
        url: Base URL of the server
        timeout: Maximum time to wait in seconds

    Returns:
        True if server is ready, False if timeout
    """
    import requests

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            # Check for success status codes (2xx or 3xx)
            if 200 <= response.status_code < 400:
                logger.info(f"Mini server is ready at {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)

    return False


@pytest.fixture(scope="session")
def mini_server() -> Generator[str, None, None]:
    """
    Start mini server for integration tests, tear down afterwards.

    This fixture starts the FastAPI mini server in a separate process,
    waits for it to be ready, yields the server URL, and then cleans up.

    The server runs on a free port and is automatically stopped after tests complete.

    Returns:
        Server URL (e.g., "http://127.0.0.1:8000")
    """
    # Find a free port
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    os.environ["MEDGRAPH_SERVER"] = base_url + "/"

    logger.info(f"Starting mini server on port {port}")

    # Start server in separate process
    process = multiprocessing.Process(target=_run_mini_server, args=(port,), daemon=True)
    process.start()

    try:
        # Wait for server to be ready
        if not _wait_for_server(base_url, timeout=MINI_SERVER_STARTUP_TIMEOUT):
            process.terminate()
            process.join(timeout=2)
            pytest.fail(f"Mini server failed to start within {MINI_SERVER_STARTUP_TIMEOUT} seconds on {base_url}")

        logger.info(f"Mini server started successfully at {base_url}")
        yield base_url

    finally:
        # Cleanup: terminate the server process
        logger.info("Shutting down mini server")
        process.terminate()
        process.join(timeout=MINI_SERVER_SHUTDOWN_TIMEOUT)

        # Force kill if still running
        if process.is_alive():
            logger.warning("Mini server did not terminate gracefully, killing")
            process.kill()
            process.join(timeout=2)
