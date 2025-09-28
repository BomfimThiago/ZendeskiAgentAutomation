"""
Zendesk integration module.

This module provides essential Zendesk API integration including
client, configuration, and models for basic ticket operations.
"""
from .client import ZendeskClient, ZendeskPaginator, get_zendesk_client
from .config import zendesk_config
from .models import (
    ZendeskTicket,
    ZendeskResponse,
    PaginatedTicketsResponse
)

__all__ = [
    "ZendeskClient",
    "ZendeskPaginator",
    "get_zendesk_client",
    "zendesk_config",
    "ZendeskTicket",
    "ZendeskResponse",
    "PaginatedTicketsResponse"
]