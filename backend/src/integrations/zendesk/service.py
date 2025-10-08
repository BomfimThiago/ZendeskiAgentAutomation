"""
Business logic service for Zendesk ticket operations.

This module contains the business logic for ticket operations,
providing reusable service methods for the AI agent.
"""
from typing import List, Optional

from .client import ZendeskClient
from .exceptions import ZendeskAPIError
from .models import ZendeskTicket
from .utils import handle_zendesk_api_error, handle_unexpected_error

from src.core.logging_config import get_logger, log_with_context

logger = get_logger("zendesk_service")


class TicketService:
    """Service class for ticket operations."""

    def __init__(self, zendesk_client: ZendeskClient):
        """Initialize the service with a Zendesk client."""
        self.client = zendesk_client

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

    async def search_tickets_by_email(self, customer_email: str) -> List[ZendeskTicket]:
        """
        Search for tickets by customer email address.

        Args:
            customer_email: Customer's email address to search for

        Returns:
            List of ZendeskTicket models matching the email

        Raises:
            HTTPException: For various API errors
        """
        try:
            log_with_context(
                logger,
                20,  # INFO
                "Searching tickets by email",
                email=customer_email
            )

            tickets = await self.client.search_tickets_by_email(customer_email)

            log_with_context(
                logger,
                20,  # INFO
                "Successfully found tickets by email",
                email=customer_email,
                ticket_count=len(tickets)
            )

            return tickets

        except ZendeskAPIError as e:
            handle_zendesk_api_error(
                error=e,
                operation="searching tickets by email",
                context={"email": customer_email}
            )

        except Exception as e:
            handle_unexpected_error(
                error=e,
                operation="searching tickets by email",
                context={"email": customer_email}
            )