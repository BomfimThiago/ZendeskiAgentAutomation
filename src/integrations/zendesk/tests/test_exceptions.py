"""
Unit tests for Zendesk exceptions.
"""
import pytest

from src.integrations.zendesk.exceptions import (
    ZendeskAPIError,
    ZendeskConnectionError,
    ZendeskTimeoutError,
    ZendeskRateLimitError
)


class TestZendeskAPIError:
    """Test ZendeskAPIError functionality."""

    def test_basic_error_creation(self):
        """Test basic error creation."""
        error = ZendeskAPIError("Test error")

        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response_data is None
        assert str(error) == "Test error"

    def test_error_with_status_code(self):
        """Test error creation with status code."""
        error = ZendeskAPIError("Not found", status_code=404)

        assert error.message == "Not found"
        assert error.status_code == 404
        assert str(error) == "[404] Not found"

    def test_error_with_response_data(self):
        """Test error creation with response data."""
        response_data = {"error": "invalid_request", "details": "Missing field"}
        error = ZendeskAPIError("Bad request", status_code=400, response_data=response_data)

        assert error.response_data == response_data
        assert error.status_code == 400

    def test_error_repr(self):
        """Test error representation."""
        error = ZendeskAPIError("Test error", status_code=500)
        expected_repr = "ZendeskAPIError(message='Test error', status_code=500)"

        assert repr(error) == expected_repr

    def test_is_rate_limit_error(self):
        """Test rate limit error detection."""
        rate_limit_error = ZendeskAPIError("Rate limited", status_code=429)
        other_error = ZendeskAPIError("Server error", status_code=500)

        assert rate_limit_error.is_rate_limit_error is True
        assert other_error.is_rate_limit_error is False

    def test_is_auth_error(self):
        """Test authentication error detection."""
        unauthorized_error = ZendeskAPIError("Unauthorized", status_code=401)
        forbidden_error = ZendeskAPIError("Forbidden", status_code=403)
        other_error = ZendeskAPIError("Not found", status_code=404)

        assert unauthorized_error.is_auth_error is True
        assert forbidden_error.is_auth_error is True
        assert other_error.is_auth_error is False

    def test_is_not_found_error(self):
        """Test not found error detection."""
        not_found_error = ZendeskAPIError("Not found", status_code=404)
        other_error = ZendeskAPIError("Server error", status_code=500)

        assert not_found_error.is_not_found_error is True
        assert other_error.is_not_found_error is False

    def test_is_client_error(self):
        """Test client error detection (4xx)."""
        client_errors = [
            ZendeskAPIError("Bad request", status_code=400),
            ZendeskAPIError("Unauthorized", status_code=401),
            ZendeskAPIError("Not found", status_code=404),
            ZendeskAPIError("Rate limited", status_code=429)
        ]

        server_error = ZendeskAPIError("Server error", status_code=500)
        no_status_error = ZendeskAPIError("Error")

        for error in client_errors:
            assert error.is_client_error is True

        assert server_error.is_client_error is False
        assert no_status_error.is_client_error is False

    def test_is_server_error(self):
        """Test server error detection (5xx)."""
        server_errors = [
            ZendeskAPIError("Internal error", status_code=500),
            ZendeskAPIError("Bad gateway", status_code=502),
            ZendeskAPIError("Service unavailable", status_code=503)
        ]

        client_error = ZendeskAPIError("Bad request", status_code=400)
        no_status_error = ZendeskAPIError("Error")

        for error in server_errors:
            assert error.is_server_error is True

        assert client_error.is_server_error is False
        assert no_status_error.is_server_error is False

    def test_error_without_status_code_properties(self):
        """Test error properties when no status code is set."""
        error = ZendeskAPIError("Generic error")

        assert error.is_rate_limit_error is False
        assert error.is_auth_error is False
        assert error.is_not_found_error is False
        assert error.is_client_error is False
        assert error.is_server_error is False


class TestSpecificExceptions:
    """Test specific exception subclasses."""

    def test_zendesk_connection_error(self):
        """Test ZendeskConnectionError."""
        error = ZendeskConnectionError("Connection failed", status_code=500)

        assert isinstance(error, ZendeskAPIError)
        assert error.message == "Connection failed"
        assert error.status_code == 500

    def test_zendesk_timeout_error(self):
        """Test ZendeskTimeoutError."""
        error = ZendeskTimeoutError("Request timeout", status_code=408)

        assert isinstance(error, ZendeskAPIError)
        assert error.message == "Request timeout"
        assert error.status_code == 408

    def test_zendesk_rate_limit_error(self):
        """Test ZendeskRateLimitError."""
        error = ZendeskRateLimitError("Rate limit exceeded", status_code=429)

        assert isinstance(error, ZendeskAPIError)
        assert error.message == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.is_rate_limit_error is True

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from ZendeskAPIError."""
        connection_error = ZendeskConnectionError("Connection failed")
        timeout_error = ZendeskTimeoutError("Timeout")
        rate_limit_error = ZendeskRateLimitError("Rate limited")

        assert isinstance(connection_error, ZendeskAPIError)
        assert isinstance(timeout_error, ZendeskAPIError)
        assert isinstance(rate_limit_error, ZendeskAPIError)

        # Test they're also regular exceptions
        assert isinstance(connection_error, Exception)
        assert isinstance(timeout_error, Exception)
        assert isinstance(rate_limit_error, Exception)