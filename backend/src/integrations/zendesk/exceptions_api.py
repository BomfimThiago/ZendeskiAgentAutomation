"""
Custom API exceptions for Zendesk operations.

This module defines FastAPI-specific exceptions for Zendesk operations,
extending the core DetailedHTTPException to provide proper HTTP status codes.
"""
from fastapi import status
from src.core.exceptions import DetailedHTTPException


class ZendeskServiceUnavailableException(DetailedHTTPException):
    """Raised when Zendesk service is unavailable."""
    STATUS_CODE = status.HTTP_503_SERVICE_UNAVAILABLE
    DETAIL = "Zendesk service unavailable"


class ZendeskConnectionException(DetailedHTTPException):
    """Raised when connection to Zendesk fails."""
    STATUS_CODE = status.HTTP_503_SERVICE_UNAVAILABLE
    DETAIL = "Failed to connect to Zendesk"


class ZendeskAuthenticationException(DetailedHTTPException):
    """Raised when Zendesk authentication fails."""
    STATUS_CODE = status.HTTP_401_UNAUTHORIZED
    DETAIL = "Authentication failed with Zendesk"


class ZendeskRateLimitException(DetailedHTTPException):
    """Raised when Zendesk rate limit is exceeded."""
    STATUS_CODE = status.HTTP_429_TOO_MANY_REQUESTS
    DETAIL = "Rate limit exceeded. Please try again later."


class TicketNotFoundException(DetailedHTTPException):
    """Raised when a ticket is not found."""
    STATUS_CODE = status.HTTP_404_NOT_FOUND
    DETAIL = "Ticket not found"


class ZendeskBadRequestException(DetailedHTTPException):
    """Raised when Zendesk request is invalid."""
    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    DETAIL = "Invalid request to Zendesk"