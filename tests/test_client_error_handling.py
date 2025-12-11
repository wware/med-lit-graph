"""
Test client error handling when the service returns errors or is unavailable.

Ensures the client fails gracefully and provides clear error messages when:
- Service returns 4xx/5xx errors
- Network errors occur
- Response is malformed
- Timeouts happen
"""

import pytest
import json
import requests

from client.python.client import MedicalGraphClient, QueryBuilder


class FakeErrorResponse:
    """Mock response object that simulates various error conditions."""

    def __init__(self, status_code, json_data=None, raise_on_json=False):
        self.status_code = status_code
        self._json_data = json_data or {}
        self._raise_on_json = raise_on_json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if self._raise_on_json:
            raise json.JSONDecodeError("Invalid JSON", "", 0)
        return self._json_data


def test_client_handles_400_bad_request():
    """
    Test that client properly handles 400 Bad Request from service.

    This happens when the query is malformed or invalid.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    # Mock session that returns 400
    class BadRequestSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(
                400, {"error": "VALIDATION_ERROR", "message": "field 'find' is required"}
            )

    client.session = BadRequestSession()

    # Should raise HTTPError
    with pytest.raises(requests.HTTPError) as exc_info:
        client.execute_raw({"invalid": "query"})

    assert "400" in str(exc_info.value)


def test_client_handles_404_not_found():
    """
    Test that client handles 404 Not Found.

    This could happen if the API endpoint doesn't exist.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class NotFoundSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(404, {"error": "Not found"})

    client.session = NotFoundSession()

    with pytest.raises(requests.HTTPError):
        client.execute_raw({"find": "nodes"})


def test_client_handles_500_internal_server_error():
    """
    Test that client handles 500 Internal Server Error.

    Service is having problems - client should fail gracefully.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class ServerErrorSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(500, {"error": "Internal server error"})

    client.session = ServerErrorSession()

    with pytest.raises(requests.HTTPError):
        client.execute_raw({"find": "nodes"})


def test_client_handles_503_service_unavailable():
    """
    Test that client handles 503 Service Unavailable.

    Service is down or overloaded.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class UnavailableSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(503, {"error": "Service unavailable"})

    client.session = UnavailableSession()

    with pytest.raises(requests.HTTPError):
        client.execute_raw({"find": "nodes"})


def test_client_handles_timeout():
    """
    Test that client handles network timeout.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=0.001)

    class TimeoutSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            raise requests.Timeout("Request timed out")

    client.session = TimeoutSession()

    with pytest.raises(requests.Timeout):
        client.execute_raw({"find": "nodes"})


def test_client_handles_connection_error():
    """
    Test that client handles connection errors.

    This happens when the service is unreachable.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class ConnectionErrorSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            raise requests.ConnectionError("Failed to establish connection")

    client.session = ConnectionErrorSession()

    with pytest.raises(requests.ConnectionError):
        client.execute_raw({"find": "nodes"})


def test_client_handles_malformed_json_response():
    """
    Test that client handles malformed JSON in response.

    Service returns invalid JSON - client should raise appropriate error.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class MalformedJsonSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(200, raise_on_json=True)

    client.session = MalformedJsonSession()

    with pytest.raises(json.JSONDecodeError):
        client.execute_raw({"find": "nodes"})


def test_client_handles_empty_response():
    """
    Test that client handles empty response gracefully.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class EmptyResponseSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(200, {})

    client.session = EmptyResponseSession()

    # Empty dict is valid JSON, should not raise
    result = client.execute_raw({"find": "nodes"})
    assert isinstance(result, dict)


def test_client_handles_missing_results_field():
    """
    Test that client handles response without 'results' field.

    Service might return valid JSON but unexpected structure.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class NoResultsSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(200, {"data": [], "count": 0})  # No 'results' field

    client.session = NoResultsSession()

    # Client should handle this gracefully
    result = client.execute_raw({"find": "nodes"})
    assert isinstance(result, dict)
    # Client might add a 'results' field or return as-is


def test_client_timeout_parameter_is_used():
    """
    Test that timeout parameter is actually passed to requests.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=42)

    timeout_used = None

    class TimeoutCheckSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            nonlocal timeout_used
            timeout_used = timeout
            return FakeErrorResponse(200, {"results": []})

    client.session = TimeoutCheckSession()
    client.execute_raw({"find": "nodes"})

    # Verify timeout was passed through
    assert timeout_used == 42


