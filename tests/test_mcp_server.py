import asyncio
from mcp.server import MCPServer


def test_mcp_list_tools_and_formatting():
    server = MCPServer(server_url="http://localhost:9200")
    # tools listing should be present
    tools = asyncio.run(server.handle_list_tools())
    assert "tools" in tools
    assert isinstance(tools["tools"], list)
    # test formatting helpers
    empty = server._format_search_results([], "some query")
    assert "No results found for" in empty

    sample_results = [
        {"pmc_id": "PMC111", "title": "Study A", "section": "results", "score": 0.9, "chunk_text": "Findings..."},
        {"pmc_id": "PMC222", "title": "Study B", "section": "discussion", "score": 0.8, "chunk_text": "More findings..."},
    ]
    formatted = server._format_search_results(sample_results, "a test")
    assert "Graph Search Results" in formatted
    assert "PMC111" in formatted
    assert "Study A" in formatted


def test_mcp_initialize_sets_client():
    server = MCPServer(server_url="http://localhost:9200")
    ok = asyncio.run(server.initialize())
    # initialize simply constructs the MedicalGraphClient inside; it should return True on success
    assert ok is True
    assert server.client is not None
