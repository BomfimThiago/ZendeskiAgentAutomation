"""
Utility functions for Zendesk integration.

This module provides reusable utility functions to reduce code duplication
across the Zendesk integration components.
"""
from typing import Optional, Any, Dict
from src.core.logging_config import get_logger, log_with_context

from .exceptions import ZendeskAPIError
from .exceptions_api import (
    ZendeskAuthenticationException,
    ZendeskRateLimitException,
    ZendeskServiceUnavailableException,
    ZendeskBadRequestException,
    TicketNotFoundException
)
from src.core.exceptions import InternalServerException

logger = get_logger("zendesk_utils")


def handle_zendesk_api_error(
    error: ZendeskAPIError,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Handle ZendeskAPIError by logging and raising appropriate custom exception.

    This utility function centralizes the error handling logic for ZendeskAPIError,
    eliminating code duplication across service methods.

    Args:
        error: The ZendeskAPIError that was caught
        operation: Description of the operation that failed (for logging)
        context: Optional context data for logging (e.g., ticket_id, status)

    Raises:
        TicketNotFoundException: When ticket is not found (404)
        ZendeskAuthenticationException: When authentication fails (401/403)
        ZendeskRateLimitException: When rate limit is exceeded (429)
        ZendeskBadRequestException: For client errors (4xx)
        ZendeskServiceUnavailableException: For other API errors
    """
    log_context = {
        "error": str(error),
        "status_code": error.status_code,
        "operation": operation
    }

    if context:
        log_context.update(context)

    log_with_context(
        logger,
        40,  # ERROR
        f"Zendesk API error during {operation}",
        **log_context
    )

    # Map ZendeskAPIError to appropriate custom exception
    if error.is_not_found_error:
        if context and "ticket_id" in context:
            raise TicketNotFoundException(f"Ticket with ID {context['ticket_id']} not found")
        else:
            raise TicketNotFoundException("Resource not found")
    elif error.is_auth_error:
        raise ZendeskAuthenticationException("Authentication failed with Zendesk")
    elif error.is_rate_limit_error:
        raise ZendeskRateLimitException("Rate limit exceeded. Please try again later.")
    elif error.is_client_error:
        raise ZendeskBadRequestException(f"Invalid request: {str(error)}")
    else:
        raise ZendeskServiceUnavailableException(f"Zendesk API error: {str(error)}")


def handle_unexpected_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Handle unexpected errors by logging and raising InternalServerException.

    Args:
        error: The unexpected exception that was caught
        operation: Description of the operation that failed (for logging)
        context: Optional context data for logging

    Raises:
        InternalServerException: Always raises this for unexpected errors
    """
    log_context = {
        "error": str(error),
        "error_type": type(error).__name__,
        "operation": operation
    }

    # Add any additional context provided
    if context:
        log_context.update(context)

    log_with_context(
        logger,
        40,  # ERROR
        f"Unexpected error during {operation}",
        **log_context
    )

    raise InternalServerException(f"Internal server error: {str(error)}")