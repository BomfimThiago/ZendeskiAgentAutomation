"""
Test fixtures and configuration for Zendesk client tests.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, Any

from src.integrations.zendesk.client import ZendeskClient, ZendeskPaginator
from src.integrations.zendesk.config import ZendeskConfig
from src.integrations.zendesk.models import (
    ZendeskTicket,
    ZendeskResponse,
    PaginatedTicketsResponse,
    PaginationMeta,
    PaginationLinks
)


@pytest.fixture
def mock_config():
    """Mock Zendesk configuration."""
    config = MagicMock(spec=ZendeskConfig)
    config.EMAIL = "test@example.com"
    config.TOKEN = "test_token"
    config.api_url = "https://test.zendesk.com/api/v2"
    config.REQUEST_TIMEOUT = 30
    config.MAX_RETRIES = 3
    config.BACKOFF_FACTOR = 1.0
    config.DEFAULT_PAGE_SIZE = 100
    config.MAX_PAGE_SIZE = 100
    config.RATE_LIMIT_RETRY_AFTER = 60
    return config


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    mock_client = AsyncMock()
    mock_client.make_request = AsyncMock()
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    return mock_client


@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "id": 123,
        "subject": "Test Ticket",
        "description": "Test description",
        "status": "open",
        "priority": "normal",
        "type": "incident",
        "tags": ["test", "bug"],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "requester_id": 456,
        "assignee_id": 789,
        "organization_id": 111,
        "custom_fields": []
    }




@pytest.fixture
def sample_tickets_response(sample_ticket_data):
    """Sample API response with multiple tickets."""
    return {
        "tickets": [
            sample_ticket_data,
            {**sample_ticket_data, "id": 124, "subject": "Another Ticket"}
        ]
    }


@pytest.fixture
def sample_paginated_response(sample_ticket_data):
    """Sample paginated API response."""
    return {
        "tickets": [sample_ticket_data],
        "meta": {
            "has_more": True,
            "after_cursor": "eyJvIjoibmljZV9pZCIsInYiOiJhUURBIn0="
        },
        "links": {
            "next": "https://test.zendesk.com/api/v2/tickets.json?page[size]=100&page[after]=eyJvIjoibmljZV9pZCIsInYiOiJhUURBIn0="
        }
    }


@pytest.fixture
def sample_paginated_response_last_page(sample_ticket_data):
    """Sample paginated API response for last page."""
    return {
        "tickets": [sample_ticket_data],
        "meta": {
            "has_more": False,
            "after_cursor": None
        },
        "links": {}
    }


@pytest_asyncio.fixture
async def zendesk_client(mock_config, mock_http_client):
    """Configured Zendesk client with mocked dependencies."""
    client = ZendeskClient()
    client.config = mock_config
    client._http_client = mock_http_client
    return client


@pytest.fixture
def mock_ticket(sample_ticket_data):
    """Mock ZendeskTicket instance."""
    return ZendeskTicket(**sample_ticket_data)




@pytest.fixture
def error_response():
    """Sample error response from Zendesk API."""
    return {
        "error": "RecordNotFound",
        "description": "Not found",
        "details": {"record_id": 999}
    }