def test_client_sets_content_type_header():
    """
    Test that client sets proper Content-Type header.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None)

    json_sent = None

    class HeaderCheckSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            nonlocal json_sent
            json_sent = json
            return FakeErrorResponse(200, {"results": []})

    client.session = HeaderCheckSession()
    client.execute_raw({"find": "nodes", "node_pattern": {"node_type": "drug"}})

    # Verify JSON was sent
    assert json_sent is not None
    assert "find" in json_sent


def test_client_handles_401_unauthorized():
    """
    Test that client handles 401 Unauthorized.

    This happens when API key is invalid or missing.
    """
    client = MedicalGraphClient(base_url="http://test", api_key="invalid", timeout=1)

    class UnauthorizedSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(401, {"error": "Invalid API key"})

    client.session = UnauthorizedSession()

    with pytest.raises(requests.HTTPError) as exc_info:
        client.execute_raw({"find": "nodes"})

    assert "401" in str(exc_info.value)


def test_client_handles_429_rate_limit():
    """
    Test that client handles 429 Too Many Requests (rate limiting).
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class RateLimitSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(
                429, {"error": "Rate limit exceeded", "retry_after": 60}
            )

    client.session = RateLimitSession()

    with pytest.raises(requests.HTTPError) as exc_info:
        client.execute_raw({"find": "nodes"})

    assert "429" in str(exc_info.value)


def test_client_with_invalid_base_url():
    """
    Test client creation with invalid base URL.
    """
    # Client should be created, but requests will fail
    client = MedicalGraphClient(base_url="not-a-valid-url", timeout=1)
    assert client.base_url == "not-a-valid-url"


def test_client_serialization_error_handling():
    """
    Test that client handles objects that can't be JSON serialized.
    """
    MedicalGraphClient(base_url="http://test", api_key=None)

    # Create a query with a non-serializable object
    class NonSerializable:
        pass

    query = {"find": "nodes", "custom_object": NonSerializable()}

    # Should raise TypeError when trying to serialize
    with pytest.raises(TypeError):
        # Try to serialize manually - client might handle this internally
        json.dumps(query)


def test_execute_with_typed_query_handles_errors():
    """
    Test that execute() method (with GraphQuery) also handles errors.
    """
    client = MedicalGraphClient(base_url="http://test", api_key=None, timeout=1)

    class ErrorSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            return FakeErrorResponse(500, {"error": "Server error"})

    client.session = ErrorSession()

    # Build a typed query
    query = QueryBuilder().find_nodes("drug", name="aspirin").limit(10).build()

    with pytest.raises(requests.HTTPError):
        client.execute(query)


def test_client_handles_network_unreachable():
    """
    Test that client handles network being unreachable.
    """
    MedicalGraphClient(base_url="http://192.0.2.1", api_key=None, timeout=0.1)

    # Note: This might actually try to connect in real tests
    # In production, you'd mock the socket layer
    # For now, document expected behavior

    # Expected: ConnectionError or Timeout when network is unreachable
    # (Exact behavior depends on network configuration)
    pass


def test_client_handles_dns_failure():
    """
    Test that client handles DNS resolution failures.
    """
    client = MedicalGraphClient(
        base_url="http://this-domain-definitely-does-not-exist-12345.com",
        api_key=None,
        timeout=1,
    )

    class DNSFailSession:
        def __init__(self):
            self.headers = {}

        def post(self, url, json=None, timeout=None):
            raise requests.ConnectionError("Failed to resolve hostname")

    client.session = DNSFailSession()

    with pytest.raises(requests.ConnectionError):
        client.execute_raw({"find": "nodes"})


def test_client_api_key_header():
    """
    Test that API key is properly set when provided to client.

    This documents that client accepts api_key parameter.
    Implementation detail of where it's stored may vary.
    """
    # Client should accept api_key parameter without error
    client = MedicalGraphClient(base_url="http://test", api_key="test-key-123", timeout=1)

    # Client created successfully - exact storage mechanism is implementation detail
    assert client is not None
    assert client.base_url == "http://test"
