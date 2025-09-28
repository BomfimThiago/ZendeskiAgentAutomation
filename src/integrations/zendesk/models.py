"""
Essential Pydantic models for Zendesk API responses.

This module defines the core data models used for Zendesk API interactions,
focusing on tickets and pagination.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.core.models import CustomModel


class ZendeskTicket(CustomModel):
    """Zendesk ticket model."""
    id: int
    subject: str
    description: Optional[str] = None
    status: str  # new, open, pending, hold, solved, closed
    priority: Optional[str] = None  # low, normal, high, urgent
    type: Optional[str] = None  # problem, incident, question, task
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    requester_id: int
    assignee_id: Optional[int] = None
    organization_id: Optional[int] = None
    custom_fields: List[Dict[str, Any]] = []


class ZendeskResponse(CustomModel):
    """Generic Zendesk API response wrapper."""
    ticket: Optional[ZendeskTicket] = None
    tickets: Optional[List[ZendeskTicket]] = []
    count: Optional[int] = None
    next_page: Optional[str] = None
    previous_page: Optional[str] = None


class PaginationLinks(CustomModel):
    """Pagination links from Zendesk API response."""
    next: Optional[str] = None
    prev: Optional[str] = None


class PaginationMeta(CustomModel):
    """Pagination metadata from Zendesk API response."""
    has_more: bool = False
    after_cursor: Optional[str] = None
    before_cursor: Optional[str] = None


class PaginatedResponse(CustomModel):
    """Base paginated response from Zendesk API."""
    links: Optional[PaginationLinks] = None
    meta: Optional[PaginationMeta] = None


class PaginatedTicketsResponse(PaginatedResponse):
    """Paginated tickets response."""
    tickets: List[ZendeskTicket] = []
