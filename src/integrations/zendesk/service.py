"""
Business logic service for Zendesk ticket operations.

This module contains the business logic for ticket operations,
separating concerns from the router and providing reusable service methods.
"""
from typing import List, Optional

from .client import ZendeskClient
from .exceptions import ZendeskAPIError
from .schemas import TicketsListResponse, PaginationMeta, TicketResponse
from .models import ZendeskTicket
from .utils import handle_zendesk_api_error, handle_unexpected_error

from src.core.logging_config import get_logger, log_with_context

logger = get_logger("zendesk_service")


class TicketService:
    """Service class for ticket operations."""

    def __init__(self, zendesk_client: ZendeskClient):
        """Initialize the service with a Zendesk client."""
        self.client = zendesk_client

    async def get_tickets(
        self,
        status: Optional[str] = None,
        page_size: int = 25,
        after_cursor: Optional[str] = None
    ) -> TicketsListResponse:
        """
        Get tickets with pagination and filtering.

        Args:
            status: Optional status filter
            page_size: Number of tickets per page (1-100)
            after_cursor: Cursor for pagination

        Returns:
            TicketsListResponse with tickets and pagination info

        Raises:
            HTTPException: For various API errors
        """
        try:
            log_with_context(
                logger,
                20,  # INFO
                "Fetching tickets",
                status=status,
                page_size=page_size,
                has_cursor=bool(after_cursor)
            )

            # Get paginated tickets from Zendesk
            paginated_response = await self.client.get_tickets_page(
                status=status,
                page_size=page_size,
                after_cursor=after_cursor
            )

            ticket_responses = [
                TicketResponse(**ticket.model_dump())
                for ticket in paginated_response.tickets
            ]

            meta = PaginationMeta(
                has_more=paginated_response.meta.has_more if paginated_response.meta else False,
                after_cursor=paginated_response.meta.after_cursor if paginated_response.meta else None,
                before_cursor=paginated_response.meta.before_cursor if paginated_response.meta else None
            )

            response = TicketsListResponse(
                tickets=ticket_responses,
                meta=meta,
                count=len(ticket_responses)
            )

            log_with_context(
                logger,
                20,  # INFO
                "Successfully fetched tickets",
                count=len(ticket_responses),
                has_more=meta.has_more
            )

            return response

        except ZendeskAPIError as e:
            handle_zendesk_api_error(
                error=e,
                operation="fetching tickets",
                context={
                    "status": status,
                    "page_size": page_size,
                    "has_cursor": bool(after_cursor)
                }
            )

        except Exception as e:
            handle_unexpected_error(
                error=e,
                operation="fetching tickets",
                context={
                    "status": status,
                    "page_size": page_size,
                    "has_cursor": bool(after_cursor)
                }
            )

    async def get_ticket_by_id(self, ticket_id: int) -> ZendeskTicket:
        """
        Get a single ticket by ID.

        Args:
            ticket_id: The ticket ID to retrieve

        Returns:
            ZendeskTicket model

        Raises:
            HTTPException: For various API errors
        """
        try:
            log_with_context(
                logger,
                20,  # INFO
                "Fetching ticket by ID",
                ticket_id=ticket_id
            )

            ticket = await self.client.get_ticket(ticket_id)

            log_with_context(
                logger,
                20,  # INFO
                "Successfully fetched ticket",
                ticket_id=ticket_id,
                subject=ticket.subject
            )

            return ticket

        except ZendeskAPIError as e:
            handle_zendesk_api_error(
                error=e,
                operation="fetching ticket by ID",
                context={"ticket_id": ticket_id}
            )

        except Exception as e:
            handle_unexpected_error(
                error=e,
                operation="fetching ticket by ID",
                context={"ticket_id": ticket_id}
            )

    async def create_ticket(
        self,
        subject: str,
        description: str,
        requester_email: str = None,
        requester_name: str = None,
        ticket_type: str = "question",
        priority: str = "normal",
        tags: List[str] = None
    ) -> ZendeskTicket:
        """
        Create a new ticket in Zendesk.

        Args:
            subject: Ticket subject line
            description: Ticket description/body
            requester_email: Email of the person requesting support
            requester_name: Name of the person requesting support
            ticket_type: Type of ticket (problem, incident, question, task)
            priority: Priority level (low, normal, high, urgent)
            tags: List of tags for the ticket

        Returns:
            ZendeskTicket model of the created ticket

        Raises:
            HTTPException: For various API errors
        """
        try:
            log_with_context(
                logger,
                20,  # INFO
                "Creating new ticket",
                subject=subject,
                type=ticket_type,
                priority=priority,
                has_requester=bool(requester_email or requester_name)
            )

            ticket = await self.client.create_ticket(
                subject=subject,
                description=description,
                requester_email=requester_email,
                requester_name=requester_name,
                ticket_type=ticket_type,
                priority=priority,
                tags=tags
            )

            log_with_context(
                logger,
                20,  # INFO
                "Successfully created ticket",
                ticket_id=ticket.id,
                subject=ticket.subject,
                status=ticket.status
            )

            return ticket

        except ZendeskAPIError as e:
            handle_zendesk_api_error(
                error=e,
                operation="creating ticket",
                context={
                    "subject": subject,
                    "type": ticket_type,
                    "priority": priority,
                    "has_requester": bool(requester_email or requester_name)
                }
            )

        except Exception as e:
            handle_unexpected_error(
                error=e,
                operation="creating ticket",
                context={
                    "subject": subject,
                    "type": ticket_type,
                    "priority": priority,
                    "has_requester": bool(requester_email or requester_name)
                }
            )