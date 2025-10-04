"""
FastAPI router for Zendesk ticket operations.

This module provides REST endpoints for ticket operations following FastAPI best practices.
All endpoints are async and use proper dependency injection.
"""
from typing import Annotated, Union
from fastapi import APIRouter, Depends, Query, status

from .dependencies import ZendeskClientDep, ValidTicketDep, TicketServiceDep
from .schemas import (
    TicketsListResponse,
    TicketDetailResponse,
    TicketQueryParams,
    ErrorResponse,
    TicketResponse
)

router = APIRouter(tags=["Zendesk Tickets"])


@router.get(
    "/tickets",
    response_model=TicketsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tickets",
    description="Retrieve tickets from Zendesk with optional filtering and cursor-based pagination",
    responses={
        status.HTTP_200_OK: {
            "model": TicketsListResponse,
            "description": "Successfully retrieved tickets"
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid query parameters"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication failed"
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Zendesk service unavailable"
        }
    }
)
async def get_tickets(
    ticket_service: TicketServiceDep,
    status_filter: Annotated[Union[str, None], Query(
        alias="status",
        description="Filter tickets by status",
        example="open"
    )] = None,
    page_size: Annotated[int, Query(
        ge=1,
        le=100,
        description="Number of tickets per page (1-100)",
        example=25
    )] = 25,
    after_cursor: Annotated[Union[str, None], Query(
        alias="after",
        description="Cursor for pagination",
        example="eyJvIjoibmljZV9pZCIsInYiOiJhUURBIn0="
    )] = None
) -> TicketsListResponse:
    """
    Get tickets from Zendesk with optional filtering and pagination.

    This endpoint supports:
    - Status filtering (open, pending, solved, etc.)
    - Cursor-based pagination for efficient browsing
    - Configurable page sizes (1-100 tickets)

    Example usage:
    - `GET /tickets` - Get first 25 tickets
    - `GET /tickets?status=open&page_size=50` - Get 50 open tickets
    - `GET /tickets?after=cursor123` - Get next page using cursor
    """
    return await ticket_service.get_tickets(
        status=status_filter,
        page_size=page_size,
        after_cursor=after_cursor
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ticket by ID",
    description="Retrieve a specific ticket by its ID",
    responses={
        status.HTTP_200_OK: {
            "model": TicketDetailResponse,
            "description": "Successfully retrieved ticket"
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Ticket not found"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication failed"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Zendesk service unavailable"
        }
    }
)
async def get_ticket_by_id(
    ticket: ValidTicketDep
) -> TicketDetailResponse:
    """
    Get a specific ticket by ID.

    The ticket ID is validated through dependency injection,
    ensuring the ticket exists before processing the request.
    """
    return TicketDetailResponse(ticket=ticket)


@router.get(
    "/tickets/search/by-email",
    response_model=TicketsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search tickets by email",
    description="Search for tickets by customer email address using Zendesk Search API",
    responses={
        status.HTTP_200_OK: {
            "model": TicketsListResponse,
            "description": "Successfully found tickets for the email"
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Missing or invalid email parameter"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication failed"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Zendesk service unavailable"
        }
    }
)
async def search_tickets_by_email(
    ticket_service: TicketServiceDep,
    email: Annotated[str, Query(
        description="Customer email address to search for tickets",
        example="customer@example.com"
    )]
) -> TicketsListResponse:
    """
    Search for tickets by customer email address.

    This endpoint uses Zendesk's Search API to efficiently find all tickets
    associated with a specific customer email address.

    Example usage:
    - `GET /tickets/search/by-email?email=customer@example.com`
    """
    tickets = await ticket_service.search_tickets_by_email(email)

    # Convert to TicketResponse format
    ticket_responses = [
        TicketResponse(**ticket.model_dump())
        for ticket in tickets
    ]

    return TicketsListResponse(
        tickets=ticket_responses,
        count=len(ticket_responses),
        meta={
            "has_more": False,
            "after_cursor": None,
            "before_cursor": None
        }
    )