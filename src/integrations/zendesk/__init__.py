"""
Zendesk integration module.

This module provides essential Zendesk API integration including
client, configuration, models, and FastAPI endpoints for ticket operations.
"""
from .client import ZendeskClient, ZendeskPaginator, get_zendesk_client
from .config import zendesk_config
from .models import (
    ZendeskTicket,
    ZendeskResponse,
    PaginatedTicketsResponse
)
from .router import router as zendesk_router
from .chat_router import router as chat_router
from .service import TicketService
from .exceptions_api import (
    ZendeskServiceUnavailableException,
    ZendeskConnectionException,
    ZendeskAuthenticationException,
    ZendeskRateLimitException,
    TicketNotFoundException,
    ZendeskBadRequestException
)
from .utils import handle_zendesk_api_error, handle_unexpected_error

__all__ = [
    "ZendeskClient",
    "ZendeskPaginator",
    "get_zendesk_client",
    "zendesk_config",
    "ZendeskTicket",
    "ZendeskResponse",
    "PaginatedTicketsResponse",
    "zendesk_router",
    "chat_router",
    "TicketService",
    "ZendeskServiceUnavailableException",
    "ZendeskConnectionException",
    "ZendeskAuthenticationException",
    "ZendeskRateLimitException",
    "TicketNotFoundException",
    "ZendeskBadRequestException",
    "handle_zendesk_api_error",
    "handle_unexpected_error"
]