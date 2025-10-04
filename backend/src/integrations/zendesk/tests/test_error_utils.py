"""
Unit tests for Zendesk error handling utilities.

This module tests the error handling utility functions to ensure
they properly map ZendeskAPIError to custom exceptions.
"""
import pytest
from unittest.mock import Mock

from ..utils import handle_zendesk_api_error, handle_unexpected_error
from ..exceptions import ZendeskAPIError
from ..exceptions_api import (
    TicketNotFoundException,
    ZendeskAuthenticationException,
    ZendeskRateLimitException,
    ZendeskBadRequestException,
    ZendeskServiceUnavailableException
)
from src.core.exceptions import InternalServerException


class TestErrorHandlingUtils:
    """Test error handling utility functions."""

    def test_handle_404_error(self):
        """Test that 404 errors are mapped to TicketNotFoundException."""
        error = ZendeskAPIError("Not found", status_code=404)

        with pytest.raises(TicketNotFoundException, match="Ticket with ID 123 not found"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation",
                context={"ticket_id": 123}
            )

    def test_handle_404_error_without_ticket_context(self):
        """Test that 404 errors without ticket context use generic message."""
        error = ZendeskAPIError("Not found", status_code=404)

        with pytest.raises(TicketNotFoundException, match="Resource not found"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation"
            )

    def test_handle_401_error(self):
        """Test that 401 errors are mapped to ZendeskAuthenticationException."""
        error = ZendeskAPIError("Unauthorized", status_code=401)

        with pytest.raises(ZendeskAuthenticationException, match="Authentication failed with Zendesk"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation"
            )

    def test_handle_403_error(self):
        """Test that 403 errors are mapped to ZendeskAuthenticationException."""
        error = ZendeskAPIError("Forbidden", status_code=403)

        with pytest.raises(ZendeskAuthenticationException, match="Authentication failed with Zendesk"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation"
            )

    def test_handle_429_error(self):
        """Test that 429 errors are mapped to ZendeskRateLimitException."""
        error = ZendeskAPIError("Rate limited", status_code=429)

        with pytest.raises(ZendeskRateLimitException, match="Rate limit exceeded"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation"
            )

    def test_handle_400_error(self):
        """Test that 4xx errors are mapped to ZendeskBadRequestException."""
        error = ZendeskAPIError("Bad request", status_code=400)

        with pytest.raises(ZendeskBadRequestException, match="Invalid request"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation"
            )

    def test_handle_500_error(self):
        """Test that 5xx errors are mapped to ZendeskServiceUnavailableException."""
        error = ZendeskAPIError("Server error", status_code=500)

        with pytest.raises(ZendeskServiceUnavailableException, match="Zendesk API error"):
            handle_zendesk_api_error(
                error=error,
                operation="test operation"
            )

    def test_handle_unexpected_error(self):
        """Test that unexpected errors are mapped to InternalServerException."""
        error = ValueError("Something went wrong")

        with pytest.raises(InternalServerException, match="Internal server error"):
            handle_unexpected_error(
                error=error,
                operation="test operation",
                context={"test": "data"}
            )

    def test_error_handling_with_context(self):
        """Test that context data is properly logged."""
        error = ZendeskAPIError("Not found", status_code=404)
        context = {"ticket_id": 123, "user_id": 456}

        with pytest.raises(TicketNotFoundException):
            handle_zendesk_api_error(
                error=error,
                operation="fetching ticket",
                context=context
            )