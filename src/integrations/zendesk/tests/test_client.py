"""
Unit tests for simplified ZendeskClient.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import base64

from src.integrations.zendesk.client import ZendeskClient, ZendeskPaginator, get_zendesk_client
from src.integrations.zendesk.exceptions import ZendeskAPIError
from src.integrations.zendesk.models import ZendeskTicket, PaginatedTicketsResponse


class TestSimplifiedZendeskClient:
    """Test simplified ZendeskClient functionality."""

    def test_client_initialization(self):
        """Test client initializes with correct config."""
        client = ZendeskClient()
        assert client.config is not None
        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_client_connect(self, mock_config):
        """Test client connection setup."""
        with patch('src.integrations.zendesk.client.AsyncHTTPClient') as mock_http_client_class:
            mock_http_client = AsyncMock()
            mock_http_client_class.return_value = mock_http_client

            client = ZendeskClient()
            client.config = mock_config

            await client.connect()

            expected_auth = base64.b64encode(f"{mock_config.EMAIL}/token:{mock_config.TOKEN}".encode()).decode()

            mock_http_client_class.assert_called_once()
            call_args = mock_http_client_class.call_args

            assert call_args[1]['base_url'] == mock_config.api_url
            assert f"Basic {expected_auth}" in call_args[1]['headers']['Authorization']
            mock_http_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ticket_success(self, zendesk_client, sample_ticket_data):
        """Test successful single ticket retrieval."""
        response = {"ticket": sample_ticket_data}
        zendesk_client._make_request = AsyncMock(return_value=response)

        result = await zendesk_client.get_ticket(123)

        assert isinstance(result, ZendeskTicket)
        assert result.id == 123
        assert result.subject == "Test Ticket"
        zendesk_client._make_request.assert_called_once_with(
            "GET", "tickets/123.json"
        )

    @pytest.mark.asyncio
    async def test_get_tickets_legacy_mode(self, zendesk_client, sample_tickets_response):
        """Test get_tickets in legacy mode."""
        zendesk_client._make_request = AsyncMock(return_value=sample_tickets_response)

        result = await zendesk_client.get_tickets(
            status="open",
            page_size=50,
            use_pagination=False
        )

        assert len(result) == 2
        assert all(isinstance(ticket, ZendeskTicket) for ticket in result)
        zendesk_client._make_request.assert_called_once_with(
            "GET",
            "tickets.json",
            params={"status": "open", "per_page": 50}
        )

    @pytest.mark.asyncio
    async def test_get_tickets_paginated(self, zendesk_client):
        """Test get_tickets_paginated returns proper paginator."""
        result = zendesk_client.get_tickets_paginated(
            status="open",
            page_size=50
        )

        assert isinstance(result, ZendeskPaginator)
        assert result.client is zendesk_client
        assert result.endpoint == "tickets.json"
        assert result.params == {
            "status": "open",
            "page[size]": 50
        }

    @pytest.mark.asyncio
    async def test_get_tickets_page(self, zendesk_client, sample_paginated_response):
        """Test get_tickets_page method."""
        zendesk_client._make_request = AsyncMock(return_value=sample_paginated_response)

        result = await zendesk_client.get_tickets_page(
            status="open",
            page_size=50,
            after_cursor="test_cursor"
        )

        assert isinstance(result, PaginatedTicketsResponse)
        assert len(result.tickets) == 1
        assert result.meta.has_more is True

        zendesk_client._make_request.assert_called_once_with(
            "GET",
            "tickets.json",
            params={
                "status": "open",
                "page[size]": 50,
                "page[after]": "test_cursor"
            }
        )

    @pytest.mark.asyncio
    async def test_get_all_tickets(
        self,
        zendesk_client,
        sample_paginated_response,
        sample_paginated_response_last_page
    ):
        """Test get_all_tickets method."""
        zendesk_client._make_request = AsyncMock(side_effect=[
            sample_paginated_response,
            sample_paginated_response_last_page
        ])

        result = await zendesk_client.get_all_tickets(status="open")

        assert len(result) == 2
        assert all(isinstance(ticket, ZendeskTicket) for ticket in result)
        assert zendesk_client._make_request.call_count == 2

    @pytest.mark.asyncio
    async def test_get_zendesk_client_factory(self, mock_config):
        """Test factory function creates and connects client."""
        with patch('src.integrations.zendesk.client.ZendeskClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await get_zendesk_client()

            assert result is mock_client
            mock_client.connect.assert_called_once()


class TestZendeskPaginator:
    """Test ZendeskPaginator functionality."""

    @pytest.mark.asyncio
    async def test_paginator_initialization(self, zendesk_client):
        """Test paginator initialization."""
        endpoint = "tickets.json"
        params = {"status": "open"}

        paginator = ZendeskPaginator(zendesk_client, endpoint, params)

        assert paginator.client is zendesk_client
        assert paginator.endpoint == endpoint
        assert paginator.params == params
        assert paginator._current_cursor is None
        assert paginator._has_more is True

    @pytest.mark.asyncio
    async def test_paginator_initialization_no_params(self, zendesk_client):
        """Test paginator initialization without params."""
        endpoint = "tickets.json"

        paginator = ZendeskPaginator(zendesk_client, endpoint)

        assert paginator.params == {}

    @pytest.mark.asyncio
    async def test_paginator_anext_first_page(
        self,
        zendesk_client,
        sample_paginated_response
    ):
        """Test getting first page of results."""
        zendesk_client._make_request = AsyncMock(return_value=sample_paginated_response)

        paginator = ZendeskPaginator(
            zendesk_client,
            "tickets.json",
            {"status": "open"}
        )

        result = await paginator.__anext__()

        assert result == sample_paginated_response
        assert paginator._has_more is True
        assert paginator._current_cursor == "eyJvIjoibmljZV9pZCIsInYiOiJhUURBIn0="

        zendesk_client._make_request.assert_called_once_with(
            "GET",
            "tickets.json",
            params={
                "status": "open",
                "page[size]": 100
            }
        )

    @pytest.mark.asyncio
    async def test_paginator_anext_stop_iteration(self, zendesk_client):
        """Test StopAsyncIteration when no more pages."""
        zendesk_client._make_request = AsyncMock()
        paginator = ZendeskPaginator(zendesk_client, "tickets.json")
        paginator._has_more = False

        with pytest.raises(StopAsyncIteration):
            await paginator.__anext__()

        zendesk_client._make_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_paginator_async_iteration(
        self,
        zendesk_client,
        sample_paginated_response,
        sample_paginated_response_last_page
    ):
        """Test full async iteration through multiple pages."""
        zendesk_client._make_request = AsyncMock(side_effect=[
            sample_paginated_response,
            sample_paginated_response_last_page
        ])

        paginator = ZendeskPaginator(zendesk_client, "tickets.json")
        pages = []

        async for page in paginator:
            pages.append(page)

        assert len(pages) == 2
        assert pages[0] == sample_paginated_response
        assert pages[1] == sample_paginated_response_last_page
        assert zendesk_client._make_request.call_count == 2

    @pytest.mark.asyncio
    async def test_paginator_get_all(
        self,
        zendesk_client,
        sample_paginated_response,
        sample_paginated_response_last_page
    ):
        """Test get_all method."""
        zendesk_client._make_request = AsyncMock(side_effect=[
            sample_paginated_response,
            sample_paginated_response_last_page
        ])

        paginator = ZendeskPaginator(zendesk_client, "tickets.json")
        all_pages = await paginator.get_all()

        assert len(all_pages) == 2
        assert all_pages[0] == sample_paginated_response
        assert all_pages[1] == sample_paginated_response_last_page

    @pytest.mark.asyncio
    async def test_paginator_get_all_with_max_pages(
        self,
        zendesk_client,
        sample_paginated_response
    ):
        """Test get_all method with max_pages limit."""
        # Mock infinite pagination
        zendesk_client._make_request = AsyncMock(return_value=sample_paginated_response)

        paginator = ZendeskPaginator(zendesk_client, "tickets.json")
        all_pages = await paginator.get_all(max_pages=2)

        assert len(all_pages) == 2
        assert zendesk_client._make_request.call_count == 2


class TestSimplifiedModels:
    """Test simplified models."""

    def test_zendesk_ticket_creation(self, sample_ticket_data):
        """Test creating a ZendeskTicket."""
        ticket = ZendeskTicket(**sample_ticket_data)

        assert ticket.id == 123
        assert ticket.subject == "Test Ticket"
        assert ticket.status == "open"
        assert ticket.tags == ["test", "bug"]

    def test_paginated_tickets_response(self, sample_ticket_data):
        """Test PaginatedTicketsResponse model."""
        response_data = {
            "tickets": [sample_ticket_data],
            "meta": {
                "has_more": True,
                "after_cursor": "test_cursor"
            },
            "links": {
                "next": "https://example.zendesk.com/api/v2/tickets.json?page[after]=test_cursor"
            }
        }

        response = PaginatedTicketsResponse(**response_data)
        assert len(response.tickets) == 1
        assert isinstance(response.tickets[0], ZendeskTicket)
        assert response.meta.has_more is True
        assert response.links.next is not None