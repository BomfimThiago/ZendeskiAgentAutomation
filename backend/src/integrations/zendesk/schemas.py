"""
Pydantic schemas for Zendesk ticket API endpoints.

This module defines request/response models for the ticket API,
following FastAPI best practices for API documentation and validation.
"""
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field

from src.core.models import CustomModel


class TicketQueryParams(BaseModel):
    """Query parameters for ticket listing."""
    status: Optional[str] = Field(
        None,
        description="Filter tickets by status (open, pending, solved, etc.)",
        example="open"
    )
    page_size: Optional[int] = Field(
        25,
        ge=1,
        le=100,
        description="Number of tickets per page (1-100)",
        example=25
    )
    after_cursor: Optional[str] = Field(
        None,
        description="Cursor for pagination (use after_cursor from previous response)",
        example="eyJvIjoibmljZV9pZCIsInYiOiJhUURBIn0="
    )


class TicketResponse(CustomModel):
    """Single ticket response model."""
    id: int = Field(description="Ticket ID", example=123)
    subject: str = Field(description="Ticket subject", example="Login issue")
    description: Optional[str] = Field(description="Ticket description", example="User cannot log in")
    status: str = Field(description="Ticket status", example="open")
    priority: Optional[str] = Field(description="Ticket priority", example="normal")
    type: Optional[str] = Field(description="Ticket type", example="incident")
    tags: List[str] = Field(default=[], description="Ticket tags", example=["login", "urgent"])
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    requester_id: int = Field(description="ID of user who created the ticket", example=456)
    assignee_id: Optional[int] = Field(description="ID of assigned agent", example=789)
    organization_id: Optional[int] = Field(description="Organization ID", example=111)


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    has_more: bool = Field(description="Whether there are more results", example=True)
    after_cursor: Optional[str] = Field(
        description="Cursor for next page",
        example="eyJvIjoibmljZV9pZCIsInYiOiJhUURBIn0="
    )
    before_cursor: Optional[str] = Field(
        description="Cursor for previous page",
        example="eyJvIjoiYmVmb3JlX2lkIiwidjI6MjMzMn0="
    )


class TicketsListResponse(BaseModel):
    """Response model for ticket listing with pagination."""
    tickets: List[TicketResponse] = Field(description="List of tickets")
    meta: PaginationMeta = Field(description="Pagination metadata")
    count: int = Field(description="Number of tickets in this response", example=25)


class TicketDetailResponse(BaseModel):
    """Response model for single ticket detail."""
    ticket: TicketResponse = Field(description="Ticket details")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type", example="TicketNotFound")
    message: str = Field(description="Error message", example="Ticket with ID 123 not found")
    details: Optional[dict] = Field(description="Additional error details")