"""
Dependencies for Zendesk ticket endpoints.

This module provides dependency injection functions for ticket operations,
including validation, authentication, and data retrieval dependencies.
Uses custom exceptions instead of HTTPException for better error handling.
"""
from typing import Annotated, Dict, Any
from fastapi import Depends

from .client import ZendeskClient, get_zendesk_client
from .exceptions import ZendeskAPIError
from .exceptions_api import ZendeskConnectionException
from .utils import handle_zendesk_api_error, handle_unexpected_error

from src.core.logging_config import get_logger, log_with_context

logger = get_logger("zendesk_dependencies")


async def get_zendesk_client_dep() -> ZendeskClient:
    """Dependency to get Zendesk client instance.

    This dependency ensures proper connection management and error handling
    for all Zendesk operations using custom exceptions.

    Returns:
        ZendeskClient: Connected Zendesk client instance

    Raises:
        ZendeskConnectionException: When connection to Zendesk fails
    """
    try:
        client = await get_zendesk_client()
        log_with_context(
            logger,
            20,  # INFO
            "Zendesk client dependency resolved successfully"
        )
        return client
    except Exception as e:
        log_with_context(
            logger,
            40,  # ERROR
            "Failed to get Zendesk client in dependency",
            error=str(e)
        )
        raise ZendeskConnectionException(f"Failed to connect to Zendesk: {str(e)}")


async def valid_ticket_id(
    ticket_id: int,
    zendesk_client: Annotated[ZendeskClient, Depends(get_zendesk_client_dep)]
) -> Dict[str, Any]:
    """Validate ticket ID and return ticket data.

    This dependency validates that a ticket exists and returns its data.
    It's reusable across multiple endpoints that need ticket validation.

    Args:
        ticket_id: The ticket ID to validate
        zendesk_client: Injected Zendesk client instance

    Returns:
        Dict containing ticket data

    Raises:
        TicketNotFoundException: When ticket is not found
        ZendeskAuthenticationException: When authentication fails
        ZendeskRateLimitException: When rate limit is exceeded
        ZendeskServiceUnavailableException: For other Zendesk API errors
        InternalServerException: For unexpected errors
    """
    try:
        log_with_context(
            logger,
            20,  # INFO
            "Validating ticket ID",
            ticket_id=ticket_id
        )

        ticket = await zendesk_client.get_ticket(ticket_id)

        log_with_context(
            logger,
            20,  # INFO
            "Ticket validation successful",
            ticket_id=ticket_id,
            subject=ticket.subject
        )

        return ticket.model_dump()

    except ZendeskAPIError as e:
        handle_zendesk_api_error(
            error=e,
            operation="ticket validation",
            context={"ticket_id": ticket_id}
        )

    except Exception as e:
        handle_unexpected_error(
            error=e,
            operation="ticket validation",
            context={"ticket_id": ticket_id}
        )


async def get_ticket_service(
    zendesk_client: Annotated[ZendeskClient, Depends(get_zendesk_client_dep)]
) -> "TicketService":
    """Dependency to get TicketService instance.

    This dependency creates a TicketService with the injected Zendesk client,
    following dependency injection best practices.

    Returns:
        TicketService: Service instance for ticket operations
    """
    from .service import TicketService
    return TicketService(zendesk_client)


# Dependency type aliases for better readability and reusability
ZendeskClientDep = Annotated[ZendeskClient, Depends(get_zendesk_client_dep)]
ValidTicketDep = Annotated[Dict[str, Any], Depends(valid_ticket_id)]
TicketServiceDep = Annotated["TicketService", Depends(get_ticket_service)]