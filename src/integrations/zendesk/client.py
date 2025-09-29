"""
Zendesk API client for basic ticket operations.

This module provides a simplified client for interacting with the Zendesk API,
focusing on essential ticket operations with cursor-based pagination.
"""
import base64
from typing import List, Optional, Dict, Any

from src.core.logging_config import get_logger, log_with_context
from src.core.http_client import AsyncHTTPClient
from .config import zendesk_config
from .exceptions import ZendeskAPIError
from .models import ZendeskTicket, ZendeskResponse, PaginatedTicketsResponse

logger = get_logger("zendesk_client")


class ZendeskPaginator:
    """Cursor-based paginator for Zendesk API responses."""

    def __init__(self, client: 'ZendeskClient', endpoint: str, params: Optional[Dict] = None):
        self.client = client
        self.endpoint = endpoint
        self.params = params or {}
        self._current_cursor = None
        self._has_more = True

    def __aiter__(self):
        """Async iterator for paginated results."""
        return self

    async def __anext__(self):
        """Get next page of results."""
        if not self._has_more:
            raise StopAsyncIteration

        request_params = self.params.copy()
        request_params["page[size]"] = min(
            request_params.get("page[size]", self.client.config.DEFAULT_PAGE_SIZE),
            self.client.config.MAX_PAGE_SIZE
        )

        if self._current_cursor:
            request_params["page[after]"] = self._current_cursor

        response_data = await self.client._make_request("GET", self.endpoint, params=request_params)

        meta = response_data.get("meta", {})
        self._has_more = meta.get("has_more", False)
        self._current_cursor = meta.get("after_cursor")

        return response_data

    async def get_all(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Get all results from all pages (use with caution for large datasets)."""
        all_results = []
        page_count = 0

        async for page_data in self:
            all_results.append(page_data)
            page_count += 1

            if max_pages and page_count >= max_pages:
                log_with_context(
                    logger,
                    30,  # WARNING
                    f"Reached max_pages limit of {max_pages}",
                    endpoint=self.endpoint
                )
                break

        return all_results


class ZendeskClient:
    """Async client for Zendesk API operations."""

    def __init__(self):
        self.config = zendesk_config
        self._http_client: Optional[AsyncHTTPClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize the HTTP client with authentication."""
        auth_string = f"{self.config.EMAIL}/token:{self.config.TOKEN}"
        auth_bytes = auth_string.encode('utf-8')
        auth_header = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        self._http_client = AsyncHTTPClient(
            base_url=self.config.api_url,
            headers=headers,
            config=self.config
        )
        await self._http_client.connect()

        log_with_context(
            logger,
            20,  # INFO
            "Zendesk client connected",
            base_url=self.config.api_url
        )

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.disconnect()
            log_with_context(logger, 20, "Zendesk client disconnected")

    @property
    def http_client(self) -> AsyncHTTPClient:
        """Get the HTTP client instance."""
        if not self._http_client:
            raise RuntimeError("Zendesk client not connected. Use 'async with' or call connect()")
        return self._http_client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request using the core HTTP client."""
        return await self.http_client.make_request(
            method=method,
            endpoint=endpoint,
            data=data,
            params=params,
            custom_error_class=ZendeskAPIError
        )

    # Pagination Methods
    def get_tickets_paginated(
        self,
        status: Optional[str] = None,
        page_size: Optional[int] = None
    ) -> ZendeskPaginator:
        """Get paginated tickets with optional filtering."""
        params = {}
        if status:
            params["status"] = status
        if page_size:
            params["page[size]"] = min(page_size, self.config.MAX_PAGE_SIZE)

        return ZendeskPaginator(self, "tickets.json", params)

    async def get_tickets_page(
        self,
        status: Optional[str] = None,
        page_size: Optional[int] = None,
        after_cursor: Optional[str] = None
    ) -> PaginatedTicketsResponse:
        """Get a single page of tickets with cursor pagination."""
        params = {}
        if status:
            params["status"] = status
        if page_size:
            params["page[size]"] = min(page_size, self.config.MAX_PAGE_SIZE)
        if after_cursor:
            params["page[after]"] = after_cursor

        response_data = await self._make_request("GET", "tickets.json", params=params)
        return PaginatedTicketsResponse(**response_data)

    # Ticket Operations
    async def get_ticket(self, ticket_id: int) -> ZendeskTicket:
        """Get a single ticket by ID."""
        response_data = await self._make_request("GET", f"tickets/{ticket_id}.json")
        return ZendeskTicket(**response_data["ticket"])

    async def get_tickets(
        self,
        status: Optional[str] = None,
        page_size: int = None,
        use_pagination: bool = False
    ) -> List[ZendeskTicket]:
        """Get tickets with optional filtering.

        Args:
            status: Filter by ticket status
            page_size: Number of tickets per page
            use_pagination: If True, uses cursor pagination for large datasets
        """
        if use_pagination:
            paginator = self.get_tickets_paginated(status=status, page_size=page_size)
            all_tickets = []

            async for page_data in paginator:
                tickets = [ZendeskTicket(**ticket) for ticket in page_data.get("tickets", [])]
                all_tickets.extend(tickets)

                if len(all_tickets) >= 10000:
                    log_with_context(
                        logger,
                        30,  # WARNING
                        "Reached safety limit of 10,000 tickets",
                        total_tickets=len(all_tickets)
                    )
                    break

            return all_tickets
        else:
            params = {}
            if status:
                params["status"] = status
            if page_size:
                params["per_page"] = min(page_size, self.config.MAX_PAGE_SIZE)

            response_data = await self._make_request("GET", "tickets.json", params=params)
            return [ZendeskTicket(**ticket) for ticket in response_data.get("tickets", [])]

    async def get_all_tickets(
        self,
        status: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> List[ZendeskTicket]:
        """Get ALL tickets using cursor pagination."""
        paginator = self.get_tickets_paginated(status=status)
        all_tickets = []
        page_count = 0

        async for page_data in paginator:
            tickets = [ZendeskTicket(**ticket) for ticket in page_data.get("tickets", [])]
            all_tickets.extend(tickets)
            page_count += 1

            log_with_context(
                logger,
                20,  # INFO
                f"Retrieved page {page_count}",
                tickets_this_page=len(tickets),
                total_tickets=len(all_tickets)
            )

            if max_pages and page_count >= max_pages:
                log_with_context(
                    logger,
                    30,  # WARNING
                    f"Reached max_pages limit of {max_pages}",
                    total_tickets=len(all_tickets)
                )
                break

        log_with_context(
            logger,
            20,  # INFO
            "Completed retrieving all tickets",
            total_tickets=len(all_tickets),
            total_pages=page_count
        )

        return all_tickets

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
            ZendeskAPIError: If ticket creation fails
        """
        # Build ticket data
        ticket_data = {
            "subject": subject,
            "comment": {
                "body": description
            },
            "type": ticket_type,
            "priority": priority
        }

        # Add requester information if provided
        if requester_email or requester_name:
            requester_data = {}
            if requester_email:
                requester_data["email"] = requester_email
            if requester_name:
                requester_data["name"] = requester_name
            ticket_data["requester"] = requester_data

        # Add tags if provided
        if tags:
            ticket_data["tags"] = tags

        # Make the API request
        request_payload = {"ticket": ticket_data}

        log_with_context(
            logger,
            20,  # INFO
            "Creating new ticket",
            subject=subject,
            type=ticket_type,
            priority=priority,
            has_requester=bool(requester_email or requester_name)
        )

        response_data = await self._make_request("POST", "tickets.json", data=request_payload)
        created_ticket = ZendeskTicket(**response_data["ticket"])

        log_with_context(
            logger,
            20,  # INFO
            "Successfully created ticket",
            ticket_id=created_ticket.id,
            subject=created_ticket.subject,
            status=created_ticket.status
        )

        return created_ticket

    async def search_tickets_by_email(self, customer_email: str) -> List[ZendeskTicket]:
        """
        Search for tickets by customer email using Zendesk Search API.

        Args:
            customer_email: Customer's email address to search for

        Returns:
            List of ZendeskTicket models matching the email

        Raises:
            ZendeskAPIError: If search fails
        """
        try:
            # Use Zendesk Search API to find tickets by requester email
            search_query = f"type:ticket requester:{customer_email}"
            params = {
                "query": search_query,
                "sort_by": "updated_at",
                "sort_order": "desc"
            }

            log_with_context(
                logger,
                20,  # INFO
                "Searching tickets by email",
                email=customer_email
            )

            response_data = await self._make_request("GET", "search.json", params=params)

            # Parse tickets from search results
            tickets = []
            for result in response_data.get("results", []):
                if result.get("result_type") == "ticket":
                    tickets.append(ZendeskTicket(**result))

            log_with_context(
                logger,
                20,  # INFO
                "Successfully found tickets by email",
                email=customer_email,
                ticket_count=len(tickets)
            )

            return tickets

        except ZendeskAPIError as e:
            log_with_context(
                logger,
                40,  # ERROR
                "Failed to search tickets by email",
                email=customer_email,
                error=str(e)
            )
            raise

        except Exception as e:
            log_with_context(
                logger,
                40,  # ERROR
                "Unexpected error searching tickets by email",
                email=customer_email,
                error=str(e)
            )
            raise ZendeskAPIError(f"Unexpected error searching tickets: {str(e)}")



async def get_zendesk_client() -> ZendeskClient:
    """Get a Zendesk client instance."""
    client = ZendeskClient()
    await client.connect()
    return client