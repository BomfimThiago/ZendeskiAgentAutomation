"""
Zendesk integration module.

This module provides essential Zendesk API integration including
client, configuration, models, and chat AI agent.
"""
from .client import ZendeskClient, ZendeskPaginator, get_zendesk_client
from .config import zendesk_config
from .models import (
    ZendeskTicket,
    ZendeskResponse,
    PaginatedTicketsResponse
)
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